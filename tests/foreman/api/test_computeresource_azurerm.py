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

from robottelo.api.utils import satellite_setting
from robottelo.config import settings
from robottelo.constants import AZURERM_FILE_URI
from robottelo.constants import AZURERM_PLATFORM_DEFAULT
from robottelo.constants import AZURERM_PREMIUM_OS_Disk
from robottelo.constants import AZURERM_RHEL7_FT_CUSTOM_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_GALLERY_IMG_URN
from robottelo.constants import AZURERM_RHEL7_FT_IMG_URN
from robottelo.constants import AZURERM_RHEL7_UD_IMG_URN
from robottelo.constants import AZURERM_VM_SIZE_DEFAULT


class TestAzureRMComputeResourceTestCase:
    """Tests for ``api/v2/compute_resources``"""

    @pytest.mark.upgrade
    @pytest.mark.tier1
    def test_positive_crud_azurerm_cr(self, module_org, module_location, azurerm_settings,default_sat):
        """Create, Read, Update and Delete AzureRM compute resources

        :id: da081a1f-9614-4918-91cb-c900c40ac121

        :expectedresults: Compute resource should be created, read, updated and deleted

        :CaseImportance: Critical

        :CaseLevel: Component
        """
        # Create CR
        cr_name = gen_string('alpha')
        compresource = default_sat.api.AzureRMComputeResource(
            name=cr_name,
            provider='AzureRm',
            tenant=azurerm_settings['tenant'],
            app_ident=azurerm_settings['app_ident'],
            sub_id=azurerm_settings['sub_id'],
            secret_key=azurerm_settings['secret'],
            region=azurerm_settings['region'],
            organization=[module_org],
            location=[module_location],
        ).create()
        assert compresource.name == cr_name
        assert compresource.provider == 'AzureRm'
        assert compresource.tenant == azurerm_settings['tenant']
        assert compresource.app_ident == azurerm_settings['app_ident']
        assert compresource.sub_id == azurerm_settings['sub_id']
        assert compresource.region == azurerm_settings['region']

        # Update CR
        new_cr_name = gen_string('alpha')
        description = gen_string('utf8')
        compresource.name = new_cr_name
        compresource.description = description
        compresource = compresource.update(['name', 'description'])
        assert compresource.name == new_cr_name
        assert compresource.description == description

        # Delete CR
        compresource.delete()
        assert not default_sat.api.AzureRMComputeResource().search(query={'search': f'name={new_cr_name}'})

    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_create_finish_template_image(
        self, default_architecture, module_azurerm_cr, module_azurerm_finishimg
    ):
        """Finish template image along with username is being added in AzureRM CR

        :id: 78facb19-4b27-454b-abc5-2c69c0a6c28a

        :steps:
            1. Create a AzureRM Compute Resource.
            2. Add a finish template based image in it.

        :expectedresults: Finish template image should be added in AzureRM CR along with username

        :CaseImportance: Critical

        :CaseLevel: Integration
        """

        assert module_azurerm_finishimg.architecture.id == default_architecture.id
        assert module_azurerm_finishimg.compute_resource == module_azurerm_cr
        assert module_azurerm_finishimg.username == settings.azurerm.username
        assert module_azurerm_finishimg.uuid == AZURERM_RHEL7_FT_IMG_URN

    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_create_cloud_init_image(
        self, module_azurerm_cloudimg, module_azurerm_cr, default_architecture
    ):
        """Cloud Init template image along with username is being added in AzureRM CR

        :id: 05ea1b20-0dfe-4af3-b1b7-a82604aa1e79

        :steps:
            1. Create a AzureRM Compute Resource.
            2. Add a Cloud init supported image in it.

        :expectedresults: Cloud init image should be added in AzureRM CR along with username

        :CaseLevel: Integration
        """

        assert module_azurerm_cloudimg.architecture.id == default_architecture.id
        assert module_azurerm_cloudimg.compute_resource.id == module_azurerm_cr.id
        assert module_azurerm_cloudimg.username == settings.azurerm.username
        assert module_azurerm_cloudimg.uuid == AZURERM_RHEL7_UD_IMG_URN

    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_check_available_networks(self, azurermclient, module_azurerm_cr):
        """Check networks from AzureRM CR are available to select during host provision.

        :id: aee5d077-668e-4f4d-adee-6472f0e4ecaa

        :expectedresults: All the networks from AzureRM CR should be available.

        :CaseLevel: Integration
        """
        cr_nws = module_azurerm_cr.available_networks()
        portal_nws = azurermclient.list_network()
        assert len(portal_nws) == len(cr_nws['results'])

    @pytest.mark.stubbed
    @pytest.mark.tier2
    def test_gov_cloud_regions_from_azure_compute_resources(self):
        """Check Azure Gov Cloud for US Cloud region options when creating a compute resource

        :id: 65e03f7e-a2c7-4541-b92b-38d80ab48175

        :CaseImportance: Medium

        :CaseLevel: Acceptance

        :CaseAutomation: ManualOnly

        :steps:
            1. Create Azure Compute Resource
            2. Select US Government Cloud option
            3. Input Client ID, tenant ID, Secret, and Sub Id
            4. Verify you can select US regions
            5. Test connection and create compute resource

        :expectedresults: All regions below should be visible
            1. US DoD Central
            2. US DoD East
            3. US Gov Arizona
            4. US Gov Iowa
            5. US Gov Texas
            6. US Gov Virginia

        :BZ: 1829107

        :customerscenario: true
        """


@pytest.mark.run_in_one_thread
class TestAzureRMHostProvisioningTestCase:
    """AzureRM Host Provisioning Tests"""

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(
        self, request, module_puppet_domain, module_azurerm_cr_puppet, module_azurerm_finishimg_puppet
    ):
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
        request.cls.fullhostname = f'{self.hostname}.{module_puppet_domain.name}'.lower()

        request.cls.compute_attrs = {
            "resource_group": self.rg_default,
            "vm_size": self.vm_size,
            "username": module_azurerm_finishimg_puppet.username,
            "password": settings.azurerm.password,
            "platform": self.platform,
            "script_command": 'touch /var/tmp/text.txt',
            "script_uris": AZURERM_FILE_URI,
            "image_id": self.rhel7_ft_img,
        }
        nw_id = module_azurerm_cr_puppet.available_networks()['results'][-1]['id']
        request.cls.interfaces_attributes = {
            "0": {
                "compute_attributes": {
                    "public_ip": "Dynamic",
                    "private_ip": "false",
                    "network": nw_id,
                }
            }
        }

    @pytest.fixture(scope='class')
    def class_host_ft(
        self,
        session_puppet_enabled_sat,
        azurermclient,
        module_azurerm_finishimg_puppet,
        module_azurerm_cr_puppet,
        session_puppet_default_architecture,
        module_puppet_domain,
        module_puppet_loc,
        module_puppet_org,
        session_puppet_default_os,
        session_puppet_enabled_proxy,
        module_puppet_environment,
    ):
        """
        Provisions the host on AzureRM using Finish template
        Later in tests this host will be used to perform assertions
        """

        with session_puppet_enabled_sat.skip_yum_update_during_provisioning(
            template='Kickstart default finish'
        ):
            host = session_puppet_enabled_sat.api.Host(
                architecture=session_puppet_default_architecture,
                build=True,
                compute_resource=module_azurerm_cr_puppet,
                compute_attributes=self.compute_attrs,
                interfaces_attributes=self.interfaces_attributes,
                domain=module_puppet_domain,
                organization=module_puppet_org,
                operatingsystem=session_puppet_default_os,
                location=module_puppet_loc,
                name=self.hostname,
                provision_method='image',
                image=module_azurerm_finishimg_puppet,
                root_pass=gen_string('alphanumeric'),
                environment=module_puppet_environment,
                puppet_proxy=session_puppet_enabled_proxy,
                puppet_ca_proxy=session_puppet_enabled_proxy,
            ).create()
            yield host
            with satellite_setting('destroy_vm_on_host_delete=True'):
                host.delete()

    @pytest.fixture(scope='class')
    def azureclient_host(self, azurermclient, class_host_ft):
        """Returns the AzureRM Client Host object to perform the assertions"""

        return azurermclient.get_vm(name=class_host_ft.name.split('.')[0])

    @pytest.mark.skip_if_open("BZ:1850934")
    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_positive_azurerm_host_provisioned(self, class_host_ft, azureclient_host):
        """Host can be provisioned on AzureRM

        :id: ff27905f-fa3c-43ac-b969-9525b32f75f5

        :CaseLevel: Component

        ::CaseImportance: Critical

        :steps:
            1. Create a AzureRM Compute Resource and provision host.

        :expectedresults:
            1. The host should be provisioned on AzureRM
            2. The host name should be the same as given in data to provision the host
            3. The host should show Installed status for provisioned host
            4. The provisioned host should be assigned with external IP
            5. The host Name and Platform should be same on Azure Cloud as provided during
               provisioned

        :BZ: 1850934
        """

        assert class_host_ft.name == self.fullhostname
        assert class_host_ft.build_status_label == "Installed"
        assert class_host_ft.ip == azureclient_host.ip

        # Azure cloud
        assert self.hostname.lower() == azureclient_host.name
        assert self.vm_size == azureclient_host.type

    @pytest.mark.skip_if_open("BZ:1850934")
    @pytest.mark.tier3
    def test_positive_azurerm_host_power_on_off(self, class_host_ft, azureclient_host):
        """Host can be powered on and off

        :id: 9ced29d7-d866-4d0c-ac27-78753b5b5a94

        :CaseLevel: System

        :steps:
            1. Create a AzureRM Compute Resource.
            2. Provision a Host on Azure Cloud using above CR.
            3. Power off the host from satellite.
            4. Power on the host again from satellite.

        :expectedresults:
            1. The provisioned host should be powered off.
            2. The provisioned host should be powered on.

        :BZ: 1850934
        """
        class_host_ft.power(data={'power_action': 'stop'})
        assert azureclient_host.is_stopped
        class_host_ft.power(data={'power_action': 'start'})
        assert azureclient_host.is_started


@pytest.mark.run_in_one_thread
class TestAzureRMUserDataProvisioning:
    """AzureRM UserData Host Provisioning Tests"""

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(
        self, request, module_puppet_domain, module_azurerm_cr_puppet, module_azurerm_finishimg_puppet
    ):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """

        request.cls.region = settings.azurerm.azure_region
        request.cls.rhel7_ud_img = AZURERM_RHEL7_UD_IMG_URN
        request.cls.rg_default = settings.azurerm.resource_group
        request.cls.premium_os_disk = AZURERM_PREMIUM_OS_Disk
        request.cls.platform = AZURERM_PLATFORM_DEFAULT
        request.cls.vm_size = AZURERM_VM_SIZE_DEFAULT
        request.cls.hostname = f'test-{gen_string("alpha")}'
        request.cls.fullhostname = f'{self.hostname}.{module_puppet_domain.name}'.lower()

        request.cls.compute_attrs = {
            "resource_group": self.rg_default,
            "vm_size": self.vm_size,
            "username": module_azurerm_finishimg_puppet.username,
            "ssh_key_data": settings.azurerm.ssh_pub_key,
            "platform": self.platform,
            "script_command": 'touch /var/tmp/text.txt',
            "script_uris": AZURERM_FILE_URI,
            "image_id": self.rhel7_ud_img,
        }

        nw_id = module_azurerm_cr_puppet.available_networks()['results'][-1]['id']
        request.cls.interfaces_attributes = {
            "0": {
                "compute_attributes": {
                    "public_ip": "Dynamic",
                    "private_ip": "false",
                    "network": nw_id,
                }
            }
        }

    @pytest.fixture(scope='class')
    def class_host_ud(
        self,
        session_puppet_enabled_sat,
        azurermclient,
        module_azurerm_cloudimg_puppet,
        module_azurerm_cr_puppet,
        session_puppet_default_architecture,
        module_puppet_domain,
        module_puppet_loc,
        module_puppet_org,
        session_puppet_default_os,
        session_puppet_enabled_proxy,
        module_puppet_environment,
    ):
        """
        Provisions the host on AzureRM using Userdata template
        Later in tests this host will be used to perform assertions
        """

        with session_puppet_enabled_sat.skip_yum_update_during_provisioning(
            template='Kickstart default finish'
        ):
            host = session_puppet_enabled_sat.api.Host(
                architecture=session_puppet_default_architecture,
                build=True,
                compute_resource=module_azurerm_cr_puppet,
                compute_attributes=self.compute_attrs,
                interfaces_attributes=self.interfaces_attributes,
                domain=module_puppet_domain,
                organization=module_puppet_org,
                operatingsystem=session_puppet_default_os,
                location=module_puppet_loc,
                name=self.hostname,
                provision_method='image',
                image=module_azurerm_cloudimg_puppet,
                root_pass=gen_string('alphanumeric'),
                environment=module_puppet_environment,
                puppet_proxy=session_puppet_enabled_proxy,
                puppet_ca_proxy=session_puppet_enabled_proxy,
            ).create()
            yield host
            with satellite_setting('destroy_vm_on_host_delete=True'):
                host.delete()

    @pytest.fixture(scope='class')
    def azureclient_host(self, azurermclient, class_host_ud):
        """Returns the AzureRM Client Host object to perform the assertions"""

        return azurermclient.get_vm(name=class_host_ud.name.split('.')[0])

    @pytest.mark.skip_if_open("BZ:1850934")
    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_positive_azurerm_ud_host_provisioned(self, class_host_ud, azureclient_host):
        """Host can be provisioned on AzureRm with userdata image/template

        :id: df496d7c-3443-4afe-b807-5bbfc90e866e

        :CaseLevel: Component

        ::CaseImportance: Critical

        :steps:
            1. Create a AzureRM Compute Resource and provision host.

        :expectedresults:
            1. The host should be provisioned on AzureRM
            2. The host name should be the same as given in data to provision the host
            3. The host should show "Pending installation" status for provisioned host(
               as Satellite and VM are in diff networks hence status shows as "Pending
               installation")
            4. The provisioned host should be assigned with external IP
            5. The host Name and Platform should be same on Azure Cloud as provided during
               provisioned.

        :BZ: 1850934
        """

        assert class_host_ud.name == self.fullhostname
        assert class_host_ud.build_status_label == "Pending installation"
        assert class_host_ud.ip == azureclient_host.ip

        # Azure cloud
        assert self.hostname.lower() == azureclient_host.name
        assert self.vm_size == azureclient_host.type

    @pytest.mark.skip_if_open("BZ:1850934")
    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_positive_host_disassociate_associate(self, class_host_ud, module_azurerm_cr_puppet):
        """Host can be Disassociate and Associate

        :id: 9514f15c-64b4-48ef-9707-fd4d39adc57d

        :steps:
            1. Disassociate a provision host and Associate it.

        :expectedresults:
            1. The host should be Disassociate
            2. The host should be Associate

        :BZ: 1850934
        """

        # Disassociate
        disasso = class_host_ud.disassociate()
        assert not disasso['compute_resource_name']

        # Associate
        asso = module_azurerm_cr_puppet.associate()
        assert len(asso['results']) > 0
        host = class_host_ud.read()
        assert host.compute_resource.id == module_azurerm_cr_puppet.id


@pytest.mark.run_in_one_thread
class TestAzureRMSharedGalleryFinishTemplateProvisioning:
    """AzureRM Host Provisioning Tests with Shared Image Gallery"""

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(
        self,
        request,
        module_puppet_domain,
        module_azurerm_cr_puppet,
        module_azurerm_gallery_finishimg_puppet,
    ):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """
        request.cls.region = settings.azurerm.azure_region
        request.cls.hostname = f'test-{gen_string("alpha")}'
        request.cls.fullhostname = f'{self.hostname}.{module_puppet_domain.name}'.lower()

        request.cls.compute_attrs = {
            "resource_group": settings.azurerm.resource_group,
            "vm_size": AZURERM_VM_SIZE_DEFAULT,
            "username": module_azurerm_gallery_finishimg.username,
            "password": settings.azurerm.password,
            "platform": AZURERM_PLATFORM_DEFAULT,
            "script_command": 'touch /var/tmp/text.txt',
            "script_uris": AZURERM_FILE_URI,
            "image_id": AZURERM_RHEL7_FT_GALLERY_IMG_URN,
        }

        nw_id = module_azurerm_cr_puppet.available_networks()['results'][-1]['id']
        request.cls.interfaces_attributes = {
            "0": {
                "compute_attributes": {
                    "public_ip": "Dynamic",
                    "private_ip": "false",
                    "network": nw_id,
                }
            }
        }

    @pytest.fixture(scope='class')
    def class_host_gallery_ft(
        self,
        session_puppet_enabled_sat,
        azurermclient,
        module_azurerm_gallery_finishimg_puppet,
        module_azurerm_cr_puppet,
        session_puppet_default_architecture,
        module_puppet_domain,
        module_puppet_loc,
        module_puppet_org,
        session_puppet_default_os,
        session_puppet_enabled_proxy,
        module_puppet_environment,
    ):
        """
        Provisions the host on AzureRM using Finish template
        Later in tests this host will be used to perform assertions
        """

        with session_puppet_enabled_sat.skip_yum_update_during_provisioning(
            template='Kickstart default finish'
        ):
            host = session_puppet_enabled_sat.api.Host(
                architecture=session_puppet_default_architecture,
                build=True,
                compute_resource=module_azurerm_cr_puppet,
                compute_attributes=self.compute_attrs,
                interfaces_attributes=self.interfaces_attributes,
                domain=module_puppet_domain,
                organization=module_puppet_org,
                operatingsystem=session_puppet_default_os,
                location=module_puppet_loc,
                name=self.hostname,
                provision_method='image',
                image=module_azurerm_gallery_finishimg_puppet,
                root_pass=gen_string('alphanumeric'),
                environment=module_puppet_environment,
                puppet_proxy=session_puppet_enabled_proxy,
                puppet_ca_proxy=session_puppet_enabled_proxy,
            ).create()
            yield host
            with satellite_setting('destroy_vm_on_host_delete=True'):
                host.delete()

    @pytest.fixture(scope='class')
    def azureclient_host(self, azurermclient, class_host_gallery_ft):
        """Returns the AzureRM Client Host object to perform the assertions"""

        return azurermclient.get_vm(name=class_host_gallery_ft.name.split('.')[0])

    @pytest.mark.skip_if_open("BZ:1850934")
    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_positive_azurerm_shared_gallery_host_provisioned(
        self, class_host_gallery_ft, azureclient_host
    ):
        """Host can be provisioned on AzureRM using Shared Gallery Image

        :id: 60fce78f-57fd-48e6-9dd0-23a7cc7e4c1c

        :CaseLevel: System

        :CaseImportance: Critical

        :steps:
            1. Create a AzureRM Compute Resource with Shared Gallery Image and provision host.

        :expectedresults:
            1. The host should be provisioned on AzureRM using Shared Gallery Image
            2. The host name should be the same as given in data to provision the host
            3. The host should show Installed status for provisioned host
            4. The provisioned host should be assigned with external IP
            5. The host Name and Platform should be same on Azure Cloud as provided during
               provisioned

        :BZ: 1850934
        """

        assert class_host_gallery_ft.name == self.fullhostname
        assert class_host_gallery_ft.build_status_label == "Installed"
        assert class_host_gallery_ft.ip == azureclient_host.ip

        # Azure cloud
        assert self.hostname.lower() == azureclient_host.name
        assert AZURERM_VM_SIZE_DEFAULT == azureclient_host.type


@pytest.mark.run_in_one_thread
class TestAzureRMCustomImageFinishTemplateProvisioning:
    """AzureRM Host Provisioning Tests with Custom Image"""

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(
        self,
        request,
        module_puppet_domain,
        module_azurerm_cr_puppet,
        module_azurerm_custom_finishimg_puppet,
    ):
        """
        Sets Constants for all the Tests, fixtures which will be later used for assertions
        """
        request.cls.region = settings.azurerm.azure_region
        request.cls.hostname = f'test-{gen_string("alpha")}'
        request.cls.fullhostname = f'{self.hostname}.{module_puppet_domain.name}'.lower()

        request.cls.compute_attrs = {
            "resource_group": settings.azurerm.resource_group,
            "vm_size": AZURERM_VM_SIZE_DEFAULT,
            "username": module_azurerm_custom_finishimg_puppet.username,
            "password": settings.azurerm.password,
            "platform": AZURERM_PLATFORM_DEFAULT,
            "script_command": 'touch /var/tmp/text.txt',
            "script_uris": AZURERM_FILE_URI,
            "image_id": AZURERM_RHEL7_FT_CUSTOM_IMG_URN,
        }

        nw_id = module_azurerm_cr_puppet.available_networks()['results'][-1]['id']
        request.cls.interfaces_attributes = {
            "0": {
                "compute_attributes": {
                    "public_ip": "Dynamic",
                    "private_ip": "false",
                    "network": nw_id,
                }
            }
        }

    @pytest.fixture(scope='class')
    def class_host_custom_ft(
        self,
        session_puppet_enabled_sat,
        azurermclient,
        module_azurerm_custom_finishimg_puppet,
        module_azurerm_cr_puppet,
        session_puppet_default_architecture,
        module_puppet_domain,
        module_puppet_loc,
        module_puppet_org,
        session_puppet_default_os,
        session_puppet_enabled_proxy,
        module_puppet_environment,
    ):
        """
        Provisions the host on AzureRM using Finish template
        Later in tests this host will be used to perform assertions
        """

        with session_puppet_enabled_sat.skip_yum_update_during_provisioning(
            template='Kickstart default finish'
        ):
            host = session_puppet_enabled_sat.api.Host(
                architecture=session_puppet_default_architecture,
                build=True,
                compute_resource=module_azurerm_cr_puppet,
                compute_attributes=self.compute_attrs,
                interfaces_attributes=self.interfaces_attributes,
                domain=module_puppet_domain,
                organization=module_puppet_org,
                operatingsystem=session_puppet_default_os,
                location=module_puppet_loc,
                name=self.hostname,
                provision_method='image',
                image=module_azurerm_custom_finishimg_puppet,
                root_pass=gen_string('alphanumeric'),
                environment=module_puppet_environment,
                puppet_proxy=session_puppet_enabled_proxy,
                puppet_ca_proxy=session_puppet_enabled_proxy,
            ).create()
            yield host
            with satellite_setting('destroy_vm_on_host_delete=True'):
                host.delete()

    @pytest.fixture(scope='class')
    def azureclient_host(self, azurermclient, class_host_custom_ft):
        """Returns the AzureRM Client Host object to perform the assertions"""

        return azurermclient.get_vm(name=class_host_custom_ft.name.split('.')[0])

    @pytest.mark.skip_if_open("BZ:1850934")
    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_positive_azurerm_custom_image_host_provisioned(
        self, class_host_custom_ft, azureclient_host
    ):
        """Host can be provisioned on AzureRM using Custom Image

        :id: b5be5128-ad49-4dbd-a660-3e38ce012327

        :CaseLevel: System

        :CaseImportance: Critical

        :steps:
            1. Create a AzureRM Compute Resource with Custom Image and provision host.

        :expectedresults:
            1. The host should be provisioned on AzureRM using Custom Image
            2. The host name should be the same as given in data to provision the host
            3. The host should show Installed status for provisioned host
            4. The provisioned host should be assigned with external IP
            5. The host Name and Platform should be same on Azure Cloud as provided during
               provisioned

        :BZ: 1850934
        """

        assert class_host_custom_ft.name == self.fullhostname
        assert class_host_custom_ft.build_status_label == "Installed"
        assert class_host_custom_ft.ip == azureclient_host.ip

        # Azure cloud
        assert self.hostname.lower() == azureclient_host.name
        assert AZURERM_VM_SIZE_DEFAULT == azureclient_host.type