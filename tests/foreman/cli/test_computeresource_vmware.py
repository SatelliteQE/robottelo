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

from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.hosts import ContentHost


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.parametrize('vmware', ['vmware7', 'vmware8'], indirect=True)
def test_positive_vmware_cr_end_to_end(target_sat, module_org, module_location, vmware):
    """Create, Read, Update and Delete VMware compute resources

    :id: 96faae3f-bc64-4147-a9fc-09c858e0a68f

    :customerscenario: true

    :expectedresults: Compute resource should be created, read, updated and deleted

    :BZ: 1387917

    :CaseImportance: Critical
    """
    cr_name = gen_string('alpha')
    # Create
    vmware_cr = target_sat.cli.ComputeResource.create(
        {
            'name': cr_name,
            'organization-ids': module_org.id,
            'location-ids': module_location.id,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'server': vmware.hostname,
            'user': settings.vmware.username,
            'password': settings.vmware.password,
            'datacenter': settings.vmware.datacenter,
        }
    )
    assert vmware_cr['name'] == cr_name
    assert vmware_cr['locations'][0] == module_location.name
    assert vmware_cr['organizations'][0] == module_org.name
    assert vmware_cr['server'] == vmware.hostname
    assert vmware_cr['datacenter'] == settings.vmware.datacenter
    # List
    target_sat.cli.ComputeResource.list({'search': f'name="{cr_name}"'})
    assert vmware_cr['name'] == cr_name
    assert vmware_cr['provider'] == FOREMAN_PROVIDERS['vmware']
    # Update CR
    new_cr_name = gen_string('alpha')
    description = gen_string('alpha')
    target_sat.cli.ComputeResource.update(
        {'name': cr_name, 'new-name': new_cr_name, 'description': description}
    )
    # Check updated values
    result = target_sat.cli.ComputeResource.info({'id': vmware_cr['id']})
    assert result['name'] == new_cr_name
    assert result['description'] == description
    # Delete CR
    target_sat.cli.ComputeResource.delete({'name': result['name']})
    assert not target_sat.cli.ComputeResource.exists(search=('name', result['name']))


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
@pytest.mark.parametrize('vmware', ['vmware7', 'vmware8'], indirect=True)
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi', 'secureboot'], indirect=True)
@pytest.mark.parametrize('provision_method', ['build', 'bootdisk'])
@pytest.mark.rhel_ver_match('[7]')
def test_positive_provision_end_to_end(
    request,
    setting_update,
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

    :id: ff9963fc-a2a7-4392-aa9a-190d5d1c8357

    :steps:
        1. Configure provisioning setup.
        2. Create VMware CR
        3. Configure host group setup.
        4. Provision a host on VMware
        5. Verify created host on VMware with wrapanapi

    :expectedresults: Host is provisioned successfully with hostgroup

    :Verifies: SAT-25810

    :customerscenario: true
    """
    sat = module_provisioning_sat.sat
    hostname = gen_string('alpha').lower()
    host = sat.cli.Host.create(
        {
            'name': hostname,
            'organization': module_sca_manifest_org.name,
            'location': module_location.name,
            'hostgroup': module_vmware_hostgroup.name,
            'compute-resource-id': module_vmware_cr.id,
            'ip': None,
            'mac': None,
            'compute-attributes': f'cluster={settings.vmware.cluster},'
            f'path=/Datacenters/{settings.vmware.datacenter}/vm/,'
            'scsi_controller_type=VirtualLsiLogicController,'
            f'guest_id=rhel7_64Guest,firmware={pxe_loader.vm_firmware},'
            'cpus=1,memory_mb=6000, start=1',
            'interface': f'compute_type=VirtualVmxnet3,'
            f'compute_network=VLAN {settings.provisioning.vlan_id}',
            'volume': f'name=Hard disk,size_gb=10,thin=true,eager_zero=false,storage_pod={settings.vmware.datastore_cluster}',
            'provision-method': provision_method,
        }
    )
    # teardown
    request.addfinalizer(lambda: sat.provisioning_cleanup(host['name'], interface='CLI'))

    hostname = f'{hostname}.{module_provisioning_sat.domain.name}'
    assert hostname == host['name']
    # check if vm is created on vmware
    assert vmwareclient.does_vm_exist(hostname) is True
    wait_for(
        lambda: sat.cli.Host.info({'name': hostname})['status']['build-status']
        != 'Pending installation',
        timeout=1800,
        delay=30,
    )
    host_info = sat.cli.Host.info({'id': host['id']})
    assert host_info['status']['build-status'] == 'Installed'

    # Verify SecureBoot is enabled on host after provisioning is completed successfully
    if pxe_loader.vm_firmware == 'uefi_secure_boot':
        provisioning_host = ContentHost(host_info['network']['ipv4-address'])
        # Wait for the host to be rebooted and SSH daemon to be started.
        provisioning_host.wait_for_connection()
        assert 'SecureBoot enabled' in provisioning_host.execute('mokutil --sb-state').stdout


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
@pytest.mark.parametrize('vmware', ['vmware7', 'vmware8'], indirect=True)
@pytest.mark.rhel_ver_match('[8]')
@pytest.mark.skip_if_open('SAT-35643')
def test_positive_image_provision_end_to_end(
    request,
    setting_update,
    module_provisioning_sat,
    module_sca_manifest_org,
    module_location,
    pxe_loader,
    module_vmware_cr,
    module_vmware_image,
    module_vmware_hostgroup,
    vmware,
    vmwareclient,
):
    """Provision a host with image on vmware compute resource with
    the help of hostgroup.

    :id: 8f0e2278-b897-4927-9c21-d84313623cc4

    :steps:
        1. Configure provisioning setup.
        2. Create VMware CR
        3. Create VMware image
        4. Configure host group setup.
        5. Provision a host on VMware
        6. Verify created host on VMware with wrapanapi

    :expectedresults: Host is provisioned successfully.

    :verifies: SAT-30594
    """
    sat = module_provisioning_sat.sat
    hostname = gen_string('alpha').lower()
    host = sat.cli.Host.create(
        {
            'name': hostname,
            'organization': module_sca_manifest_org.name,
            'location': module_location.name,
            'hostgroup': module_vmware_hostgroup.name,
            'compute-resource-id': module_vmware_cr.id,
            'image': module_vmware_image.name,
            'ip': None,
            'mac': None,
            #'parameters': 'name=package_upgrade,type=boolean,value=false',
            'typed-parameters': r'name=package_upgrade\,value=false\,parameter_type=boolean',
            'compute-attributes': f'cluster={settings.vmware.cluster},'
            f'path=/Datacenters/{settings.vmware.datacenter}/vm/,'
            'scsi_controller_type=VirtualLsiLogicController,'
            'guest_id=rhel8_64Guest,firmware=automatic,virtual_tpm=true'
            'cpus=1,memory_mb=6000, start=1',
            'interface': 'compute_type=VirtualVmxnet3,'
            f'compute_network=VLAN {settings.provisioning.vlan_id}',
            'volume': f'name=Hard disk,size_gb=10,thin=true,eager_zero=false,storage_pod={settings.vmware.datastore_cluster}',
            'provision-method': 'image',
        }
    )
    # teardown
    request.addfinalizer(lambda: sat.provisioning_cleanup(host['name'], interface='CLI'))

    hostname = f'{hostname}.{module_provisioning_sat.domain.name}'
    assert hostname == host['name']
    # check if vm is created on vmware
    assert vmwareclient.does_vm_exist(hostname) is True

    # Check if virtual TPM device is added to created VM (only for UEFI)
    if pxe_loader.vm_firmware != 'bios':
        vm = vmwareclient.get_vm(hostname)
        assert 'VirtualTPM' in vm.get_virtual_device_type_names()

    wait_for(
        lambda: sat.cli.Host.info({'name': hostname})['status']['build-status']
        != 'Pending installation',
        timeout=1800,
        delay=30,
    )

    host_info = sat.cli.Host.info({'id': host['id']})
    assert host_info['status']['build-status'] == 'Installed'
    # check if correct OS version is installed
    expected_rhel_version = host_info['operating-system']['operating-system']['name'].split(" ")[1]
    host_ip = host_info['network']['ipv4-address']
    host_ssh_os = sat.execute(
        f'sshpass -p {settings.provisioning.host_root_password} '
        'ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no -o PasswordAuthentication=yes '
        f'-o UserKnownHostsFile=/dev/null root@{host_ip} cat /etc/redhat-release'
    )
    assert host_ssh_os.status == 0
    assert expected_rhel_version in host_ssh_os.stdout, (
        f'The installed OS version differs from the expected version {expected_rhel_version}'
    )
