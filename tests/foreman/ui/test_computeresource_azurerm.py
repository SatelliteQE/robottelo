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

from robottelo.api.utils import skip_yum_update_during_provisioning
from robottelo.config import settings
from robottelo.constants import AZURERM_FILE_URI
from robottelo.constants import AZURERM_PLATFORM_DEFAULT
from robottelo.constants import AZURERM_VM_SIZE_DEFAULT
from robottelo.constants import COMPUTE_PROFILE_SMALL

pytestmark = [pytest.mark.skip_if_not_set('azurerm')]


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_azure_cp_attrs(module_azurerm_cr, module_azurerm_finishimg):
    """Create compute attributes on COMPUTE_PROFILE_SMALL"""

    nw_id = module_azurerm_cr.available_networks()['results'][-1]['id']
    return entities.ComputeAttribute(
        compute_profile=COMPUTE_PROFILE_SMALL,
        compute_resource=module_azurerm_cr,
        vm_attrs={
            "resource_group": settings.azurerm.resource_group,
            "vm_size": AZURERM_VM_SIZE_DEFAULT,
            "username": module_azurerm_finishimg.username,
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
    module_azurerm_cr,
    module_azure_cp_attrs,
    default_architecture,
    default_os,
    module_puppet_environment,
    default_smart_proxy,
    module_domain,
    module_location,
    module_org,
):
    """Create hostgroup"""

    return entities.HostGroup(
        architecture=default_architecture,
        compute_resource=module_azurerm_cr,
        compute_profile=COMPUTE_PROFILE_SMALL,
        domain=module_domain,
        location=[module_location],
        environment=module_puppet_environment,
        puppet_proxy=default_smart_proxy,
        puppet_ca_proxy=default_smart_proxy,
        content_source=default_smart_proxy,
        operatingsystem=default_os,
        organization=[module_org],
    ).create()


@pytest.mark.skip_if_open("BZ:1850934")
@pytest.mark.tier4
def test_positive_end_to_end_azurerm_ft_host_provision(
    session,
    azurermclient,
    module_azurerm_finishimg,
    module_azurerm_cr,
    module_domain,
    module_org,
    module_location,
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
    fqdn = f'{hostname}.{module_domain.name}'.lower()

    with session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)

        # Provision Host
        try:
            skip_yum_update_during_provisioning(template='Kickstart default finish')
            session.host.create(
                {
                    'host.name': hostname,
                    'host.hostgroup': module_azure_hg.name,
                    'provider_content.operating_system.root_password': gen_string('alpha'),
                    'provider_content.operating_system.image': module_azurerm_finishimg.name,
                }
            )

            host_info = session.host.get_details(fqdn)
            assert 'Installed' in host_info['properties']['properties_table']['Build']
            assert host_info['properties']['properties_table']['Host group'] == module_azure_hg.name

            # AzureRm Cloud assertion
            azurecloud_vm = azurermclient.get_vm(name=hostname.lower())
            assert azurecloud_vm
            assert azurecloud_vm.is_running
            assert azurecloud_vm.name == hostname.lower()
            assert azurecloud_vm.ip == host_info['properties']['properties_table']['IP Address']
            assert azurecloud_vm.type == AZURERM_VM_SIZE_DEFAULT

            # Host Delete
            session.host.delete(fqdn)
            assert not session.host.search(fqdn)

            # AzureRm Cloud assertion
            assert not azurecloud_vm.exists

        except Exception as error:
            azure_vm = entities.Host().search(query={'search': f'name={fqdn}'})
            if azure_vm:
                azure_vm[0].delete(synchronous=False)
            raise error

        finally:
            skip_yum_update_during_provisioning(template='Kickstart default finish', reverse=True)


@pytest.mark.skip_if_open("BZ:1850934")
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_azurerm_host_provision_ud(
    session,
    azurermclient,
    module_azurerm_cloudimg,
    module_azurerm_cr,
    module_domain,
    default_os,
    module_org,
    module_location,
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
    fqdn = f'{hostname}.{module_domain.name}'.lower()

    with session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)

        # Provision Host
        try:
            skip_yum_update_during_provisioning(template='Kickstart default user data')
            session.host.create(
                {
                    'host.name': hostname,
                    'host.hostgroup': module_azure_hg.name,
                    'provider_content.operating_system.root_password': gen_string('alpha'),
                    'provider_content.operating_system.image': module_azurerm_cloudimg.name,
                }
            )

            host_info = session.host.get_details(fqdn)
            assert 'Pending installation' in host_info['properties']['properties_table']['Build']
            assert host_info['properties']['properties_table']['Host group'] == module_azure_hg.name

            # AzureRm Cloud assertion
            azurecloud_vm = azurermclient.get_vm(name=hostname.lower())
            assert azurecloud_vm
            assert azurecloud_vm.is_running
            assert azurecloud_vm.name == hostname.lower()
            assert azurecloud_vm.ip == host_info['properties']['properties_table']['IP Address']
            assert azurecloud_vm.type == AZURERM_VM_SIZE_DEFAULT

        finally:
            skip_yum_update_during_provisioning(
                template='Kickstart default user data', reverse=True
            )
            azure_vm = entities.Host().search(query={'search': f'name={fqdn}'})
            if azure_vm:
                azure_vm[0].delete(synchronous=False)
