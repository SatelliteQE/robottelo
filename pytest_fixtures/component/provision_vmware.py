from broker import Broker
from fauxfactory import gen_string
import pytest
from wrapanapi import VMWareSystem
from wrapanapi.systems.virtualcenter import VMWareVirtualMachine

from robottelo.config import settings


@pytest.fixture(scope='module')
def vmware(request):
    versions = {
        'vmware7': settings.vmware.vcenter7,
        'vmware8': settings.vmware.vcenter8,
    }
    return versions[getattr(request, 'param', 'vmware8')]


@pytest.fixture
def vmwareclient(vmware):
    vmwareclient = VMWareSystem(
        hostname=vmware.hostname,
        username=settings.vmware.username,
        password=settings.vmware.password,
    )
    yield vmwareclient
    vmwareclient.disconnect()


@pytest.fixture(scope='module')
def module_vmware_cr(module_provisioning_sat, module_sca_manifest_org, module_location, vmware):
    return module_provisioning_sat.sat.api.VMWareComputeResource(
        name=gen_string('alpha'),
        provider='Vmware',
        url=vmware.hostname,
        user=settings.vmware.username,
        password=settings.vmware.password,
        datacenter=settings.vmware.datacenter,
        organization=[module_sca_manifest_org],
        location=[module_location],
    ).create()


@pytest.fixture
def module_vmware_hostgroup(
    module_vmware_cr,
    module_provisioning_sat,
    module_sca_manifest_org,
    module_location,
    default_architecture,
    module_provisioning_rhel_content,
    module_lce_library,
    default_partitiontable,
    module_provisioning_capsule,
    pxe_loader,
):
    return module_provisioning_sat.sat.api.HostGroup(
        name=gen_string('alpha'),
        organization=[module_sca_manifest_org],
        location=[module_location],
        architecture=default_architecture,
        domain=module_provisioning_sat.domain,
        content_source=module_provisioning_capsule.id,
        content_view=module_provisioning_rhel_content.cv,
        compute_resource=module_vmware_cr,
        kickstart_repository=module_provisioning_rhel_content.ksrepo,
        lifecycle_environment=module_lce_library,
        root_pass=settings.provisioning.host_root_password,
        operatingsystem=module_provisioning_rhel_content.os,
        ptable=default_partitiontable,
        subnet=module_provisioning_sat.subnet,
        pxe_loader=pxe_loader.pxe_loader,
        group_parameters_attributes=[
            # assign AK in order the hosts to be subscribed
            {
                'name': 'kt_activation_keys',
                'parameter_type': 'string',
                'value': module_provisioning_rhel_content.ak.name,
            },
        ],
    ).create()


@pytest.fixture
def module_vmware_image(
    module_provisioning_sat,
    module_vmware_cr,
    module_sca_manifest_org,
    module_location,
    module_provisioning_rhel_content,
    default_architecture,
    vmware,
):
    image_os = (
        module_provisioning_sat.sat.api.OperatingSystem()
        .search(query={'search': f'name=RedHat {settings.vmware.image_os.split()[1]}'})[0]
        .read()
    )
    if not image_os:
        image_os = module_provisioning_sat.sat.api.OperatingSystem(
            name=f'RedHat {settings.vmware.image_os.split()[1]}'
        ).create()
    return module_provisioning_sat.sat.api.Image(
        architecture=default_architecture,
        compute_resource=module_vmware_cr,
        name=gen_string('alpha'),
        operatingsystem=image_os,
        username='root',
        uuid=settings.vmware.image_name,
        password=settings.provisioning.host_root_password,
    ).create()


@pytest.fixture
def provisioning_vmware_host(pxe_loader, vmwareclient):
    """Fixture to check out blank VM on VMware"""
    vm_boot_firmware = 'efi' if pxe_loader.vm_firmware == 'uefi' else 'bios'
    provisioning_host = Broker(
        workflow='deploy-blank-vm-vcenter',
        artifacts='last',
        vm_network=settings.provisioning.vlan_id,
        vm_boot_firmware=vm_boot_firmware,
    ).execute()
    yield provisioning_host
    # delete the host
    vmware_host = VMWareVirtualMachine(vmwareclient, name=provisioning_host['name'])
    vmware_host.delete()
    # check if vm is deleted from VMware
    assert vmwareclient.does_vm_exist(provisioning_host['name']) is False
