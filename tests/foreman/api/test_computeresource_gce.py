"""Tests for the GCE ``compute_resource`` paths.

A full API reference for compute resources can be found here:
http://www.katello.org/docs/api/apidoc/compute_resources.html

:Requirement: Computeresource GCE

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-GCE

:Assignee: addubey

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import VALID_GCE_ZONES

clouduser = gen_string('alpha')
finishuser = gen_string('alpha')


@pytest.fixture(scope='module')
def module_gce_cloudimg(
    default_architecture, module_gce_compute, default_os, gce_custom_cloudinit_uuid
):
    """Creates cloudinit image on GCE Compute Resource"""
    cloud_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_gce_compute,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=clouduser,
        uuid=gce_custom_cloudinit_uuid,
        user_data=True,
    ).create()
    return cloud_image


@pytest.fixture(scope='module')
def module_gce_finishimg(
    default_architecture, module_gce_compute, default_os, gce_latest_rhel_uuid
):
    """Creates finish image on GCE Compute Resource"""
    finish_image = entities.Image(
        architecture=default_architecture,
        compute_resource=module_gce_compute,
        name=gen_string('alpha'),
        operatingsystem=default_os,
        username=finishuser,
        uuid=gce_latest_rhel_uuid,
    ).create()
    return finish_image


@pytest.fixture(scope='module')
def module_gce_finishimg_puppet(
    session_puppet_enabled_sat,
    session_puppet_default_architecture,
    module_gce_compute_puppet,
    session_puppet_default_os,
    gce_latest_rhel_uuid,
):
    """Creates finish image on GCE Compute Resource"""
    finish_image = session_puppet_enabled_sat.api.Image(
        architecture=session_puppet_default_architecture,
        compute_resource=module_gce_compute_puppet,
        name=gen_string('alpha'),
        operatingsystem=session_puppet_default_os,
        username=finishuser,
        uuid=gce_latest_rhel_uuid,
    ).create()
    return finish_image


@pytest.fixture(scope='class')
def gce_domain(module_org, module_location, default_smart_proxy, default_sat):
    """Sets Domain for GCE Host Provisioning"""
    _, _, dom = default_sat.hostname.partition('.')
    domain = entities.Domain().search(query={'search': f'name="{dom}"'})
    domain = domain[0].read()
    domain.location.append(module_location)
    domain.organization.append(module_org)
    domain.dns = default_smart_proxy
    domain.update(['dns', 'location', 'organization'])
    return entities.Domain(id=domain.id).read()


@pytest.fixture(scope='class')
def gce_hostgroup(
    default_architecture,
    module_gce_compute,
    gce_domain,
    module_location,
    module_puppet_environment,
    default_smart_proxy,
    default_os,
    module_org,
    default_partitiontable,
    googleclient,
):
    """Sets Hostgroup for GCE Host Provisioning"""
    hgroup = entities.HostGroup(
        architecture=default_architecture,
        compute_resource=module_gce_compute,
        domain=gce_domain,
        location=[module_location],
        environment=module_puppet_environment,
        puppet_proxy=default_smart_proxy,
        puppet_ca_proxy=default_smart_proxy,
        root_pass=gen_string('alphanumeric'),
        operatingsystem=default_os,
        organization=[module_org],
        ptable=default_partitiontable,
    ).create()
    return hgroup


@pytest.fixture(scope='class')
def gce_hostgroup_puppet(
    session_puppet_enabled_sat,
    session_puppet_default_architecture,
    module_gce_compute_puppet,
    module_puppet_domain,
    module_puppet_loc,
    module_puppet_environment,
    session_puppet_enabled_proxy,
    session_puppet_default_os,
    module_puppet_org,
    session_puppet_default_partition_table,
    googleclient,
):
    """Sets Hostgroup for GCE Host Provisioning"""
    hgroup = session_puppet_enabled_sat.api.HostGroup(
        architecture=session_puppet_default_architecture,
        compute_resource=module_gce_compute_puppet,
        domain=module_puppet_domain,
        location=[module_puppet_loc],
        environment=module_puppet_environment,
        puppet_proxy=session_puppet_enabled_proxy,
        puppet_ca_proxy=session_puppet_enabled_proxy,
        root_pass=gen_string('alphanumeric'),
        operatingsystem=session_puppet_default_os,
        organization=[module_puppet_org],
        ptable=session_puppet_default_partition_table,
    ).create()
    return hgroup


@pytest.mark.skip_if_not_set('gce')
class TestGCEComputeResourceTestCases:
    """Tests for ``api/v2/compute_resources``."""

    @pytest.mark.tier1
    def test_positive_crud_gce_cr(self, module_org, module_location, gce_cert):
        """Create, Read, Update and Delete GCE compute resources

        :id: b324f8cd-d509-4d7a-b738-08aefafdc2b5

        :expectedresults: GCE Compute resource should be created, read, updated and deleted

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        cr_name = gen_string('alpha')
        # Testing Create
        compresource = entities.GCEComputeResource(
            name=cr_name,
            provider='GCE',
            email=gce_cert['client_email'],
            key_path=settings.gce.cert_path,
            project=gce_cert['project_id'],
            zone=settings.gce.zone,
            organization=[module_org],
            location=[module_location],
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
        updated = entities.GCEComputeResource(id=compresource.id).read()
        assert updated.name == new_name
        assert updated.description == description
        assert updated.zone == new_zone
        # Testing Delete
        updated.delete()
        assert not entities.GCEComputeResource().search(query={'search': f'name={new_name}'})

    @pytest.mark.tier3
    def test_positive_check_available_images(self, module_gce_compute, googleclient):
        """Verify all the images from GCE are available to select from

        :id: 5cdfab18-a591-4442-8c19-a01e9b10ac36

        :expectedresults: All the images from Google CR should be available to select in GCE CR

        :CaseLevel: Integration
        """
        satgce_images = module_gce_compute.available_images()
        gcloudclinet_images = googleclient.list_templates(True)
        assert len(satgce_images) == len(gcloudclinet_images)

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
        assert module_gce_finishimg.username == finishuser

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
        assert module_gce_cloudimg.username == clouduser


@pytest.mark.skip_if_not_set('gce')
class TestGCEHostProvisioningTestCase:
    """GCE Host Provisioning Tests

    :Requirement: Host
    """

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(self, request, gce_latest_rhel_uuid, module_puppet_domain):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """
        request.cls.mtype = 'g1-small'
        request.cls.network = 'default'
        request.cls.volsize = '20'
        request.cls.hostname = f'test{gen_string("alpha")}'

        request.cls.fullhostname = f'{self.hostname}.{module_puppet_domain.name}'.lower()

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
        session_puppet_enabled_sat,
        googleclient,
        session_puppet_default_architecture,
        module_puppet_domain,
        gce_hostgroup_puppet,
        module_puppet_org,
        session_puppet_default_os,
        module_puppet_loc,
        gce_latest_rhel_uuid,
        module_gce_finishimg_puppet,
    ):
        """Provisions the host on GCE

        Later in tests this host will be used to perform assertions
        """
        host = session_puppet_enabled_sat.api.Host(
            architecture=session_puppet_default_architecture,
            compute_attributes=self.compute_attrs,
            domain=module_puppet_domain,
            hostgroup=gce_hostgroup_puppet,
            organization=module_puppet_org,
            operatingsystem=session_puppet_default_os,
            location=module_puppet_loc,
            name=self.hostname,
            provision_method='image',
            image=module_gce_finishimg_puppet,
            root_pass=gen_string('alphanumeric'),
        ).create()
        yield host
        host.delete()

    @pytest.fixture(scope='class')
    def google_host(self, googleclient):
        """Returns the Google Client Host object to perform the assertions"""
        return googleclient.get_vm(name='{}'.format(self.fullhostname.replace('.', '-')))

    @pytest.mark.tier1
    def test_positive_gce_host_provisioned(self, class_host):
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
            2. The host name should should be the same as given in data to provision the host
            3. The host should show Installed status for provisioned host
        """
        assert class_host.name == self.fullhostname
        assert class_host.build_status_label == 'Installed'

    @pytest.mark.tier3
    def test_positive_gce_host_ip(self, class_host, google_host):
        """Host has assigned with external IP

        :id: e0ee4243-4b8e-474b-ad8c-46198506d196

        :CaseLevel: System

        ::CaseImportance: Critical

        :steps:
            1. Create a GCE Compute Resource
            2. Create a Hostgroup with all the Global and Foreman entities but
                without Compute Profile, required to provision a host
            3. Provision a Host on Google Cloud using above GCE CR and Hostgroup

        :expectedresults:
            1. The provisioned host should be assigned with external IP
        """
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
