"""Test for compute resource UI

:Requirement: Computeresource Vmware

:CaseAutomation: Automated

:CaseComponent: UI

:CaseLevel: Acceptance

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

import pytest
from nailgun import entities
from wrapanapi.systems.virtualcenter import vim, VMWareSystem

from robottelo.api.utils import check_create_os_with_title
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    fixture,
    run_in_one_thread,
    setting_is_set,
    tier2
)
from robottelo.config import settings
from robottelo.constants import COMPUTE_PROFILE_LARGE, FOREMAN_PROVIDERS, VMWARE_CONSTANTS

if not setting_is_set('vmware'):
    pytest.skip('skipping tests due to missing vmware settings', allow_module_level=True)


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
    if size >= 100:
        size = round(size, 0)
    else:
        size = round(size, 2)
    if size == int(size):
        size = int(size)
    return '{0} {1}'.format(size, suffixes[suffix_index])


def _get_vmware_datastore_summary_string(data_store_name=VMWARE_CONSTANTS['datastore']):
    """Return the datastore string summary for data_store_name

    For "Local-Ironforge" datastore the string looks Like:

        "Local-Ironforge (free: 1.66 TB, prov: 2.29 TB, total: 2.72 TB)"
     """
    system = VMWareSystem(
        hostname=settings.vmware.vcenter,
        username=settings.vmware.username,
        password=settings.vmware.password
    )
    data_store_summary = [h for h in system.get_obj_list(vim.Datastore)
                          if h.host and h.name == data_store_name][0].summary
    uncommitted = data_store_summary.uncommitted or 0
    capacity = _get_normalized_size(data_store_summary.capacity)
    free_space = _get_normalized_size(data_store_summary.freeSpace)
    prov = _get_normalized_size(data_store_summary.capacity + uncommitted
                                - data_store_summary.freeSpace)
    return '{0} (free: {1}, prov: {2}, total: {3})'.format(
        data_store_name, free_space, prov, capacity)


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_vmware_settings():
    return dict(
        vcenter=settings.vmware.vcenter,
        user=settings.vmware.username,
        password=settings.vmware.password,
        datacenter=settings.vmware.datacenter,
        image_name=settings.vmware.image_name,
        image_arch=settings.vmware.image_arch,
        image_os=settings.vmware.image_os,
        image_username=settings.vmware.image_username,
        image_password=settings.vmware.image_password,
        vm_name=settings.vmware.vm_name,
        current_interface=VMWARE_CONSTANTS['network_interfaces'] % settings.vlan_networking.bridge
    )


@tier2
def test_positive_end_to_end(session, module_org, module_loc, module_vmware_settings):
    """Perform end to end testing for compute resource VMware component.

    :id: 47fc9e77-5b22-46b4-a76c-3217434fde2f

    :expectedresults: All expected CRUD actions finished successfully.

    :CaseLevel: Integration
    """
    cr_name = gen_string('alpha')
    new_cr_name = gen_string('alpha')
    description = gen_string('alpha')
    display_type = choice(('VNC', 'VMRC'))
    vnc_console_passwords = choice((False, True))
    enable_caching = choice((False, True))
    new_org = entities.Organization().create()
    new_loc = entities.Location().create()
    with session:
        session.computeresource.create({
            'name': cr_name,
            'description': description,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'provider_content.vcenter': module_vmware_settings['vcenter'],
            'provider_content.user': module_vmware_settings['user'],
            'provider_content.password': module_vmware_settings['password'],
            'provider_content.datacenter.value': module_vmware_settings['datacenter'],
            'provider_content.display_type': display_type,
            'provider_content.vnc_console_passwords': vnc_console_passwords,
            'provider_content.enable_caching': enable_caching,
            'organizations.resources.assigned': [module_org.name],
            'locations.resources.assigned': [module_loc.name],
        })
        cr_values = session.computeresource.read(cr_name)
        assert cr_values['name'] == cr_name
        assert cr_values['description'] == description
        assert cr_values['provider'] == FOREMAN_PROVIDERS['vmware']
        assert cr_values['provider_content']['user'] == module_vmware_settings['user']
        assert (cr_values['provider_content']['datacenter']['value']
                == module_vmware_settings['datacenter'])
        assert cr_values['provider_content']['display_type'] == display_type
        assert cr_values['provider_content']['vnc_console_passwords'] == vnc_console_passwords
        assert cr_values['provider_content']['enable_caching'] == enable_caching
        assert cr_values['organizations']['resources']['assigned'] == [module_org.name]
        assert cr_values['locations']['resources']['assigned'] == [module_loc.name]
        session.computeresource.edit(cr_name, {
            'name': new_cr_name,
            'organizations.resources.assigned': [new_org.name],
            'locations.resources.assigned': [new_loc.name],
        })
        assert not session.computeresource.search(cr_name)
        cr_values = session.computeresource.read(new_cr_name)
        assert cr_values['name'] == new_cr_name
        assert (set(cr_values['organizations']['resources']['assigned'])
                == {module_org.name, new_org.name})
        assert (set(cr_values['locations']['resources']['assigned'])
                == {module_loc.name, new_loc.name})
        # check that the compute resource is listed in one of the default compute profiles
        profile_cr_values = session.computeprofile.list_resources(COMPUTE_PROFILE_LARGE)
        profile_cr_names = [cr['Compute Resource'] for cr in profile_cr_values]
        assert '{0} ({1})'.format(new_cr_name, FOREMAN_PROVIDERS['vmware']) in profile_cr_names
        session.computeresource.delete(new_cr_name)
        assert not session.computeresource.search(new_cr_name)


@tier2
def test_positive_retrieve_virtual_machine_list(session, module_vmware_settings):
    """List the virtual machine list from vmware compute resource

    :id: 21ade57a-0caa-4144-9c46-c8e22f33414e

    :setup: vmware hostname and credentials.

    :steps:

        1. Select the created compute resource.
        2. Go to "Virtual Machines" tab.

    :expectedresults: The Virtual machines should be displayed

    :CaseLevel: Integration
    """
    cr_name = gen_string('alpha')
    vm_name = module_vmware_settings['vm_name']
    with session:
        session.computeresource.create({
            'name': cr_name,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'provider_content.vcenter': module_vmware_settings['vcenter'],
            'provider_content.user': module_vmware_settings['user'],
            'provider_content.password': module_vmware_settings['password'],
            'provider_content.datacenter.value': module_vmware_settings['datacenter'],
        })
        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        assert (session.computeresource.search_virtual_machine(cr_name, vm_name)[0]['Name']
                == vm_name)


@tier2
def test_positive_image_end_to_end(session, module_vmware_settings):
    """Perform end to end testing for compute resource VMware component image.

    :id: 6b7949ef-c684-40aa-b181-11f8d4cd39c6

    :expectedresults: All expected CRUD actions finished successfully.

    :CaseLevel: Integration
    """
    cr_name = gen_string('alpha')
    image_name = gen_string('alpha')
    new_image_name = gen_string('alpha')
    check_create_os_with_title(module_vmware_settings['image_os'])
    image_user_data = choice((False, True))
    with session:
        session.computeresource.create({
            'name': cr_name,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'provider_content.vcenter': module_vmware_settings['vcenter'],
            'provider_content.user': module_vmware_settings['user'],
            'provider_content.password': module_vmware_settings['password'],
            'provider_content.datacenter.value': module_vmware_settings['datacenter'],
        })
        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        session.computeresource.create_image(
            cr_name,
            dict(
                name=image_name,
                operating_system=module_vmware_settings['image_os'],
                architecture=module_vmware_settings['image_arch'],
                username=module_vmware_settings['image_username'],
                user_data=image_user_data,
                password=module_vmware_settings['image_password'],
                image=module_vmware_settings['image_name'],
            )
        )
        values = session.computeresource.read_image(cr_name, image_name)
        assert values['name'] == image_name
        assert values['operating_system'] == module_vmware_settings['image_os']
        assert values['architecture'] == module_vmware_settings['image_arch']
        assert values['username'] == module_vmware_settings['image_username']
        assert values['user_data'] == image_user_data
        assert values['image'] == module_vmware_settings['image_name']
        session.computeresource.update_image(cr_name, image_name, dict(name=new_image_name))
        assert session.computeresource.search_images(cr_name, image_name)[0]['Name'] != image_name
        assert (session.computeresource.search_images(cr_name, new_image_name)[0]['Name']
                == new_image_name)
        session.computeresource.delete_image(cr_name, new_image_name)
        assert (session.computeresource.search_images(cr_name, new_image_name)[0]['Name']
                != new_image_name)


@tier2
@run_in_one_thread
def test_positive_resource_vm_power_management(session,  module_vmware_settings):
    """Read current VMware Compute Resource virtual machine power status and
    change it to opposite one

    :id: faeabe45-5112-43a6-bde9-f869dfb26cf5

    :expectedresults: virtual machine is powered on or powered off depending on its initial state

    :CaseLevel: Integration
    """
    cr_name = gen_string('alpha')
    vm_name = module_vmware_settings['vm_name']
    with session:
        session.computeresource.create({
            'name': cr_name,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'provider_content.vcenter': module_vmware_settings['vcenter'],
            'provider_content.user': module_vmware_settings['user'],
            'provider_content.password': module_vmware_settings['password'],
            'provider_content.datacenter.value': module_vmware_settings['datacenter'],
        })
        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        power_status = session.computeresource.vm_status(cr_name, vm_name)
        if power_status:
            session.computeresource.vm_poweroff(cr_name, vm_name)
        else:
            session.computeresource.vm_poweron(cr_name, vm_name)
        assert session.computeresource.vm_status(cr_name, vm_name) is not power_status


@tier2
def test_positive_select_vmware_custom_profile_guest_os_rhel7(session,  module_vmware_settings):
    """Select custom default (3-Large) compute profile guest OS RHEL7.

    :id: 24f7bb5f-2aaf-48cb-9a56-d2d0713dfe3d

    :customerscenario: true

    :setup: vmware hostname and credentials.

    :steps:

        1. Create a compute resource of type vmware.
        2. Provide valid hostname, username and password.
        3. Select the created vmware CR.
        4. Click Compute Profile tab.
        5. Select 3-Large profile
        6. Set Guest OS field to RHEL7 OS.

    :expectedresults: Guest OS RHEL7 is selected successfully.

    :BZ: 1315277

    :CaseLevel: Integration
    """
    cr_name = gen_string('alpha')
    guest_os_name = 'Red Hat Enterprise Linux 7 (64-bit)'
    with session:
        session.computeresource.create({
            'name': cr_name,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'provider_content.vcenter': module_vmware_settings['vcenter'],
            'provider_content.user': module_vmware_settings['user'],
            'provider_content.password': module_vmware_settings['password'],
            'provider_content.datacenter.value': module_vmware_settings['datacenter'],
        })
        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        session.computeresource.update_computeprofile(
            cr_name,
            COMPUTE_PROFILE_LARGE,
            {'provider_content.guest_os': guest_os_name}
        )
        values = session.computeresource.read_computeprofile(cr_name, COMPUTE_PROFILE_LARGE)
        assert values['provider_content']['guest_os'] == guest_os_name


@tier2
def test_positive_access_vmware_with_custom_profile(session,  module_vmware_settings):
    """Associate custom default (3-Large) compute profile

    :id: 751ef765-5091-4322-a0d9-0c9c73009cc4

    :setup: vmware hostname and credentials.

    :steps:

        1. Create a compute resource of type vmware.
        2. Provide valid hostname, username and password.
        3. Select the created vmware CR.
        4. Click Compute Profile tab.
        5. Edit (3-Large) with valid configurations and submit.

    :expectedresults: The Compute Resource created and associated to compute profile (3-Large)
        with provided values.

    :CaseLevel: Integration
    """
    cr_name = gen_string('alpha')
    data_store_summary_string = _get_vmware_datastore_summary_string()
    cr_profile_data = dict(
        cpus='2',
        cores_per_socket='2',
        memory='1024',
        firmware='EFI',
        cluster=VMWARE_CONSTANTS.get('cluster'),
        resource_pool=VMWARE_CONSTANTS.get('pool'),
        folder=VMWARE_CONSTANTS.get('folder'),
        guest_os=VMWARE_CONSTANTS.get('guest_os'),
        virtual_hw_version=VMWARE_CONSTANTS.get('virtualhw_version'),
        memory_hot_add=True,
        cpu_hot_add=True,
        cdrom_drive=True,
        annotation_notes=gen_string('alpha'),
        network_interfaces=[
            dict(nic_type=VMWARE_CONSTANTS.get('network_interface_name'),
                 network=module_vmware_settings['current_interface']),
            dict(nic_type=VMWARE_CONSTANTS.get('network_interface_name'),
                 network=module_vmware_settings['current_interface']),
        ],
        storage=[
            dict(
                controller=VMWARE_CONSTANTS.get('scsicontroller'),
                disks=[
                    dict(
                        data_store=data_store_summary_string,
                        size='10 GB',
                        thin_provision=True,
                        eager_zero=True,
                    ),
                    dict(
                        data_store=data_store_summary_string,
                        size='20 GB',
                        thin_provision=False,
                        eager_zero=False,
                    ),
                ],
            ),
            dict(
                controller=VMWARE_CONSTANTS.get('scsicontroller'),
                disks=[
                    dict(
                        data_store=data_store_summary_string,
                        size='30 GB',
                        thin_provision=False,
                        eager_zero=True,
                    ),
                ],
            ),
        ],
    )
    with session:
        session.computeresource.create({
            'name': cr_name,
            'provider': FOREMAN_PROVIDERS['vmware'],
            'provider_content.vcenter': module_vmware_settings['vcenter'],
            'provider_content.user': module_vmware_settings['user'],
            'provider_content.password': module_vmware_settings['password'],
            'provider_content.datacenter.value': module_vmware_settings['datacenter'],
        })
        assert session.computeresource.search(cr_name)[0]['Name'] == cr_name
        session.computeresource.update_computeprofile(
            cr_name,
            COMPUTE_PROFILE_LARGE,
            {'provider_content.{0}'.format(key): value for key, value in cr_profile_data.items()}
        )
        values = session.computeresource.read_computeprofile(cr_name, COMPUTE_PROFILE_LARGE)
        provider_content = values['provider_content']
        # assert main compute resource profile data updated successfully.
        excluded_keys = ['network_interfaces', 'storage']
        expected_value = {key: value for key, value in cr_profile_data.items()
                          if key not in excluded_keys}
        provided_value = {key: value for key, value in provider_content.items()
                          if key in expected_value}
        assert provided_value == expected_value
        # assert compute resource profile network data updated successfully.
        for network_index, expected_network_value in enumerate(
                cr_profile_data['network_interfaces']):
            provided_network_value = {
                    key: value
                    for key, value in provider_content['network_interfaces'][network_index].items()
                    if key in expected_network_value
            }
            assert provided_network_value == expected_network_value
        # assert compute resource profile storage data updated successfully.
        for controller_index, expected_controller_value in enumerate(cr_profile_data['storage']):
            provided_controller_value = provider_content['storage'][controller_index]
            assert (provided_controller_value['controller']
                    == expected_controller_value['controller'])
            for disk_index, expected_disk_value in enumerate(expected_controller_value['disks']):
                provided_disk_value = {
                        key: value
                        for key, value in provided_controller_value['disks'][disk_index].items()
                        if key in expected_disk_value
                }
                assert provided_disk_value == expected_disk_value
