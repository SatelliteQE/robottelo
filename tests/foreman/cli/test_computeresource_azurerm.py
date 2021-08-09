"""Test class for AzureRM Compute Resource

:Requirement: ComputeResources AzureRM

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ComputeResources-Azure

:Assignee: jyejare

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import set_hammer_api_timeout
from robottelo.api.utils import skip_yum_update_during_provisioning
from robottelo.cli.computeprofile import ComputeProfile
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.host import Host
from robottelo.config import settings
from robottelo.constants import AZURERM_FILE_URI
from robottelo.constants import AZURERM_PLATFORM_DEFAULT
from robottelo.constants import AZURERM_PREMIUM_OS_Disk
from robottelo.constants import AZURERM_RHEL7_FT_BYOS_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_CUSTOM_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_GALLERY_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_IMG_URN
from robottelo.constants import AZURERM_RHEL7_UD_IMG_URN
from robottelo.constants import AZURERM_VM_SIZE_DEFAULT


@pytest.fixture(scope='class')
def azurerm_hostgroup(
    default_architecture,
    module_azurerm_cr,
    module_domain,
    module_location,
    module_puppet_environment,
    default_smart_proxy,
    default_os,
    module_org,
):
    """Sets Hostgroup for AzureRm Host Provisioning"""

    hgroup = entities.HostGroup(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        domain=module_domain,
        location=[module_location],
        environment=module_puppet_environment,
        puppet_proxy=default_smart_proxy,
        puppet_ca_proxy=default_smart_proxy,
        root_pass=gen_string('alphanumeric'),
        operatingsystem=default_os,
        organization=[module_org],
    ).create()
    return hgroup


class TestAzureRMComputeResourceTestCase:
    """AzureRm compute resource Tests"""

    @pytest.mark.upgrade
    @pytest.mark.tier1
    def test_positive_crud_azurerm_cr(self, module_org, module_location, azurerm_settings):
        """Create, Read, Update and Delete AzureRm compute resources

        :id: 776243ac-1666-4d9b-b99c-f0cadb19b06e

        :expectedresults: Compute resource should be created, read, updated and deleted

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        # Create CR
        cr_name = gen_string('alpha')
        compresource = ComputeResource.create(
            {
                'name': cr_name,
                'provider': 'AzureRm',
                'app-ident': azurerm_settings['app_ident'],
                'secret-key': azurerm_settings['secret'],
                'tenant': azurerm_settings['tenant'],
                'sub-id': azurerm_settings['sub_id'],
                'region': azurerm_settings['region'],
                'organization-id': module_org.id,
                'location-id': module_location.id,
            }
        )
        assert compresource['name'] == cr_name
        assert compresource['provider'] == 'Azure Resource Manager'
        assert compresource['tenant'] == azurerm_settings['tenant']
        assert compresource['app_ident'] == azurerm_settings['app_ident']
        assert compresource['sub_id'] == azurerm_settings['sub_id']
        assert compresource['region'] == azurerm_settings['region']
        assert module_org.name in compresource['organizations']
        assert module_location.name in compresource['locations']

        # List CR
        list_cr = ComputeResource.list()
        assert len([cr for cr in list_cr if cr['name'] == cr_name]) == 1

        # Update CR
        new_cr_name = gen_string('alpha')
        description = gen_string('utf8')
        ComputeResource.update({'name': cr_name, 'new-name': new_cr_name})
        ComputeResource.update({'name': new_cr_name, 'description': description})
        # check updated values
        result = ComputeResource.info({'id': compresource['id']})
        assert result['name'] == new_cr_name
        assert result['description'] == description

        # Delete CR
        ComputeResource.delete({'name': result['name']})
        assert not ComputeResource.exists(search=('name', result['name']))

    @pytest.mark.upgrade
    @pytest.mark.tier2
    @pytest.mark.parametrize(
        "image",
        [
            AZURERM_RHEL7_FT_IMG_URN,
            AZURERM_RHEL7_UD_IMG_URN,
            AZURERM_RHEL7_FT_BYOS_IMG_URN,
            AZURERM_RHEL7_FT_CUSTOM_IMG_URN,
            AZURERM_RHEL7_FT_GALLERY_IMG_URN,
        ],
    )
    def test_positive_image_crud(self, default_architecture, module_azurerm_cr, default_os, image):
        """Finish template/Cloud_init image along with username is being Create, Read, Update and
        Delete in AzureRm compute resources

        :id: e4f40640-46dd-4ef8-8be5-99c625056aff

        :parametrized: yes

        :steps:
            1. Create an AzureRm Compute Resource.
            2. Create a finish template/Cloud_init based image in it.
            3. List/info the created image
            4. Update image name and username
            5. Delete created image

        :expectedresults: Finish template/Cloud_init image should be created, list, updated and
                          deleted in AzureRm CR along with username

        :CaseImportance: Critical

        :CaseLevel: Integration
        """

        # Create
        img_name = gen_string('alpha')
        username = gen_string('alpha')
        img_ft = ComputeResource.image_create(
            {
                'name': img_name,
                'operatingsystem-id': default_os.id,
                'architecture-id': default_architecture.id,
                'uuid': image,
                'compute-resource': module_azurerm_cr.name,
                'username': username,
                'user-data': 'no',
            }
        )[0]
        assert img_ft['message'] == 'Image created.'
        assert img_ft['name'] == img_name

        # Info Image
        img_info = ComputeResource.image_info(
            {'name': img_name, 'compute-resource': module_azurerm_cr.name}
        )[0]
        assert img_info['operating-system'] == default_os.title
        assert img_info['username'] == username
        assert img_info['uuid'] == image
        assert img_info['user-data'] == 'false'
        assert img_info['architecture'] == default_architecture.name

        # List image
        list_img = ComputeResource.image_list({'compute-resource': module_azurerm_cr.name})
        assert len(list_img) == 1
        assert list_img[0]['name'] == img_name

        # Update image
        new_img_name = gen_string('alpha')
        new_username = gen_string('alpha')
        result = ComputeResource.image_update(
            {
                'name': img_name,
                'compute-resource': module_azurerm_cr.name,
                'new-name': new_img_name,
                'username': new_username,
            }
        )[0]
        assert result['message'] == 'Image updated.'
        assert result['name'] == new_img_name

        img_info = ComputeResource.image_info(
            {'name': new_img_name, 'compute-resource': module_azurerm_cr.name}
        )[0]
        assert img_info['username'] == new_username

        # Delete Image
        result = ComputeResource.image_delete(
            {'name': new_img_name, 'compute-resource': module_azurerm_cr.name}
        )[0]
        assert result['message'] == 'Image deleted.'
        assert result['name'] == new_img_name

    @pytest.mark.skip_if_open("BZ:1850934")
    @pytest.mark.tier2
    def test_positive_check_available_networks(self, azurermclient, module_azurerm_cr):
        """Check networks from AzureRm CR are available to select during host provision.

        :id: 9e08463c-c700-47fc-8a58-e03aa8bcd097

        :expectedresults: All the networks from AzureRM CR should be available.

        :CaseLevel: Integration

        :BZ: 1850934
        """

        result = ComputeResource.networks({'id': module_azurerm_cr.id})
        assert len(result) > 0

    @pytest.mark.tier2
    def test_positive_create_compute_profile_values(self, azurermclient, module_azurerm_cr):
        """Compute-profile values are being Create using AzureRm compute resource.

        :id: 1fbe642e-f83d-46f1-95af-0f59af826781

        :steps:
            1. Create an AzureRm Compute Resource.
            2. Create Compute-profile value

        :expectedresults: Compute-profile values should be create with AzureRm CR

        :CaseLevel: Integration
        """
        username = gen_string('alpha')
        password = gen_string('alpha')
        cp_name = gen_string('alpha')
        script_command = 'touch /var/tmp/text.txt'
        nw_id = module_azurerm_cr.available_networks()['results'][-1]['id']

        profile = ComputeProfile.create({'name': cp_name})
        result = ComputeProfile.values_create(
            {
                'compute-profile-id': int(profile['id']),
                'compute-resource': module_azurerm_cr.name,
                'compute-attributes': f'resource_group={settings.azurerm.resource_group},'
                f'vm_size={AZURERM_VM_SIZE_DEFAULT},'
                f'username={username},'
                f'password={password},'
                f'platform={AZURERM_PLATFORM_DEFAULT},'
                f'script_command={script_command},'
                f'script_uris={AZURERM_FILE_URI},'
                f'premium_os_disk=1',
                'interface': f'compute_network={nw_id},'
                'compute_public_ip=Static,'
                'compute_private_ip=false',
            }
        )[0]

        assert result['message'] == 'Compute profile attributes are set.'

        # Info
        result_info = ComputeProfile.info({'name': cp_name})
        vm_attributes = result_info['compute-attributes'][0]['vm-attributes']
        assert module_azurerm_cr.name == result_info['compute-attributes'][0]['compute-resource']
        assert settings.azurerm.resource_group in vm_attributes
        assert AZURERM_VM_SIZE_DEFAULT in vm_attributes
        assert username in vm_attributes
        assert password in vm_attributes
        assert AZURERM_PLATFORM_DEFAULT in vm_attributes
        assert script_command in vm_attributes
        assert AZURERM_FILE_URI in vm_attributes


@pytest.mark.run_in_one_thread
class TestAzureRMFinishTemplateProvisioning:
    """AzureRM Host Provisioning Tests"""

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(self, request, module_domain, module_azurerm_cr, module_azurerm_finishimg):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """
        request.cls.region = settings.azurerm.azure_region
        request.cls.rhel7_ft_img = AZURERM_RHEL7_FT_IMG_URN
        request.cls.rg_default = settings.azurerm.resource_group
        request.cls.premium_os_disk = AZURERM_PREMIUM_OS_Disk
        request.cls.platform = AZURERM_PLATFORM_DEFAULT
        request.cls.vm_size = AZURERM_VM_SIZE_DEFAULT
        request.cls.hostname = f'test-{gen_string("alpha")}'
        request.cls.fullhostname = f'{self.hostname}.{module_domain.name}'.lower()
        script_command = 'touch /var/tmp/test.txt'

        request.cls.compute_attrs = (
            f'resource_group={self.rg_default},'
            f'vm_size={self.vm_size},'
            f'username={module_azurerm_finishimg.username},'
            f'ssh_key_data={settings.azurerm.ssh_pub_key},'
            f'platform={self.platform},'
            f'script_command={script_command},'
            f'script_uris={AZURERM_FILE_URI},'
            f'premium_os_disk={self.premium_os_disk}'
        )
        nw_id = module_azurerm_cr.available_networks()['results'][-1]['id']
        request.cls.interfaces_attributes = (
            f'compute_network={nw_id},compute_public_ip=Static,compute_private_ip=false'
        )

    @pytest.fixture(scope='class')
    def class_host_ft(
        self,
        azurermclient,
        module_azurerm_finishimg,
        module_azurerm_cr,
        default_architecture,
        module_domain,
        module_location,
        module_org,
        default_os,
        default_smart_proxy,
        module_puppet_environment,
    ):
        """
        Provisions the host on AzureRM using Finish template
        Later in tests this host will be used to perform assertions
        """
        set_hammer_api_timeout()
        skip_yum_update_during_provisioning(template='Kickstart default finish')
        host = Host.create(
            {
                'name': self.hostname,
                'compute-resource': module_azurerm_cr.name,
                'compute-attributes': self.compute_attrs,
                'interface': self.interfaces_attributes,
                'location-id': module_location.id,
                'organization-id': module_org.id,
                'domain-id': module_domain.id,
                'architecture-id': default_architecture.id,
                'operatingsystem-id': default_os.id,
                'root-password': gen_string('alpha'),
                'image': module_azurerm_finishimg.name,
            },
            timeout=1800,
        )
        yield host
        skip_yum_update_during_provisioning(template='Kickstart default finish', reverse=True)
        Host.delete({'name': self.fullhostname}, timeout=1800)
        set_hammer_api_timeout(reverse=True)

    @pytest.fixture(scope='class')
    def azureclient_host(self, azurermclient, class_host_ft):
        """Returns the AzureRM Client Host object to perform the assertions"""
        return azurermclient.get_vm(name=class_host_ft['name'].split('.')[0])

    @pytest.mark.skip_if_open("BZ:1850934")
    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_positive_azurerm_host_provisioned(
        self, class_host_ft, azureclient_host, module_azurerm_cr, module_azurerm_finishimg
    ):
        """Host can be provisioned on AzureRM

        :id: 9e8242e5-3ef3-4884-a200-7ba79b8ef49f

        :CaseLevel: Component

        ::CaseImportance: Critical

        :steps:
            1. Create a AzureRM Compute Resource and provision host.

        :expectedresults:
            1. The host should be provisioned on AzureRM
            2. The host name should be the same as given in data to provision the host
            3. The host should show Installed status for provisioned host
            4. The provisioned host should be assigned with external IP
            5. The host Compute Resource name same as previsioned
            6. The host image name same as previsioned
            7. The host Name and Platform should be same on Azure Cloud as provided during
               provisioned.

        :BZ: 1850934
        """

        assert class_host_ft['name'] == self.fullhostname
        assert class_host_ft['status']['build-status'] == "Installed"
        assert class_host_ft['compute-resource'] == module_azurerm_cr.name
        assert class_host_ft['operating-system']['image'] == module_azurerm_finishimg.name
        assert class_host_ft['network-interfaces'][0]['ipv4-address'] == azureclient_host.ip

        # Azure cloud
        assert self.hostname.lower() == azureclient_host.name
        assert self.vm_size == azureclient_host.type


@pytest.mark.run_in_one_thread
class TestAzureRMUserDataProvisioning:
    """AzureRM Host Provisioning Tests"""

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(self, request, module_domain, module_azurerm_cr, module_azurerm_cloudimg):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """
        request.cls.region = settings.azurerm.azure_region
        request.cls.rhel7_ft_img = AZURERM_RHEL7_UD_IMG_URN
        request.cls.rg_default = settings.azurerm.resource_group
        request.cls.premium_os_disk = AZURERM_PREMIUM_OS_Disk
        request.cls.platform = AZURERM_PLATFORM_DEFAULT
        request.cls.vm_size = AZURERM_VM_SIZE_DEFAULT
        request.cls.hostname = f'test-{gen_string("alpha")}'
        request.cls.fullhostname = f'{self.hostname}.{module_domain.name}'.lower()
        script_command = 'touch /var/tmp/test.txt'

        request.cls.compute_attrs = (
            f'resource_group={self.rg_default},'
            f'vm_size={self.vm_size},'
            f'username={module_azurerm_cloudimg.username},'
            f'password={settings.azurerm.password},'
            f'platform={self.platform},'
            f'script_command={script_command},'
            f'script_uris={AZURERM_FILE_URI},'
            f'premium_os_disk={self.premium_os_disk}'
        )
        nw_id = module_azurerm_cr.available_networks()['results'][-1]['id']
        request.cls.interfaces_attributes = (
            f'compute_network={nw_id},compute_public_ip=Dynamic,compute_private_ip=false'
        )

    @pytest.fixture(scope='class')
    def class_host_ud(
        self,
        azurermclient,
        module_azurerm_cloudimg,
        module_azurerm_cr,
        default_architecture,
        module_domain,
        module_location,
        module_org,
        default_os,
        default_smart_proxy,
        module_puppet_environment,
        azurerm_hostgroup,
    ):
        """
        Provisions the host on AzureRM using UserData template
        Later in tests this host will be used to perform assertions
        """
        set_hammer_api_timeout()
        skip_yum_update_during_provisioning(template='Kickstart default user data')
        host = Host.create(
            {
                'name': self.hostname,
                'compute-attributes': self.compute_attrs,
                'interface': self.interfaces_attributes,
                'image': module_azurerm_cloudimg.name,
                'hostgroup': azurerm_hostgroup.name,
                'location': module_location.name,
                'organization': module_org.name,
                'operatingsystem-id': default_os.id,
            },
            timeout=1800,
        )
        yield host
        skip_yum_update_during_provisioning(template='Kickstart default user data', reverse=True)
        Host.delete({'name': self.fullhostname}, timeout=1800)
        set_hammer_api_timeout(reverse=True)

    @pytest.fixture(scope='class')
    def azureclient_host(self, azurermclient, class_host_ud):
        """Returns the AzureRM Client Host object to perform the assertions"""
        return azurermclient.get_vm(name=class_host_ud['name'].split('.')[0])

    @pytest.mark.skip_if_open("BZ:1850934")
    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_positive_azurerm_host_provisioned(
        self,
        class_host_ud,
        azureclient_host,
        module_azurerm_cr,
        module_azurerm_cloudimg,
        azurerm_hostgroup,
    ):
        """Host can be provisioned on AzureRM

        :id: c99d2679-1742-4ef3-9288-2961d18a30e7

        :CaseLevel: Component

        ::CaseImportance: Critical

        :steps:
            1. Create a AzureRM Compute Resource and provision host.

        :expectedresults:
            1. The host with hostgroup should be provisioned on AzureRM
            2. The host name should be the same as given in data to provision the host
            3. The host should show "Pending installation" status for provisioned host(
               as Satellite and VM are in diff networks hence status shows as "Pending
               installation")
            4. The provisioned host should be assigned with external IP
            5. The host Name and Platform should be same on Azure Cloud as provided during
               provisioned.

        :BZ: 1850934
        """
        assert class_host_ud['name'] == self.fullhostname
        assert class_host_ud['status']['build-status'] == "Pending installation"
        assert class_host_ud['network-interfaces'][0]['ipv4-address'] == azureclient_host.ip
        assert class_host_ud['compute-resource'] == module_azurerm_cr.name
        assert class_host_ud['operating-system']['image'] == module_azurerm_cloudimg.name
        assert class_host_ud['host-group'] == azurerm_hostgroup.name

        # Azure cloud
        assert self.hostname.lower() == azureclient_host.name
        assert self.vm_size == azureclient_host.type


@pytest.mark.run_in_one_thread
class TestAzureRMBYOSFinishTemplateProvisioning:
    """AzureRM Host Provisioning Test with BYOS Image"""

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(self, request, module_domain, module_azurerm_cr, module_azurerm_byos_finishimg):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """
        request.cls.region = settings.azurerm.azure_region
        request.cls.hostname = f'test-{gen_string("alpha")}'
        request.cls.fullhostname = f'{self.hostname}.{module_domain.name}'.lower()
        script_command = 'touch /var/tmp/test.txt'

        request.cls.compute_attrs = (
            f'resource_group={settings.azurerm.resource_group},vm_size={AZURERM_VM_SIZE_DEFAULT}, '
            f'username={module_azurerm_byos_finishimg.username}, '
            f'ssh_key_data={settings.azurerm.ssh_pub_key}, platform={AZURERM_PLATFORM_DEFAULT},'
            f'script_command={script_command}, script_uris={AZURERM_FILE_URI},'
            f'premium_os_disk={AZURERM_PREMIUM_OS_Disk}'
        )
        nw_id = module_azurerm_cr.available_networks()['results'][-1]['id']
        request.cls.interfaces_attributes = (
            f'compute_network={nw_id},compute_public_ip=Static, compute_private_ip=false'
        )

    @pytest.fixture(scope='class')
    def class_byos_ft_host(
        self,
        azurermclient,
        module_azurerm_byos_finishimg,
        module_azurerm_cr,
        default_architecture,
        module_domain,
        module_location,
        module_org,
        default_os,
        default_smart_proxy,
        module_puppet_environment,
    ):
        """
        Provisions the host on AzureRM with BYOS Image
        Later in tests this host will be used to perform assertions
        """
        set_hammer_api_timeout()
        skip_yum_update_during_provisioning(template='Kickstart default finish')
        host = Host.create(
            {
                'name': self.hostname,
                'compute-resource': module_azurerm_cr.name,
                'compute-attributes': self.compute_attrs,
                'interface': self.interfaces_attributes,
                'location-id': module_location.id,
                'organization-id': module_org.id,
                'domain-id': module_domain.id,
                'architecture-id': default_architecture.id,
                'operatingsystem-id': default_os.id,
                'root-password': gen_string('alpha'),
                'image': module_azurerm_byos_finishimg.name,
                'volume': "disk_size_gb=5",
            },
            timeout=1800,
        )
        yield host
        skip_yum_update_during_provisioning(template='Kickstart default finish', reverse=True)
        Host.delete({'name': self.fullhostname}, timeout=1800)
        set_hammer_api_timeout(reverse=True)

    @pytest.fixture(scope='class')
    def azureclient_host(self, azurermclient, class_byos_ft_host):
        """Returns the AzureRM Client Host object to perform the assertions"""
        return azurermclient.get_vm(name=class_byos_ft_host['name'].split('.')[0])

    @pytest.mark.skip_if_open("BZ:1850934")
    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_positive_azurerm_byosft_host_provisioned(
        self,
        class_byos_ft_host,
        azureclient_host,
        module_azurerm_cr,
        module_azurerm_byos_finishimg,
    ):
        """Host can be provisioned on AzureRM using BYOS Image

        :id: 5ebfc3ed-0e61-4cb1-9d5e-831d81bb3bcc

        :CaseLevel: System

        ::CaseImportance: Critical

        :steps:
            1. Create a AzureRM Compute Resource with BYOS Image and provision host.

        :expectedresults:
            1. The host should be provisioned on AzureRM using BYOS Image
            2. The host name should be the same as given in data to provision the host
            3. The host should show Installed status for provisioned host
            4. The provisioned host should be assigned with external IP
            5. The host Compute Resource name same as provisioned
            6. The host image name same as provisioned
            7. The host Name and Platform should be same on Azure Cloud as provided during
               provisioning.

        :BZ: 1850934
        """

        assert class_byos_ft_host['name'] == self.fullhostname
        assert class_byos_ft_host['status']['build-status'] == "Installed"
        assert class_byos_ft_host['compute-resource'] == module_azurerm_cr.name
        assert class_byos_ft_host['operating-system']['image'] == module_azurerm_byos_finishimg.name
        assert class_byos_ft_host['network-interfaces'][0]['ipv4-address'] == azureclient_host.ip

        # Azure cloud
        assert self.hostname.lower() == azureclient_host.name
        assert AZURERM_VM_SIZE_DEFAULT == azureclient_host.type
