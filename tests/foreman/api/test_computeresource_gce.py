"""Tests for the GCE ``compute_resource`` paths.

A full API reference for compute resources can be found here:
http://www.katello.org/docs/api/apidoc/compute_resources.html

:Requirement: Computeresource GCE

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-GCE

:Team: Rocket

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.constants import VALID_GCE_ZONES

RHEL_CLOUD_PROJECTS = ['rhel-cloud', 'rhel-sap-cloud']


@pytest.mark.skip_if_not_set('gce')
class TestGCEComputeResourceTestCases:
    """Tests for ``api/v2/compute_resources``."""

    @pytest.mark.tier1
    @pytest.mark.parametrize('sat_gce', ['sat', 'puppet_sat'], indirect=True)
    def test_positive_crud_gce_cr(self, sat_gce, sat_gce_org, sat_gce_loc, gce_cert):
        """Create, Read, Update and Delete GCE compute resources

        :id: b324f8cd-d509-4d7a-b738-08aefafdc2b5

        :expectedresults: GCE Compute resource should be created, read, updated and deleted

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        cr_name = gen_string('alpha')
        # Testing Create
        compresource = sat_gce.api.GCEComputeResource(
            name=cr_name,
            provider='GCE',
            key_path=settings.gce.cert_path,
            zone=settings.gce.zone,
            organization=[sat_gce_org],
            location=[sat_gce_loc],
        ).create()
        assert compresource.name == cr_name
        # Testing Update
        new_name = gen_string('alpha')
        description = gen_string('utf8')
        new_zone = random.choice(VALID_GCE_ZONES)
        compresource.name = new_name
        compresource.description = description
        compresource.zone = new_zone
        compresource.update(['name', 'description', 'zone'])
        # Testing Read
        updated = sat_gce.api.GCEComputeResource(id=compresource.id).read()
        assert updated.name == new_name
        assert updated.description == description
        assert updated.zone == new_zone
        # Testing Delete
        updated.delete()
        assert not sat_gce.api.GCEComputeResource().search(query={'search': f'name={new_name}'})

    @pytest.mark.tier3
    def test_positive_check_available_images(self, module_gce_compute, googleclient):
        """Verify RHEL images from GCP are available to select in GCE CR

        :id: 5cdfab18-a591-4442-8c19-a01e9b10ac36

        :BZ: 2164989

        :expectedresults: RHEL images from GCP are available to select in GCE CR

        :CaseLevel: Integration
        """
        satgce_images = module_gce_compute.available_images()
        googleclient_images = googleclient.list_templates(
            include_public=True, public_projects=RHEL_CLOUD_PROJECTS
        )
        googleclient_image_names = [img.name for img in googleclient_images]
        # Validating GCE_CR images in Google CR
        sat_available_images = [satgce_images[i]['name'] for i in range(len(satgce_images))]
        for image in sat_available_images:
            assert image in googleclient_image_names
            # Validate only rhel-images exist in GCE_CR
            assert image.startswith('rhel-')

    @pytest.mark.tier3
    def test_positive_check_available_networks(self, module_gce_compute, googleclient):
        """Verify all the networks from GCE are available to select

        :id: 259c9f5f-19dd-4e06-af5e-874612914f44

        :expectedresults: All the networks from Google CR should be available to select in GCE CR

        :CaseLevel: Integration
        """
        gceavailable_networks = module_gce_compute.available_networks()
        satgce_networks = [net['name'] for net in gceavailable_networks['results']]
        gcloudclient_networks = googleclient.list_network()
        assert sorted(satgce_networks) == sorted(gcloudclient_networks)

    @pytest.mark.tier3
    def test_positive_check_available_flavors(self, module_gce_compute):
        """Verify flavors from GCE are available to select

        :id: f1da6706-9c27-4730-98e2-f710b847ff97

        :BZ: 1794744

        :expectedresults: All the flavors from Google CR should be available to select in GCE Host

        :CaseLevel: Integration
        """
        satgce_flavors = int(module_gce_compute.available_flavors()['total'])
        assert satgce_flavors > 1

    @pytest.mark.tier3
    def test_positive_create_finish_template_image(
        self, module_gce_finishimg, module_gce_compute, gce_latest_rhel_uuid
    ):
        """Finish template image along with username is being added in GCE CR

        :id: ec7ac618-ed1d-4b36-af7b-995cf4f78341

        :BZ: 1794744

        :steps:
            1. Create a GCE Compute Resource.
            2. Add a finish template based image in GCE CR.

        :expectedresults: Finish template image should be added in GCE CR along with username

        :CaseLevel: Integration
        """
        assert module_gce_finishimg.compute_resource.id == module_gce_compute.id
        assert module_gce_finishimg.uuid == gce_latest_rhel_uuid

    @pytest.mark.tier3
    def test_positive_create_cloud_init_image(
        self, module_gce_cloudimg, module_gce_compute, gce_custom_cloudinit_uuid
    ):
        """Cloud Init template image along with username is being added in GCE CR

        :id: 5a30c227-324a-49f9-932f-ce80da8611d0

        :steps:
            1. Create a GCE Compute Resource.
            2. Add a cloud init template in GCE CR.

        :expectedresults: Cloud init image should be added in GCE CR along with username

        :CaseLevel: Integration
        """
        assert module_gce_cloudimg.compute_resource.id == module_gce_compute.id
        assert module_gce_cloudimg.uuid == gce_custom_cloudinit_uuid


@pytest.mark.skip_if_not_set('gce')
class TestGCEHostProvisioningTestCase:
    """GCE Host Provisioning Tests

    :Requirement: Host
    """

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(self, request, gce_latest_rhel_uuid, sat_gce_domain):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """
        request.cls.mtype = 'g1-small'
        request.cls.network = 'default'
        request.cls.volsize = '20'
        request.cls.hostname = f'test{gen_string("alpha")}'

        request.cls.fullhostname = f'{self.hostname}.{sat_gce_domain.name}'.lower()

        request.cls.compute_attrs = {
            'image_id': gce_latest_rhel_uuid,
            'machine_type': self.mtype,
            'network': self.network,
            'associate_external_ip': True,
            'volumes_attributes': {'0': {'size_gb': self.volsize}},
        }

    @pytest.fixture(scope='class')
    def class_host(
        self,
        sat_gce,
        googleclient,
        sat_gce_default_architecture,
        sat_gce_domain,
        gce_hostgroup,
        sat_gce_org,
        sat_gce_default_os,
        sat_gce_loc,
        gce_latest_rhel_uuid,
        module_gce_finishimg,
    ):
        """Provisions the host on GCE

        Later in tests this host will be used to perform assertions
        """
        host = sat_gce.api.Host(
            architecture=sat_gce_default_architecture,
            compute_attributes=self.compute_attrs,
            domain=sat_gce_domain,
            hostgroup=gce_hostgroup,
            organization=sat_gce_org,
            operatingsystem=sat_gce_default_os,
            location=sat_gce_loc,
            name=self.hostname,
            provision_method='image',
            image=module_gce_finishimg,
            root_pass=gen_string('alphanumeric'),
        ).create()
        yield host
        host.delete()

    @pytest.fixture(scope='class')
    def google_host(self, googleclient):
        """Returns the Google Client Host object to perform the assertions"""
        return googleclient.get_vm(name='{}'.format(self.fullhostname.replace('.', '-')))

    @pytest.mark.e2e
    @pytest.mark.tier1
    @pytest.mark.parametrize('sat_gce', ['sat', 'puppet_sat'], indirect=True)
    def test_positive_gce_host_provisioned(self, class_host, google_host):
        """Host can be provisioned on Google Cloud

        :id: 889975f2-56ca-4584-95a7-21c513969630

        :CaseLevel: Component

        ::CaseImportance: Critical

        :steps:
            1. Create a GCE Compute Resource
            2. Create a Hostgroup with all the Global and Foreman entities but
                without Compute Profile, required to provision a host
            3. Provision a Host on Google Cloud using above GCE CR and Hostgroup

        :expectedresults:
            1. The host should be provisioned on Google Compute Engine
            2. The host name should be the same as given in data to provision the host
            3. The host should show Installed status for provisioned host
            4. The provisioned host should be assigned with external IP
        """
        assert class_host.name == self.fullhostname
        assert class_host.build_status_label == 'Installed'
        assert class_host.ip == google_host.ip

    @pytest.mark.tier3
    def test_positive_gce_host_power_on_off(self, class_host, google_host):
        """Host can be powered on and off

        :id: b622c6fc-c45e-431d-8de3-9d0237873998

        :CaseLevel: System

        :steps:
            1. Create a GCE Compute Resource
            2. Create a Hostgroup with all the Global and Foreman entities but
                without Compute Profile, required to provision a host
            3. Provision a Host on Google Cloud using above GCE CR and Hostgroup
            4. Power off the host from satellite
            5. Power on the host again from satellite

        :expectedresults:
            1. The provisioned host should be powered off and on requesting so
            2. The provisioned host should be powered on and on requesting so
        """
        class_host.power(data={'power_action': 'stop'})
        google_host.wait_for_state('VmState.STOPPED', '5m')
        assert google_host.is_stopped
        class_host.power(data={'power_action': 'start'})
        google_host.wait_for_state('VmState.RUNNING', '2m')
        assert google_host.is_running
