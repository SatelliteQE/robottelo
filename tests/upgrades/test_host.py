"""Test Host/Provisioning related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: pdragun

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random
from collections import namedtuple

import pytest
from airgun.session import Session
from fauxfactory import gen_string
from nailgun import entities
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import LATEST_RHEL7_GCE_IMG_UUID
from robottelo.constants import VALID_GCE_ZONES


class TestScenarioPositiveGCEHostComputeResource:
    """The host can be provisioned on GCE CR created in previous version

    :steps:

        1. In Preupgrade Satellite, create GCE Compute Resource
        2. Upgrade the satellite to next/latest version
        3. Postupgrade, The Compute Resource attributes can be manipulated
        4. The host can be provisioned on GCE CR created in previous satellite version

    :expectedresults:

        1. The host should be provisioned on GCE CR created in previous version
        2. The GCE CR attributes should be manipulated
    """

    @pytest.fixture(scope='class')
    def arch_os_domain(self, class_target_sat):
        arch = class_target_sat.api.Architecture().search(query={'search': 'name=x86_64'})[0]
        os = class_target_sat.api.OperatingSystem().search(
            query={'search': 'family=Redhat and major=7'}
        )[0]

        domain_name = class_target_sat.hostname.split('.', 1)[1]
        return namedtuple('ArchOsDomain', ['arch', 'os', 'domain'])(arch, os, domain_name)

    @pytest.fixture(scope='class')
    def delete_host(self):
        if self.fullhost:
            host = entities.Host().search(query={'search': f'name={self.fullhost}'})
            if host:
                entities.Host(id=host[0].id).delete()

    @pytest.mark.pre_upgrade
    def test_pre_create_gce_cr_and_host(
        self, arch_os_domain, function_org, gce_cert, save_test_data
    ):
        """Create GCE Compute Resource

        :id: preupgrade-ef82143d-efef-49b2-9702-93d67ef6804c

        :steps: In Preupgrade Satellite, create GCE Compute Resource

        :expectedresults: The GCE CR created successfully
        """
        arch, os, domain_name = arch_os_domain
        cr_name = gen_string('alpha')
        loc = entities.Location().create()
        with Session('gce_upgrade_tests') as session:
            # Compute Resource Create and Assertions
            session.computeresource.create(
                {
                    'name': cr_name,
                    'provider': FOREMAN_PROVIDERS['google'],
                    'provider_content.google_project_id': gce_cert['project_id'],
                    'provider_content.client_email': gce_cert['client_email'],
                    'provider_content.certificate_path': settings.gce.cert_path,
                    'provider_content.zone.value': settings.gce.zone,
                    'organizations.resources.assigned': [function_org.name],
                    'locations.resources.assigned': [loc.name],
                }
            )
        gce_cr = entities.AbstractComputeResource().search(query={'search': f'name={cr_name}'})[0]
        gce_img = entities.Image(
            architecture=arch,
            compute_resource=gce_cr,
            name='autoupgrade_gce_img',
            operatingsystem=os,
            username='gceautou',
            uuid=LATEST_RHEL7_GCE_IMG_UUID,
        ).create()
        save_test_data(
            {
                'org': function_org.name,
                'loc': loc.name,
                'cr_name': cr_name,
            }
        )
        assert gce_cr.name == cr_name
        assert gce_img.name == 'autoupgrade_gce_img'

    @pytest.mark.post_upgrade(depend_on=test_pre_create_gce_cr_and_host)
    def test_post_create_gce_cr_and_host(
        self, target_sat, arch_os_domain, delete_host, pre_upgrade_data
    ):
        """Host provisioned using preupgrade GCE CR

        :id: postupgrade-ef82143d-efef-49b2-9702-93d67ef6804c

        :steps:

            1. Postupgrade, The Compute Resource attributes can be manipulated
            2. The host can be provisioned on GCE CR created in previous satellite version

        :expectedresults:

            1. The host should be provisioned on GCE CR created in previous version
            2. The GCE CR attributes should be manipulated
        """
        arch, os, domain_name = arch_os_domain
        hostname = gen_string('alpha')
        self.__class__.fullhost = f'{hostname}.{domain_name}'.lower()
        gce_cr = entities.GCEComputeResource().search(
            query={'search': f'name={pre_upgrade_data["cr_name"]}'}
        )[0]
        org = entities.Organization().search(query={'search': f'name={pre_upgrade_data["org"]}'})[0]
        loc = entities.Location().search(query={'search': f'name={pre_upgrade_data["loc"]}'})[0]
        compute_attrs = {
            'machine_type': 'g1-small',
            'network': 'default',
            'associate_external_ip': True,
            'volumes_attributes': {'0': {'size_gb': '10'}},
            'image_id': LATEST_RHEL7_GCE_IMG_UUID,
        }
        # Host Provisioning Tests
        with target_sat.skip_yum_update_during_provisioning(template='Kickstart default finish'):
            gce_hst = entities.Host(
                name=hostname,
                organization=org,
                location=loc,
                root_pass=gen_string('alphanumeric'),
                architecture=arch,
                compute_resource=gce_cr,
                domain=entities.Domain().search(query={'search': f'name={domain_name}'})[0],
                compute_attributes=compute_attrs,
                operatingsystem=os,
                provision_method='image',
            ).create()
        wait_for(
            lambda: entities.Host()
            .search(query={'search': f'name={self.fullhost}'})[0]
            .build_status_label
            == 'Installed',
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        assert gce_hst.name == self.fullhost
        gce_hst = entities.Host(id=gce_hst.id).read()
        assert gce_hst.build_status_label == 'Installed'
        # CR Manipulation Tests
        newgce_name = gen_string('alpha')
        newgce_zone = random.choice(VALID_GCE_ZONES)
        gce_cr.name = newgce_name
        gce_cr.zone = newgce_zone
        gce_cr.update(['name', 'zone'])
        gce_cr = entities.GCEComputeResource(id=gce_cr.id).read()
        assert gce_cr.name == newgce_name
        assert gce_cr.zone == newgce_zone
