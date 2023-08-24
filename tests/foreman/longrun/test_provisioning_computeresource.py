"""
:CaseLevel: Acceptance

:CaseComponent: ComputeResources

:Team: Rocket

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from wrapanapi import VMWareSystem

from robottelo.cli.factory import make_compute_resource
from robottelo.cli.factory import make_host
from robottelo.cli.host import Host
from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import VMWARE_CONSTANTS


@pytest.fixture(scope="module")
def vmware():
    bridge = settings.vlan_networking.bridge
    vmware = type("", (), {})()
    vmware.vmware_server = settings.vmware.vcenter
    vmware.vmware_password = settings.vmware.password
    vmware.vmware_username = settings.vmware.username
    vmware.vmware_datacenter = settings.vmware.datacenter
    vmware.vmware_img_name = settings.vmware.image_name
    vmware.vmware_img_arch = settings.vmware.image_arch
    vmware.vmware_img_os = settings.vmware.image_os
    vmware.vmware_img_user = settings.vmware.image_username
    vmware.vmware_img_pass = settings.vmware.image_password
    vmware.vmware_vm_name = settings.vmware.vm_name
    vmware.current_interface = VMWARE_CONSTANTS.get('network_interfaces') % bridge
    vmware.vmware_api = VMWareSystem(
        hostname=vmware.vmware_server,
        username=vmware.vmware_username,
        password=vmware.vmware_password,
    )
    vmware.vmware_net_id = vmware.vmware_api.get_network(vmware.current_interface)._moId
    return vmware


@pytest.fixture(scope="module")
def provisioning(module_org, module_location, target_sat):
    os = None
    if hasattr(settings, 'rhev') and hasattr(settings.rhev, 'image_os') and settings.rhev.image_os:
        os = settings.rhev.image_os
    provisioning = type("", (), {})()
    provisioning.org_name = module_org.name
    provisioning.loc_name = module_location.name
    provisioning.config_env = target_sat.api_factory.configure_provisioning(
        compute=True, org=module_org, loc=module_location, os=os
    )
    provisioning.os_name = provisioning.config_env['os']
    return provisioning


@pytest.fixture(scope="module")
def vmware_cr(provisioning, vmware):
    return make_compute_resource(
        {
            'name': gen_string('alpha'),
            'organizations': provisioning.org_name,
            'locations': provisioning.loc_name,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'server': vmware.vmware_server,
            'user': vmware.vmware_username,
            'password': vmware.vmware_password,
            'datacenter': vmware.vmware_datacenter,
        }
    )


@pytest.fixture(scope="function")
def tear_down(provisioning):
    """Delete the hosts to free the resources"""
    yield
    hosts = Host.list({'organization': provisioning.org_name})
    for host in hosts:
        Host.delete({'id': host['id']})


@pytest.mark.on_premises_provisioning
@pytest.mark.vlan_networking
@pytest.mark.tier3
def test_positive_provision_vmware_with_host_group(
    vmware, provisioning, tear_down, vmware_cr, target_sat
):
    """Provision a host on vmware compute resource with
    the help of hostgroup.

    :Requirement: Computeresource Vmware

    :CaseComponent: ComputeResources-VMWare

    :Team: Rocket

    :customerscenario: true

    :id: ae4d5949-f0e6-44ca-93b6-c5241a02b64b

    :setup:

        1. Vaild vmware hostname ,credentials.
        2. Configure provisioning setup.
        3. Configure host group setup.

    :steps:

        1. Go to "Hosts --> New host".
        2. Assign the host group to the host.
        3. Select the Deploy on as vmware Compute Resource.
        4. Provision the host.

    :expectedresults: The host should be provisioned with host group

    :CaseAutomation: Automated

    :CaseLevel: System
    """
    host_name = gen_string('alpha').lower()
    host = make_host(
        {
            'name': f'{host_name}',
            'root-password': gen_string('alpha'),
            'organization': provisioning.org_name,
            'location': provisioning.loc_name,
            'hostgroup': provisioning.config_env['host_group'],
            'pxe-loader': 'PXELinux BIOS',
            'compute-resource-id': vmware_cr.get('id'),
            'compute-attributes': "cpus=2,"
            "corespersocket=2,"
            "memory_mb=4028,"
            "cluster={},"
            "path=/Datacenters/{}/vm/QE,"
            "guest_id=rhel7_64Guest,"
            "scsi_controller_type=VirtualLsiLogicController,"
            "hardware_version=Default,"
            "start=1".format(VMWARE_CONSTANTS['cluster'], vmware.vmware_datacenter),
            'ip': None,
            'mac': None,
            'interface': "compute_network={},"
            "compute_type=VirtualVmxnet3".format(vmware.vmware_net_id),
            'volume': "name=Hard disk,"
            "size_gb=10,"
            "thin=true,"
            "eager_zero=false,"
            "datastore={}".format(VMWARE_CONSTANTS['datastore'].split()[0]),
            'provision-method': 'build',
        }
    )
    hostname = '{}.{}'.format(host_name, provisioning.config_env['domain'])
    assert hostname == host['name']
    # Check on Vmware, if VM exists
    assert vmware.vmware_api.does_vm_exist(hostname)
    host_info = Host.info({'name': hostname})
    host_ip = host_info.get('network').get('ipv4-address')
    # Start to run a ping check if network was established on VM
    target_sat.ping_host(host=host_ip)


@pytest.mark.on_premises_provisioning
@pytest.mark.vlan_networking
@pytest.mark.tier3
def test_positive_provision_vmware_with_host_group_bootdisk(
    vmware, provisioning, tear_down, vmware_cr, target_sat
):
    """Provision a bootdisk based host on VMWare compute resource.

    :Requirement: Computeresource Vmware

    :CaseComponent: ComputeResources-VMWare

    :id: bc5f457d-c29a-4c62-bbdc-af8f4f813519

    :bz: 1679225

    :setup:

        1. Vaild VMWare hostname, credentials.
        2. Configure provisioning setup.
        3. Configure host group setup.

    :steps: Using Hammer CLI, Provision a VM on VMWare with hostgroup and
        provisioning method as `bootdisk`.

    :expectedresults: The host should be provisioned with provisioning type bootdisk

    :CaseAutomation: Automated

    :customerscenario: true

    :CaseLevel: System
    """
    host_name = gen_string('alpha').lower()
    host = make_host(
        {
            'name': f'{host_name}',
            'root-password': gen_string('alpha'),
            'organization': provisioning.org_name,
            'location': provisioning.loc_name,
            'hostgroup': provisioning.config_env['host_group'],
            'pxe-loader': 'PXELinux BIOS',
            'compute-resource-id': vmware_cr.get('id'),
            'content-source-id': '1',
            'compute-attributes': "cpus=2,"
            "corespersocket=2,"
            "memory_mb=4028,"
            "cluster={},"
            "path=/Datacenters/{}/vm/QE,"
            "guest_id=rhel7_64Guest,"
            "scsi_controllers=`type=VirtualLsiLogicController,key=1000',"
            "hardware_version=Default,"
            "start=1".format(VMWARE_CONSTANTS['cluster'], vmware.vmware_datacenter),
            "ip": None,
            "mac": None,
            'interface': "compute_network={},"
            "compute_type=VirtualVmxnet3".format(vmware.vmware_net_id),
            'volume': "name=Hard disk,"
            "size_gb=10,"
            "thin=true,"
            "eager_zero=false,"
            "datastore={}".format(VMWARE_CONSTANTS['datastore'].split()[0]),
            'provision-method': 'bootdisk',
        }
    )
    hostname = '{}.{}'.format(host_name, provisioning.config_env['domain'])
    assert hostname == host['name']
    # Check on Vmware, if VM exists
    assert vmware.vmware_api.does_vm_exist(hostname)
    host_info = Host.info({'name': hostname})
    host_ip = host_info.get('network').get('ipv4-address')
    # Start to run a ping check if network was established on VM
    target_sat.ping_host(host=host_ip)
