"""Test Host/Provisioning related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

from airgun.session import Session
from fauxfactory import gen_string
from nailgun import entities
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade
from upgrade_tests.helpers.scenarios import create_dict
from upgrade_tests.helpers.scenarios import get_entity_data
from wait_for import wait_for

from robottelo.api.utils import skip_yum_update_during_provisioning
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import LATEST_RHEL7_GCE_IMG_UUID
from robottelo.constants import VALID_GCE_ZONES
from robottelo.helpers import download_gce_cert
from robottelo.test import APITestCase
from robottelo.test import settings

GCE_SETTINGS = dict(
    project_id=settings.gce.project_id,
    client_email=settings.gce.client_email,
    cert_path=settings.gce.cert_path,
    zone=settings.gce.zone,
    cert_url=settings.gce.cert_url,
)


class scenario_positive_gce_host_compute_resource(APITestCase):
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

    @classmethod
    def setUpClass(cls):
        cls.fullhost = None
        cls.arch = entities.Architecture().search(query={'search': 'name=x86_64'})[0]
        cls.os = entities.OperatingSystem().search(query={'search': 'family=Redhat and major=7'})[
            0
        ]
        download_gce_cert()
        cls.domain_name = settings.server.hostname.split('.', 1)[1]

    @classmethod
    def tearDownClass(cls):
        if cls.fullhost:
            hst = entities.Host().search(query={'search': f'name={cls.fullhost}'})
            if hst:
                entities.Host(id=hst[0].id).delete()

    @pre_upgrade
    def test_pre_create_gce_cr_and_host(self):
        """"""
        cr_name = gen_string('alpha')
        org = entities.Organization().create()
        loc = entities.Location().create()
        with Session('gce_upgrade_tests') as session:
            # Compute Resource Create and Assertions
            session.computeresource.create(
                {
                    'name': cr_name,
                    'provider': FOREMAN_PROVIDERS['google'],
                    'provider_content.google_project_id': GCE_SETTINGS['project_id'],
                    'provider_content.client_email': GCE_SETTINGS['client_email'],
                    'provider_content.certificate_path': GCE_SETTINGS['cert_path'],
                    'provider_content.zone.value': GCE_SETTINGS['zone'],
                    'organizations.resources.assigned': [org.name],
                    'locations.resources.assigned': [loc.name],
                }
            )
        gce_cr = entities.AbstractComputeResource().search(query={'search': f'name={cr_name}'})[0]
        gce_img = entities.Image(
            architecture=self.arch,
            compute_resource=gce_cr,
            name='autoupgrade_gce_img',
            operatingsystem=self.os,
            username='gceautou',
            uuid=LATEST_RHEL7_GCE_IMG_UUID,
        ).create()
        create_dict(
            {self.__class__.__name__: {'org': org.name, 'loc': loc.name, 'cr_name': cr_name}}
        )
        assert gce_cr.name == cr_name
        assert gce_img.name == 'autoupgrade_gce_img'

    @post_upgrade(depend_on=test_pre_create_gce_cr_and_host)
    def test_post_create_gce_cr_and_host(self):
        """"""
        hostname = gen_string('alpha')
        self.__class__.fullhost = f'{hostname}.{self.domain_name}'.lower()
        preentities = get_entity_data(self.__class__.__name__)
        gce_cr = entities.GCEComputeResource().search(
            query={'search': f"name={preentities['cr_name']}"}
        )[0]
        org = entities.Organization().search(query={'search': f"name={preentities['org']}"})[0]
        loc = entities.Location().search(query={'search': f"name={preentities['loc']}"})[0]
        compute_attrs = {
            'machine_type': 'g1-small',
            'network': 'default',
            'associate_external_ip': True,
            'volumes_attributes': {'0': {'size_gb': '10'}},
            'image_id': LATEST_RHEL7_GCE_IMG_UUID,
        }
        # Host Provisioning Tests
        try:
            skip_yum_update_during_provisioning(template='Kickstart default finish')
            gce_hst = entities.Host(
                name=hostname,
                organization=org,
                location=loc,
                root_pass=gen_string('alphanumeric'),
                architecture=self.arch,
                compute_resource=gce_cr,
                domain=entities.Domain().search(query={'search': f'name={self.domain_name}'})[0],
                compute_attributes=compute_attrs,
                operatingsystem=self.os,
                provision_method='image',
            ).create()
        finally:
            skip_yum_update_during_provisioning(template='Kickstart default finish', reverse=True)
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
