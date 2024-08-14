"""
:Requirement: Computeresource Vmware

:CaseComponent: ComputeResources-VMWare

:Team: Rocket

:CaseImportance: High

:CaseAutomation: Automated

"""

from fauxfactory import gen_string
import pytest
from wait_for import wait_for
from wrapanapi.systems.virtualcenter import VMWareVirtualMachine

from robottelo.config import settings


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
@pytest.mark.parametrize('vmware', ['vmware7', 'vmware8'], indirect=True)
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.parametrize('provision_method', ['build', 'bootdisk'])
@pytest.mark.rhel_ver_match('[8]')
def test_positive_provision_end_to_end(
    request,
    setting_update,
    module_provisioning_rhel_content,
    module_provisioning_sat,
    module_sca_manifest_org,
    module_location,
    pxe_loader,
    module_vmware_cr,
    module_vmware_hostgroup,
    provision_method,
    vmware,
    vmwareclient,
):
    """Provision a host on vmware compute resource with
    the help of hostgroup.

    :id: 6985e7c0-d258-4fc4-833b-e680804b55e8

    :steps:

        1. Configure provisioning setup.
        2. Create VMware CR
        3. Configure host group setup.
        4. Provision a host on VMware
        5. Verify created host on VMware with wrapanapi

    :expectedresults: Host is provisioned succesfully with hostgroup

    :CaseImportance: Critical

    :Verifies: SAT-23417, SAT-23558

    :customerscenario: true

    :BZ: 2186114

    :verifies: SAT-18721
    """
    sat = module_provisioning_sat.sat
    name = gen_string('alpha').lower()
    host = sat.api.Host(
        hostgroup=module_vmware_hostgroup,
        organization=module_sca_manifest_org,
        location=module_location,
        name=name,
        operatingsystem=module_provisioning_rhel_content.os,
        subnet=module_provisioning_sat.subnet,
        compute_attributes={
            'path': '/Datacenters/SatQE-Datacenter/vm/',
            'cpus': 2,
            'memory_mb': 6000,
            'firmware': 'bios' if pxe_loader.vm_firmware == 'bios' else 'efi',
            'cluster': f'{settings.vmware.cluster}',
            'start': '1',
            'guest_id': 'rhel8_64Guest',
            'scsi_controllers': [{'type': 'ParaVirtualSCSIController', 'key': 1001}],
            'nvme_controllers': [{'type': 'VirtualNVMEController', 'key': 2001}],
            'volumes_attributes': {
                '0': {
                    'size_gb': 8,
                    'thin': '1',
                    'storage_pod': settings.vmware.datastore_cluster,
                    'controller_key': 2001,
                },
                '1': {
                    'size_gb': 8,
                    'thin': '1',
                    'storage_pod': settings.vmware.datastore_cluster,
                    'controller_key': 1001,
                },
            },
        },
        interfaces_attributes={
            '0': {
                'type': 'interface',
                'primary': True,
                'managed': True,
                'compute_attributes': {
                    'model': 'VirtualVmxnet3',
                    'network': f'VLAN {settings.provisioning.vlan_id}',
                },
            }
        },
        provision_method=provision_method,
        build=True,
    ).create(create_missing=False)

    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))
    assert host.name == f'{name}.{module_provisioning_sat.domain.name}'
    # check if vm is created on vmware
    assert vmwareclient.does_vm_exist(host.name) is True
    # check the build status
    wait_for(
        lambda: host.read().build_status_label != 'Pending installation',
        timeout=1500,
        delay=10,
    )
    assert host.read().build_status_label == 'Installed'


@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('module_provisioning_sat', ['discovery'], indirect=True)
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
@pytest.mark.tier3
def test_positive_provision_vmware_pxe_discovery(
    request,
    module_provisioning_rhel_content,
    module_discovery_sat,
    provisioning_hostgroup,
    provisioning_vmware_host,
    pxe_loader,
    vmwareclient,
):
    """Provision a pxe-based discovered host on VMware

    :id: 29d46a87-bd6f-4963-9ed6-b3456c600779

    :parametrized: yes

    :Setup: Provisioning and discovery should be configured

    :steps:
        1. Boot up the host to discover
        2. Provision the host

    :expectedresults: Host should be provisioned successfully

    """
    mac = provisioning_vmware_host['provisioning_nic_mac_addr']
    sat = module_discovery_sat.sat
    # start the provisioning host
    vmware_host = VMWareVirtualMachine(vmwareclient, name=provisioning_vmware_host['name'])
    vmware_host.start()
    wait_for(
        lambda: sat.api.DiscoveredHost().search(query={'mac': mac}) != [],
        timeout=1500,
        delay=40,
    )
    discovered_host = sat.api.DiscoveredHost().search(query={'mac': mac})[0]
    discovered_host.hostgroup = provisioning_hostgroup
    discovered_host.location = provisioning_hostgroup.location[0]
    discovered_host.organization = provisioning_hostgroup.organization[0]
    discovered_host.build = True
    host = discovered_host.update(['hostgroup', 'build', 'location', 'organization'])
    host = sat.api.Host().search(query={'search': f'name={host.name}'})[0]
    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))
    wait_for(
        lambda: host.read().build_status_label != 'Pending installation',
        timeout=1500,
        delay=10,
    )
    assert host.read().build_status_label == 'Installed'
    assert not sat.api.DiscoveredHost().search(query={'mac': mac})
