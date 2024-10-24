"""Test for compute resource UI

:Requirement: Computeresource Vmware

:CaseAutomation: Automated

:CaseComponent: ComputeResources-VMWare

:Team: Rocket

:CaseImportance: High

"""

from math import floor, log10
from random import choice

import pytest
from wait_for import TimedOutError, wait_for
from wrapanapi.systems.virtualcenter import vim

from robottelo.config import settings
from robottelo.constants import (
    COMPUTE_PROFILE_LARGE,
    COMPUTE_PROFILE_SMALL,
    DEFAULT_LOC,
    FOREMAN_PROVIDERS,
    VMWARE_CONSTANTS,
)
from robottelo.hosts import ContentHost
from robottelo.utils.datafactory import gen_string
from robottelo.utils.issue_handlers import is_open

pytestmark = [pytest.mark.skip_if_not_set('vmware')]


def _round_to_2_significant_digits(x):
    return round(x, -int(floor(log10(abs(x)))) + 1)


def _get_normalized_size(size):
    """Convert a size in bytes to KB or MB or GB or TB

    example :

        _get_normalized_size(2527070196732)
        return '2.3 TB'

    :return a string size number + the corresponding suffix  B or KB or MB or GB or TB
    """
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    suffix_index = 0
    while size > 1024 and suffix_index < 4:
        suffix_index += 1
        size = size / 1024.0
    size = _round_to_2_significant_digits(size)
    if size == int(size):
        size = int(size)
    return f'{size} {suffixes[suffix_index]}'


def get_vmware_datastore_summary_string(vmwareclient):
    """Return the datastore string summary for data_store_name

    For "Local-Ironforge" datastore the string looks Like:

        "Local-Ironforge (free: 1.66 TB, prov: 2.29 TB, total: 2.72 TB)"
    """
    data_store_summary = [
        h
        for h in vmwareclient.get_obj_list(vim.Datastore)
        if h.host and h.name == settings.vmware.datastore
    ][0].summary
    uncommitted = data_store_summary.uncommitted or 0
    capacity = _get_normalized_size(data_store_summary.capacity)
    free_space = _get_normalized_size(data_store_summary.freeSpace)
    prov = _get_normalized_size(
        data_store_summary.capacity + uncommitted - data_store_summary.freeSpace
    )
    return f'{settings.vmware.datastore} (free: {free_space}, prov: {prov}, total: {capacity})'


@pytest.mark.e2e
@pytest.mark.tier1
@pytest.mark.parametrize('vmware', ['vmware7', 'vmware8'], indirect=True)
def test_positive_cr_end_to_end(session, module_org, module_location, vmware, module_target_sat):
    """Perform end-to-end testing for compute resource VMware component.

    :id: 47fc9e77-5b22-46b4-a76c-3217434fde2f

    :expectedresults: All expected CRUD actions finished successfully.
    """
    cr_name = gen_string('alpha')
    new_cr_name = gen_string('alpha')
    description = gen_string('alpha')
    display_type = choice(('VNC', 'VMRC'))
    vnc_console_passwords = choice((False, True))
    enable_caching = choice((False, True))
    new_org = module_target_sat.api.Organization().create()
    new_loc = module_target_sat.api.Location().create()
    with session:
        session.computeresource.create(
            {
                'name': cr_name,
                'description': description,
                'provider': FOREMAN_PROVIDERS['vmware'],
                'provider_content.vcenter': vmware.hostname,
                'provider_content.user': settings.vmware.username,
                'provider_content.password': settings.vmware.password,
                'provider_content.datacenter.value': settings.vmware.datacenter,
                'provider_content.display_type': display_type,
                'provider_content.vnc_console_passwords': vnc_console_passwords,
                'provider_content.enable_caching': enable_caching,
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_location.name],
            }
        )
        cr_values = session.computeresource.read(cr_name)
        assert cr_values['name'] == cr_name
        assert cr_values['description'] == description
        assert cr_values['provider'] == FOREMAN_PROVIDERS['vmware']
        assert cr_values['provider_content']['user'] == settings.vmware.username
        assert cr_values['provider_content']['datacenter']['value'] == settings.vmware.datacenter
        assert cr_values['provider_content']['display_type'] == display_type
        assert cr_values['provider_content']['vnc_console_passwords'] == vnc_console_passwords
        assert cr_values['provider_content']['enable_caching'] == enable_caching
        assert cr_values['organizations']['resources']['assigned'] == [module_org.name]
        assert cr_values['locations']['resources']['assigned'] == [module_location.name]
        session.computeresource.edit(
            cr_name,
            {
                'name': new_cr_name,
                'organizations.resources.assigned': [new_org.name],
                'locations.resources.assigned': [new_loc.name],
            },
        )
        assert not session.computeresource.search(cr_name)
        cr_values = session.computeresource.read(new_cr_name)
        assert cr_values['name'] == new_cr_name
        assert set(cr_values['organizations']['resources']['assigned']) == {
            module_org.name,
            new_org.name,
        }
        assert set(cr_values['locations']['resources']['assigned']) == {
            module_location.name,
            new_loc.name,
        }
        # check that the compute resource is listed in one of the default compute profiles
        profile_cr_values = session.computeprofile.list_resources(COMPUTE_PROFILE_LARGE)
        profile_cr_names = [cr['Compute Resource'] for cr in profile_cr_values]
        assert '{} ({})'.format(new_cr_name, FOREMAN_PROVIDERS['vmware']) in profile_cr_names
        session.computeresource.delete(new_cr_name)
        assert not session.computeresource.search(new_cr_name)


@pytest.mark.tier2
@pytest.mark.parametrize('vmware', ['vmware7', 'vmware8'], indirect=True)
def test_positive_retrieve_virtual_machine_list(session, vmware):
    """List the virtual machine list from vmware compute resource

    :id: 21ade57a-0caa-4144-9c46-c8e22f33414e

    :setup: vmware hostname and credentials.

    :steps:

        1. Select the created compute resource.
        2. Go to "Virtual Machines" tab.

    :expectedresults: The Virtual machines should be displayed
    """
    cr_name = gen_string('alpha')
    vm_name = settings.vmware.vm_name
    with session:
        session.computeresource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS['vmware'],
                'provider_content.vcenter': vmware.hostname,
                'provider_content.user': settings.vmware.username,
                'provider_content.password': settings.vmware.password,
                'provider_content.datacenter.value': settings.vmware.datacenter,
            }
        )
        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        assert (
            session.computeresource.search_virtual_machine(cr_name, vm_name)[0]['Name'] == vm_name
        )


@pytest.mark.e2e
@pytest.mark.tier2
@pytest.mark.parametrize('vmware', ['vmware7', 'vmware8'], indirect=True)
def test_positive_image_end_to_end(session, target_sat, vmware):
    """Perform end to end testing for compute resource VMware component image.

    :id: 6b7949ef-c684-40aa-b181-11f8d4cd39c6

    :expectedresults: All expected CRUD actions finished successfully.
    """
    cr_name = gen_string('alpha')
    image_name = gen_string('alpha')
    new_image_name = gen_string('alpha')
    os = target_sat.api_factory.check_create_os_with_title(settings.vmware.image_os)
    image_user_data = choice((False, True))
    with session:
        session.computeresource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS['vmware'],
                'provider_content.vcenter': vmware.hostname,
                'provider_content.user': settings.vmware.username,
                'provider_content.password': settings.vmware.password,
                'provider_content.datacenter.value': settings.vmware.datacenter,
            }
        )
        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        session.computeresource.create_image(
            cr_name,
            dict(
                name=image_name,
                operating_system=os.title,
                architecture=settings.vmware.image_arch,
                username=settings.vmware.image_username,
                user_data=image_user_data,
                password=settings.vmware.image_password,
                image=settings.vmware.image_name,
            ),
        )
        values = session.computeresource.read_image(cr_name, image_name)
        assert values['name'] == image_name
        assert values['operating_system'] == os.title
        assert values['architecture'] == settings.vmware.image_arch
        assert values['username'] == settings.vmware.image_username
        assert values['user_data'] == image_user_data
        assert values['image'] == settings.vmware.image_name
        session.computeresource.update_image(cr_name, image_name, dict(name=new_image_name))
        assert session.computeresource.search_images(cr_name, image_name)[0]['Name'] != image_name
        assert (
            session.computeresource.search_images(cr_name, new_image_name)[0]['Name']
            == new_image_name
        )
        session.computeresource.delete_image(cr_name, new_image_name)
        assert (
            session.computeresource.search_images(cr_name, new_image_name)[0]['Name']
            != new_image_name
        )


@pytest.mark.tier2
@pytest.mark.run_in_one_thread
@pytest.mark.parametrize('vmware', ['vmware7', 'vmware8'], indirect=True)
def test_positive_resource_vm_power_management(session, vmware):
    """Read current VMware Compute Resource virtual machine power status and
    change it to opposite one

    :id: faeabe45-5112-43a6-bde9-f869dfb26cf5

    :expectedresults: virtual machine is powered on or powered off depending on its initial state
    """
    cr_name = gen_string('alpha')
    vm_name = settings.vmware.vm_name
    with session:
        session.computeresource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS['vmware'],
                'provider_content.vcenter': vmware.hostname,
                'provider_content.user': settings.vmware.username,
                'provider_content.password': settings.vmware.password,
                'provider_content.datacenter.value': settings.vmware.datacenter,
            }
        )
        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        power_status = session.computeresource.vm_status(cr_name, vm_name)
        if power_status:
            session.computeresource.vm_poweroff(cr_name, vm_name)
        else:
            session.computeresource.vm_poweron(cr_name, vm_name)
        try:
            wait_for(
                lambda: (
                    session.browser.refresh(),
                    session.computeresource.vm_status(cr_name, vm_name),
                )[1]
                is not power_status,
                timeout=30,
                delay=2,
            )
        except TimedOutError as err:
            raise AssertionError('Timed out waiting for VM to toggle power state') from err


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.tier2
@pytest.mark.parametrize('vmware', ['vmware7', 'vmware8'], indirect=True)
def test_positive_vmware_custom_profile_end_to_end(
    session, vmware, request, target_sat, get_vmware_datastore_summary_string
):
    """Perform end to end testing for VMware compute profile.

    :id: 24f7bb5f-2aaf-48cb-9a56-d2d0713dfe3d

    :customerscenario: true

    :steps:

        1. Create a compute resource of type vmware.
        2. Update a compute profile with all values

    :expectedresults: Compute profiles are updated successfully with all the values.

    :BZ: 1315277

    :verifies: SAT-23630
    """
    cr_name = gen_string('alpha')
    guest_os_names = [
        'Red Hat Enterprise Linux 7 (64-bit)',
        'Red Hat Enterprise Linux 8 (64 bit)',
        'Red Hat Enterprise Linux 9 (64 bit)',
    ]
    compute_profile = ['1-Small', '2-Medium', '3-Large']
    cpus = ['2', '4', '6']
    vm_memory = ['4000', '6000', '8000']
    annotation_notes = gen_string('alpha')
    firmware_type = ['Automatic', 'BIOS', 'EFI']
    resource_pool = VMWARE_CONSTANTS['pool']
    folder = VMWARE_CONSTANTS['folder']
    virtual_hw_version = VMWARE_CONSTANTS['virtualhw_version']
    memory_hot_add = True
    cpu_hot_add = True
    cdrom_drive = True
    disk_size = '10 GB'
    network = 'VLAN 400'  # hardcoding network here as this test won't be doing actual provisioning
    storage_data = {
        'storage': {
            'controller': VMWARE_CONSTANTS['scsicontroller'],
            'disks': [
                {
                    'data_store': get_vmware_datastore_summary_string,
                    'size': disk_size,
                    'thin_provision': True,
                }
            ],
        }
    }
    network_data = {
        'network_interfaces': {
            'nic_type': VMWARE_CONSTANTS['network_interface_name'],
            'network': network,
        }
    }
    with session:
        session.computeresource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS['vmware'],
                'provider_content.vcenter': vmware.hostname,
                'provider_content.user': settings.vmware.username,
                'provider_content.password': settings.vmware.password,
                'provider_content.datacenter.value': settings.vmware.datacenter,
            }
        )

        @request.addfinalizer
        def _finalize():
            cr = target_sat.api.VMWareComputeResource().search(query={'search': f'name={cr_name}'})
            if cr:
                target_sat.api.VMWareComputeResource(id=cr[0].id).delete()

        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        for guest_os_name, cprofile, cpu, memory, firmware in zip(
            guest_os_names, compute_profile, cpus, vm_memory, firmware_type, strict=True
        ):
            session.computeresource.update_computeprofile(
                cr_name,
                cprofile,
                {
                    'provider_content.guest_os': guest_os_name,
                    'provider_content.cpus': cpu,
                    'provider_content.memory': memory,
                    'provider_content.cluster': settings.vmware.cluster,
                    'provider_content.annotation_notes': annotation_notes,
                    'provider_content.virtual_hw_version': virtual_hw_version,
                    'provider_content.firmware': firmware,
                    'provider_content.resource_pool': resource_pool,
                    'provider_content.folder': folder,
                    'provider_content.memory_hot_add': memory_hot_add,
                    'provider_content.cpu_hot_add': cpu_hot_add,
                    'provider_content.cdrom_drive': cdrom_drive,
                    'provider_content.storage': [value for value in storage_data.values()],
                    'provider_content.network_interfaces': [
                        value for value in network_data.values()
                    ],
                },
            )
            values = session.computeresource.read_computeprofile(cr_name, cprofile)
            provider_content = values['provider_content']
            assert provider_content['guest_os'] == guest_os_name
            assert provider_content['cpus'] == cpu
            assert provider_content['memory'] == memory
            assert provider_content['cluster'] == settings.vmware.cluster
            assert provider_content['annotation_notes'] == annotation_notes
            assert provider_content['virtual_hw_version'] == virtual_hw_version
            if not is_open('SAT-23630'):
                assert values['provider_content']['firmware'] == firmware
            assert provider_content['resource_pool'] == resource_pool
            assert provider_content['folder'] == folder
            assert provider_content['memory_hot_add'] == memory_hot_add
            assert provider_content['cpu_hot_add'] == cpu_hot_add
            assert provider_content['cdrom_drive'] == cdrom_drive
            assert (
                provider_content['storage'][0]['controller'] == VMWARE_CONSTANTS['scsicontroller']
            )
            assert provider_content['storage'][0]['disks'][0]['size'] == disk_size
            assert (
                provider_content['network_interfaces'][0]['nic_type']
                == VMWARE_CONSTANTS['network_interface_name']
            )
            assert provider_content['network_interfaces'][0]['network'] == network
        session.computeresource.delete(cr_name)
        assert not session.computeresource.search(cr_name)


@pytest.mark.tier2
@pytest.mark.parametrize('vmware', ['vmware7', 'vmware8'], indirect=True)
def test_positive_virt_card(session, target_sat, module_location, module_org, vmware):
    """Check to see that the Virtualization card appears for an imported VM

    :id: 0502d5a6-64c1-422f-a9ba-ac7c2ee7bad2

    :parametrized: no

    :expectedresults: Virtualization card appears in the new Host UI for the VM

    :CaseImportance: Medium
    """
    # create entities for hostgroup
    default_loc_id = (
        target_sat.api.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0].id
    )
    target_sat.api.SmartProxy(id=1, location=[default_loc_id, module_location.id]).update()
    domain = target_sat.api.Domain(
        organization=[module_org.id], location=[module_location]
    ).create()
    subnet = target_sat.api.Subnet(
        organization=[module_org.id], location=[module_location], domain=[domain]
    ).create()
    architecture = target_sat.api.Architecture().create()
    ptable = target_sat.api.PartitionTable(
        organization=[module_org.id], location=[module_location]
    ).create()
    operatingsystem = target_sat.api.OperatingSystem(
        architecture=[architecture], ptable=[ptable]
    ).create()
    medium = target_sat.api.Media(
        organization=[module_org.id], location=[module_location], operatingsystem=[operatingsystem]
    ).create()
    lce = (
        target_sat.api.LifecycleEnvironment(name="Library", organization=module_org.id)
        .search()[0]
        .read()
        .id
    )
    cv = target_sat.api.ContentView(organization=module_org).create()
    cv.publish()

    # create hostgroup
    hostgroup_name = gen_string('alpha')
    target_sat.api.HostGroup(
        name=hostgroup_name,
        architecture=architecture,
        domain=domain,
        subnet=subnet,
        location=[module_location.id],
        medium=medium,
        operatingsystem=operatingsystem,
        organization=[module_org],
        ptable=ptable,
        lifecycle_environment=lce,
        content_view=cv,
        content_source=1,
    ).create()
    cr_name = gen_string('alpha')
    with session:
        session.computeresource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS['vmware'],
                'provider_content.vcenter': vmware.hostname,
                'provider_content.user': settings.vmware.username,
                'provider_content.password': settings.vmware.password,
                'provider_content.datacenter.value': settings.vmware.datacenter,
                'locations.resources.assigned': [module_location.name],
                'organizations.resources.assigned': [module_org.name],
            }
        )
        session.hostgroup.update(hostgroup_name, {'host_group.deploy': cr_name + " (VMware)"})
        session.computeresource.vm_import(
            cr_name,
            settings.vmware.vm_name,
            hostgroup_name,
            module_location.name,
            name=settings.vmware.vm_name,
        )
        host_name = '.'.join([settings.vmware.vm_name, domain.name])
        power_status = session.computeresource.vm_status(cr_name, settings.vmware.vm_name)
        if power_status is False:
            session.computeresource.vm_poweron(cr_name, settings.vmware.vm_name)
            try:
                wait_for(
                    lambda: (
                        session.browser.refresh(),
                        session.computeresource.vm_status(cr_name, settings.vmware.vm_name),
                    )[1]
                    is not power_status,
                    timeout=30,
                    delay=2,
                )
            except TimedOutError as err:
                raise AssertionError('Timed out waiting for VM to toggle power state') from err

        virt_card = session.host_new.get_virtualization(host_name)['details']
        assert virt_card['datacenter'] == settings.vmware.datacenter
        assert virt_card['cluster'] == settings.vmware.cluster
        assert virt_card['memory'] == '5 GB'
        assert 'public_ip_address' in virt_card
        assert virt_card['mac_address'] == vmware.mac_address
        assert virt_card['cpus'] == '1'
        if 'disk_label' in virt_card:
            assert virt_card['disk_label'] == 'Hard disk 1'
        if 'disk_capacity' in virt_card:
            assert virt_card['disk_capacity'] != ''
        if 'partition_capacity' in virt_card:
            assert virt_card['partition_capacity'] != ''
        if 'partition_path' in virt_card:
            assert virt_card['partition_path'] == '/boot'
        if 'partition_allocation' in virt_card:
            assert virt_card['partition_allocation'] != ''
        assert virt_card['cores_per_socket'] == '1'
        assert virt_card['firmware'] == 'bios'
        assert virt_card['hypervisor'] != ''
        assert virt_card['connection_state'] == 'connected'
        assert virt_card['overall_status'] == 'green'
        assert virt_card['annotation_notes'] == ''
        assert virt_card['running_on'] == cr_name
        target_sat.api.Host(
            id=target_sat.api.Host().search(query={'search': f'name={host_name}'})[0].id
        ).delete()


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize(
    'setting_update',
    ['remote_execution_connect_by_ip=True', 'destroy_vm_on_host_delete=True'],
    indirect=True,
)
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.parametrize('provision_method', ['build'])
@pytest.mark.rhel_ver_match('[8]')
@pytest.mark.tier3
def test_positive_provision_end_to_end(
    request,
    module_sca_manifest_org,
    module_location,
    pxe_loader,
    module_vmware_cr,
    module_vmware_hostgroup,
    provision_method,
    setting_update,
    vmware,
    vmwareclient,
    target_sat,
    module_provisioning_rhel_content,
):
    """Assign Ansible role to a Hostgroup and verify ansible role execution job is scheduled after a host is provisioned

    :id: 500f32e8-c1db-4ef9-ae20-0dbb5bccf2ea

    :steps:
        1. Import role(s) available by default.
        2. Assign role(s) to Hostgroup.
        3. Provision a Host with Hostgroup.
        4. In Host -> Overview -> Select the "Recent Job" action.
        5. Verify that the Ansible roles job has been Scheduled.

    :expectedresults: Assign ansible role is successfully executed on the provisioned host.

    :BZ: 2025523

    :Verifies: SAT-24780

    :customerscenario: true
    """
    SELECTED_ROLE = 'theforeman.foreman_scap_client'
    host_name = gen_string('alpha').lower()
    guest_os_names = 'Red Hat Enterprise Linux 8 (64 bit)'
    network_data = {
        'network_interfaces': {
            'nic_type': VMWARE_CONSTANTS['network_interface_name'],
            'network': f'VLAN {settings.provisioning.vlan_id}',
        }
    }
    proxy_id = target_sat.nailgun_smart_proxy.id
    target_sat.api.AnsibleRoles().sync(data={'proxy_id': proxy_id, 'role_names': [SELECTED_ROLE]})
    with target_sat.ui_session() as session:
        session.location.select(module_location.name)
        session.organization.select(module_sca_manifest_org.name)
        session.hostgroup.assign_role_to_hostgroup(
            module_vmware_hostgroup.name, {'ansible_roles.resources': SELECTED_ROLE}
        )
        assert SELECTED_ROLE in session.hostgroup.read_role(
            module_vmware_hostgroup.name, SELECTED_ROLE
        )
        session.computeresource.update_computeprofile(
            entity_name=module_vmware_cr.name,
            compute_profile=COMPUTE_PROFILE_SMALL,
            values={
                'provider_content.memory': '6000',
                'provider_content.cluster': settings.vmware.cluster,
                'provider_content.guest_os': guest_os_names,
                'provider_content.storage': get_vmware_datastore_summary_string(vmwareclient),
                'provider_content.network_interfaces': [value for value in network_data.values()],
            },
        )
        session.host.create(
            {
                'host.name': host_name,
                'host.hostgroup': module_vmware_hostgroup.name,
                'host.inherit_deploy_option': False,
                'host.deploy': module_vmware_cr.name + f' ({FOREMAN_PROVIDERS["vmware"]})',
                'host.inherit_compute_profile_option': False,
                'host.compute_profile': COMPUTE_PROFILE_SMALL,
            }
        )
        request.addfinalizer(lambda: target_sat.provisioning_cleanup(host_name))
        wait_for(
            lambda: session.host_new.get_host_statuses(host_name)['Build']['Status']
            != 'Pending installation',
            timeout=1800,
            delay=30,
            fail_func=session.browser.refresh,
            silent_failure=True,
            handle_exception=True,
        )
        values = session.host_new.get_host_statuses(
            f'{host_name}.{module_vmware_hostgroup.domain.read().name}'
        )
        assert values['Build']['Status'] == 'Installed'
        assert values['Execution']['Status'] == 'Last execution succeeded'

        # Verify if assigned role is executed on the host, and correct host passwd is set
        host = ContentHost(target_sat.api.Host().search(query={'host': host_name})[0].read().ip)
        assert host.execute('yum list installed rubygem-foreman_scap_client').status == 0
