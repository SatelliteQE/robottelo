"""Test class for AzureRM Compute Resource

:Requirement: ComputeResources AzureRM

:CaseAutomation: Automated

:CaseComponent: ComputeResources-Azure

:Team: Rocket

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import (
    AZURERM_FILE_URI,
    AZURERM_PLATFORM_DEFAULT,
    AZURERM_RHEL7_FT_CUSTOM_IMG_URN,
    AZURERM_RHEL7_UD_IMG_URN,
    AZURERM_VM_SIZE_DEFAULT,
    AZURERM_PREMIUM_OS_Disk,
)


@pytest.fixture(scope='class')
def azurerm_hostgroup(
    sat_azure,
    sat_azure_default_architecture,
    module_azurerm_cr,
    sat_azure_domain,
    sat_azure_loc,
    sat_azure_default_os,
    sat_azure_org,
):
    """Sets Hostgroup for AzureRm Host Provisioning"""

    return sat_azure.api.HostGroup(
        architecture=sat_azure_default_architecture,
        compute_resource=module_azurerm_cr,
        domain=sat_azure_domain,
        location=[sat_azure_loc],
        root_pass=gen_string('alphanumeric'),
        operatingsystem=sat_azure_default_os,
        organization=[sat_azure_org],
    ).create()


class TestAzureRMComputeResourceTestCase:
    """AzureRm compute resource Tests"""

    @pytest.mark.upgrade
    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'sat_azure', ['sat', 'puppet_sat'], indirect=True, ids=['satellite', 'puppet_enabled']
    )
    def test_positive_crud_azurerm_cr(
        self, azurerm_settings, sat_azure, sat_azure_loc, sat_azure_org
    ):
        """Create, Read, Update and Delete AzureRm compute resources

        :id: 776243ac-1666-4d9b-b99c-f0cadb19b06e

        :expectedresults: Compute resource should be created, read, updated and deleted

        :CaseImportance: Critical

        """
        # Create CR
        cr_name = gen_string('alpha')
        compresource = sat_azure.cli.ComputeResource.create(
            {
                'name': cr_name,
                'provider': 'AzureRm',
                'app-ident': azurerm_settings['app_ident'],
                'secret-key': azurerm_settings['secret'],
                'tenant': azurerm_settings['tenant'],
                'sub-id': azurerm_settings['sub_id'],
                'region': azurerm_settings['region'],
                'organization-id': sat_azure_org.id,
                'location-id': sat_azure_loc.id,
            }
        )
        assert compresource['name'] == cr_name
        assert compresource['provider'] == 'Azure Resource Manager'
        assert compresource['tenant'] == azurerm_settings['tenant']
        assert compresource['app_ident'] == azurerm_settings['app_ident']
        assert compresource['sub_id'] == azurerm_settings['sub_id']
        assert compresource['region'] == azurerm_settings['region']
        assert sat_azure_org.name in compresource['organizations']
        assert sat_azure_loc.name in compresource['locations']

        # List CR
        list_cr = sat_azure.cli.ComputeResource.list()
        assert len([cr for cr in list_cr if cr['name'] == cr_name]) == 1

        # Update CR
        new_cr_name = gen_string('alpha')
        description = gen_string('utf8')
        sat_azure.cli.ComputeResource.update({'name': cr_name, 'new-name': new_cr_name})
        sat_azure.cli.ComputeResource.update({'name': new_cr_name, 'description': description})
        # check updated values
        result = sat_azure.cli.ComputeResource.info({'id': compresource['id']})
        assert result['name'] == new_cr_name
        assert result['description'] == description

        # Delete CR
        sat_azure.cli.ComputeResource.delete({'name': result['name']})
        assert not sat_azure.cli.ComputeResource.exists(search=('name', result['name']))

    @pytest.mark.upgrade
    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'sat_azure', ['sat', 'puppet_sat'], indirect=True, ids=['satellite', 'puppet_enabled']
    )
    @pytest.mark.parametrize(
        "image",
        [
            AZURERM_RHEL7_UD_IMG_URN,
            AZURERM_RHEL7_FT_CUSTOM_IMG_URN,
        ],
    )
    def test_positive_image_crud(
        self,
        sat_azure,
        sat_azure_default_architecture,
        module_azurerm_cr,
        sat_azure_default_os,
        image,
    ):
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

        """

        # Create
        img_name = gen_string('alpha')
        username = gen_string('alpha')
        img_ft = sat_azure.cli.ComputeResource.image_create(
            {
                'name': img_name,
                'operatingsystem-id': sat_azure_default_os.id,
                'architecture-id': sat_azure_default_architecture.id,
                'uuid': image,
                'compute-resource': module_azurerm_cr.name,
                'username': username,
                'user-data': 'no',
            }
        )[0]
        assert img_ft['message'] == 'Image created.'
        assert img_ft['name'] == img_name

        # Info Image
        img_info = sat_azure.cli.ComputeResource.image_info(
            {'name': img_name, 'compute-resource': module_azurerm_cr.name}
        )[0]
        assert img_info['operating-system'] == sat_azure_default_os.title
        assert img_info['username'] == username
        assert img_info['uuid'] == image
        assert img_info['user-data'] == 'false'
        assert img_info['architecture'] == sat_azure_default_architecture.name

        # List image
        list_img = sat_azure.cli.ComputeResource.image_list(
            {'compute-resource': module_azurerm_cr.name}
        )
        assert len(list_img) == 1
        assert list_img[0]['name'] == img_name

        # Update image
        new_img_name = gen_string('alpha')
        new_username = gen_string('alpha')
        result = sat_azure.cli.ComputeResource.image_update(
            {
                'name': img_name,
                'compute-resource': module_azurerm_cr.name,
                'new-name': new_img_name,
                'username': new_username,
            }
        )[0]
        assert result['message'] == 'Image updated.'
        assert result['name'] == new_img_name

        img_info = sat_azure.cli.ComputeResource.image_info(
            {'name': new_img_name, 'compute-resource': module_azurerm_cr.name}
        )[0]
        assert img_info['username'] == new_username

        # Delete Image
        result = sat_azure.cli.ComputeResource.image_delete(
            {'name': new_img_name, 'compute-resource': module_azurerm_cr.name}
        )[0]
        assert result['message'] == 'Image deleted.'
        assert result['name'] == new_img_name

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'sat_azure', ['sat', 'puppet_sat'], indirect=True, ids=['satellite', 'puppet_enabled']
    )
    def test_positive_check_available_networks(self, sat_azure, azurermclient, module_azurerm_cr):
        """Check networks from AzureRm CR are available to select during host provision.

        :id: 9e08463c-c700-47fc-8a58-e03aa8bcd097

        :expectedresults: All the networks from AzureRM CR should be available.

        :BZ: 1850934
        """

        result = sat_azure.cli.ComputeResource.networks({'id': module_azurerm_cr.id})
        assert len(result) > 0

    @pytest.mark.tier2
    @pytest.mark.parametrize(
        'sat_azure', ['sat', 'puppet_sat'], indirect=True, ids=['satellite', 'puppet_enabled']
    )
    def test_positive_create_compute_profile_values(
        self, azurermclient, module_azurerm_cr, sat_azure
    ):
        """Compute-profile values are being Create using AzureRm compute resource.

        :id: 1fbe642e-f83d-46f1-95af-0f59af826781

        :steps:
            1. Create an AzureRm Compute Resource.
            2. Create Compute-profile value

        :expectedresults: Compute-profile values should be create with AzureRm CR

        """
        username = gen_string('alpha')
        password = gen_string('alpha')
        cp_name = gen_string('alpha')
        script_command = 'touch /var/tmp/text.txt'
        nw_id = module_azurerm_cr.available_networks()['results'][-1]['id']

        profile = sat_azure.cli.ComputeProfile.create({'name': cp_name})
        result = sat_azure.cli.ComputeProfile.values_create(
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
        result_info = sat_azure.cli.ComputeProfile.info({'name': cp_name})
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
    def class_setup(
        self,
        request,
        sat_azure_domain,
        module_azurerm_cr,
        module_azurerm_custom_finishimg,
    ):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """
        request.cls.region = settings.azurerm.azure_region
        request.cls.rhel7_ft_img = AZURERM_RHEL7_FT_CUSTOM_IMG_URN
        request.cls.rg_default = settings.azurerm.resource_group
        request.cls.premium_os_disk = AZURERM_PREMIUM_OS_Disk
        request.cls.platform = AZURERM_PLATFORM_DEFAULT
        request.cls.vm_size = AZURERM_VM_SIZE_DEFAULT
        request.cls.hostname = f'test-{gen_string("alpha")}'
        request.cls.fullhostname = f'{self.hostname}.{sat_azure_domain.name}'.lower()
        script_command = 'touch /var/tmp/test.txt'

        request.cls.compute_attrs = (
            f'resource_group={self.rg_default},'
            f'vm_size={self.vm_size},'
            f'username={module_azurerm_custom_finishimg.username},'
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
        sat_azure,
        module_azurerm_custom_finishimg,
        module_azurerm_cr,
        sat_azure_default_architecture,
        sat_azure_domain,
        sat_azure_loc,
        sat_azure_org,
        sat_azure_default_os,
    ):
        """
        Provisions the host on AzureRM using Finish template
        Later in tests this host will be used to perform assertions
        """
        with (
            sat_azure.hammer_api_timeout(),
            sat_azure.skip_yum_update_during_provisioning(template='Kickstart default finish'),
        ):
            host = sat_azure.cli.Host.create(
                {
                    'name': self.hostname,
                    'compute-resource': module_azurerm_cr.name,
                    'compute-attributes': self.compute_attrs,
                    'interface': self.interfaces_attributes,
                    'location-id': sat_azure_loc.id,
                    'organization-id': sat_azure_org.id,
                    'domain-id': sat_azure_domain.id,
                    'domain': sat_azure_domain.name,
                    'architecture-id': sat_azure_default_architecture.id,
                    'operatingsystem-id': sat_azure_default_os.id,
                    'root-password': gen_string('alpha'),
                    'image': module_azurerm_custom_finishimg.name,
                },
                timeout=1800000,
            )
            yield host
            with sat_azure.api_factory.satellite_setting('destroy_vm_on_host_delete=True'):
                if sat_azure.cli.Host.exists(search=('name', host['name'])):
                    sat_azure.cli.Host.delete({'name': self.fullhostname}, timeout=1800000)

    @pytest.fixture(scope='class')
    def azureclient_host(self, azurermclient, class_host_ft):
        """Returns the AzureRM Client Host object to perform the assertions"""
        return azurermclient.get_vm(name=class_host_ft['name'].split('.')[0])

    @pytest.mark.e2e
    @pytest.mark.upgrade
    @pytest.mark.tier3
    @pytest.mark.parametrize('sat_azure', ['sat'], indirect=True)
    def test_positive_azurerm_host_provisioned(
        self,
        class_host_ft,
        azureclient_host,
        module_azurerm_cr,
        module_azurerm_custom_finishimg,
    ):
        """Host can be provisioned on AzureRM

        :id: 9e8242e5-3ef3-4884-a200-7ba79b8ef49f

        :CaseImportance: Critical

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
        assert class_host_ft['compute-resource']['name'] == module_azurerm_cr.name
        assert (
            class_host_ft['operating-system']['image']['name']
            == module_azurerm_custom_finishimg.name
        )
        assert class_host_ft['network-interfaces']['1']['ipv4-address'] == azureclient_host.ip

        # Azure cloud
        assert self.hostname.lower() == azureclient_host.name
        assert self.vm_size == azureclient_host.type


@pytest.mark.run_in_one_thread
class TestAzureRMUserDataProvisioning:
    """AzureRM Host Provisioning Tests"""

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(
        self,
        request,
        sat_azure_domain,
        module_azurerm_cr,
        module_azurerm_cloudimg,
    ):
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
        request.cls.fullhostname = f'{self.hostname}.{sat_azure_domain.name}'.lower()
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
        sat_azure,
        module_azurerm_cloudimg,
        sat_azure_loc,
        sat_azure_org,
        sat_azure_default_os,
        azurerm_hostgroup,
    ):
        """
        Provisions the host on AzureRM using UserData template
        Later in tests this host will be used to perform assertions
        """
        with (
            sat_azure.hammer_api_timeout(),
            sat_azure.skip_yum_update_during_provisioning(template='Kickstart default user data'),
        ):
            host = sat_azure.cli.Host.create(
                {
                    'name': self.hostname,
                    'compute-attributes': self.compute_attrs,
                    'interface': self.interfaces_attributes,
                    'image': module_azurerm_cloudimg.name,
                    'hostgroup': azurerm_hostgroup.name,
                    'location': sat_azure_loc.name,
                    'organization': sat_azure_org.name,
                    'operatingsystem-id': sat_azure_default_os.id,
                },
                timeout=1800000,
            )
            yield host
            with sat_azure.api_factory.satellite_setting('destroy_vm_on_host_delete=True'):
                if sat_azure.cli.Host.exists(search=('name', host['name'])):
                    sat_azure.cli.Host.delete({'name': self.fullhostname}, timeout=1800000)

    @pytest.fixture(scope='class')
    def azureclient_host(self, azurermclient, class_host_ud):
        """Returns the AzureRM Client Host object to perform the assertions"""
        return azurermclient.get_vm(name=class_host_ud['name'].split('.')[0])

    @pytest.mark.upgrade
    @pytest.mark.tier3
    @pytest.mark.parametrize(
        'sat_azure', ['sat', 'puppet_sat'], indirect=True, ids=['satellite', 'puppet_enabled']
    )
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

        :CaseImportance: Critical

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
        assert class_host_ud['network-interfaces']['1']['ipv4-address'] == azureclient_host.ip
        assert class_host_ud['compute-resource']['name'] == module_azurerm_cr.name
        assert class_host_ud['operating-system']['image']['name'] == module_azurerm_cloudimg.name
        assert class_host_ud['host-group']['name'] == azurerm_hostgroup.name

        # Azure cloud
        assert self.hostname.lower() == azureclient_host.name
        assert self.vm_size == azureclient_host.type
