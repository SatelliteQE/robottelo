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

from robottelo.api.utils import satellite_setting
from robottelo.config import settings
from robottelo.constants import AZURERM_FILE_URI
from robottelo.constants import AZURERM_PLATFORM_DEFAULT
from robottelo.constants import AZURERM_VM_SIZE_DEFAULT
from robottelo.constants import COMPUTE_PROFILE_SMALL

pytestmark = [pytest.mark.skip_if_not_set('azurerm')]


@pytest.fixture(scope='module')
def module_azure_cp_attrs(
    module_azurerm_cr_puppet, module_azurerm_finishimg_puppet, session_puppet_enabled_sat
):
    """Create compute attributes on COMPUTE_PROFILE_SMALL"""

    nw_id = module_azurerm_cr_puppet.available_networks()['results'][-1]['id']
    return session_puppet_enabled_sat.api.ComputeAttribute(
        compute_profile=COMPUTE_PROFILE_SMALL,
        compute_resource=module_azurerm_cr_puppet,
        vm_attrs={
            "resource_group": settings.azurerm.resource_group,
            "vm_size": AZURERM_VM_SIZE_DEFAULT,
            "username": module_azurerm_finishimg_puppet.username,
            "password": settings.azurerm.password,
            "platform": AZURERM_PLATFORM_DEFAULT,
            "script_command": "touch /var/tmp/text.txt",
            "script_uris": AZURERM_FILE_URI,
            "volumes_attributes": {"0": {"disk_size_gb": "5"}},
            "interfaces_attributes": {
                "0": {"public_ip": "Static", "private_ip": "false", "network": nw_id}
            },
        },
    ).create()


@pytest.fixture(scope='module')
def module_azure_hg(
    session_puppet_enabled_sat,
    module_azurerm_cr_puppet,
    module_azure_cp_attrs,
    session_puppet_default_architecture,
    session_puppet_default_os,
    module_puppet_environment,
    session_puppet_enabled_proxy,
    module_puppet_domain,
    module_puppet_loc,
    module_puppet_org,
):
    """Create hostgroup"""

    return session_puppet_enabled_sat.api.HostGroup(
        architecture=session_puppet_default_architecture,
        compute_resource=module_azurerm_cr_puppet,
        compute_profile=COMPUTE_PROFILE_SMALL,
        domain=module_puppet_domain,
        location=[module_puppet_loc],
        environment=module_puppet_environment,
        puppet_proxy=session_puppet_enabled_proxy,
        puppet_ca_proxy=session_puppet_enabled_proxy,
        content_source=session_puppet_enabled_proxy,
        operatingsystem=session_puppet_default_os,
        organization=[module_puppet_org],
    ).create()


@pytest.mark.tier4
def test_positive_end_to_end_azurerm_ft_host_provision(
    session,
    session_puppet_enabled_sat,
    azurermclient,
    module_azurerm_finishimg_puppet,
    module_azurerm_cr_puppet,
    module_puppet_domain,
    module_puppet_org,
    module_puppet_loc,
    module_azure_hg,
):

    """Provision Host with hostgroup and Compute-profile using
    finish template on AzureRm compute resource

    :id: d64d249d-70a2-4329-bff4-3b50b8596c44

    :expectedresults:
            1. Host is provisioned.
            2. Host is deleted Successfully.

    :CaseLevel: System

    :BZ: 1850934
    """
    hostname = f'test-{gen_string("alpha")}'
    fqdn = f'{hostname}.{module_puppet_domain.name}'.lower()
    finishimg_image = module_azurerm_finishimg_puppet.name

    with session_puppet_enabled_sat.ui_session as session:
        session.organization.select(org_name=module_puppet_org.name)
        session.location.select(loc_name=module_puppet_loc.name)

        # Provision Host
        try:
            with session_puppet_enabled_sat.skip_yum_update_during_provisioning(
                template='Kickstart default finish'
            ):
                session.host.create(
                    {
                        'host.name': hostname,
                        'host.hostgroup': module_azure_hg.name,
                        'provider_content.operating_system.root_password': gen_string('alpha'),
                        'provider_content.operating_system.image': finishimg_image,
                    }
                )

                host_info = session.host.get_details(fqdn)
                assert 'Installed' in host_info['properties']['properties_table']['Build']
                assert (
                    host_info['properties']['properties_table']['Host group']
                    == module_azure_hg.name
                )

                # AzureRm Cloud assertion
                azurecloud_vm = azurermclient.get_vm(name=hostname.lower())
                assert azurecloud_vm
                assert azurecloud_vm.is_running
                assert azurecloud_vm.name == hostname.lower()
                assert azurecloud_vm.ip == host_info['properties']['properties_table']['IP Address']
                assert azurecloud_vm.type == AZURERM_VM_SIZE_DEFAULT

                # Host Delete
                with satellite_setting('destroy_vm_on_host_delete=True'):
                    session.host.delete(fqdn)
                assert not session.host.search(fqdn)

                # AzureRm Cloud assertion
                assert not azurecloud_vm.exists

        except Exception as error:
            azure_vm = session_puppet_enabled_sat.api.Host().search(
                query={'search': f'name={fqdn}'}
            )
            if azure_vm:
                azure_vm[0].delete(synchronous=False)
            azurecloud_vm = azurermclient.get_vm(name=hostname.lower())
            if azurecloud_vm.exists:
                azurecloud_vm.delete()
            raise error


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_azurerm_host_provision_ud(
    session,
    session_puppet_enabled_sat,
    azurermclient,
    module_azurerm_cloudimg_puppet,
    module_azurerm_cr_puppet,
    module_puppet_domain,
    session_puppet_default_os,
    module_puppet_org,
    module_puppet_loc,
    module_azure_hg,
):

    """Provision a Host with hostgroup and Compute-profile using
    cloud-init image on AzureRm compute resource

    :id: 2dc6c494-0e80-4845-af8f-43d37f69a093

    :expectedresults: Host is provisioned successfully.

    :CaseImportance: Critical

    :CaseLevel: System

    :BZ: 1850934
    """

    hostname = f'test-{gen_string("alpha")}'
    fqdn = f'{hostname}.{module_puppet_domain.name}'.lower()
    cloudimg_image = module_azurerm_cloudimg_puppet.name

    with session_puppet_enabled_sat.ui_session as session:
        session.organization.select(org_name=module_puppet_org.name)
        session.location.select(loc_name=module_puppet_loc.name)
        # Provision Host
        try:
            with session_puppet_enabled_sat.skip_yum_update_during_provisioning(
                template='Kickstart default user data'
            ):
                session.host.create(
                    {
                        'host.name': hostname,
                        'host.hostgroup': module_azure_hg.name,
                        'provider_content.operating_system.root_password': gen_string('alpha'),
                        'provider_content.operating_system.image': cloudimg_image,
                    }
                )

                host_info = session.host.get_details(fqdn)
                assert (
                    'Pending installation' in host_info['properties']['properties_table']['Build']
                )
                assert (
                    host_info['properties']['properties_table']['Host group']
                    == module_azure_hg.name
                )

                # AzureRm Cloud assertion
                azurecloud_vm = azurermclient.get_vm(name=hostname.lower())
                assert azurecloud_vm
                assert azurecloud_vm.is_running
                assert azurecloud_vm.name == hostname.lower()
                assert azurecloud_vm.ip == host_info['properties']['properties_table']['IP Address']
                assert azurecloud_vm.type == AZURERM_VM_SIZE_DEFAULT

        finally:
            azure_vm = session_puppet_enabled_sat.api.Host().search(
                query={'search': f'name={fqdn}'}
            )
            if azure_vm:
                with satellite_setting('destroy_vm_on_host_delete=True'):
                    azure_vm[0].delete(synchronous=False)
