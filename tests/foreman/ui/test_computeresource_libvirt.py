"""Test for Compute Resource UI

:Requirement: Computeresource Libvirt

:CaseAutomation: Automated

:CaseComponent: ComputeResources-libvirt

:Team: Rocket

:CaseImportance: High

"""

from random import choice

from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import (
    COMPUTE_PROFILE_SMALL,
    FOREMAN_PROVIDERS,
    LIBVIRT_RESOURCE_URL,
)
from robottelo.hosts import ContentHost

pytestmark = [pytest.mark.skip_if_not_set('libvirt')]

LIBVIRT_URL = LIBVIRT_RESOURCE_URL % settings.libvirt.libvirt_hostname


@pytest.mark.e2e
def test_positive_end_to_end(session, module_target_sat, module_org, module_location):
    """Perform end to end testing for compute resource Libvirt component.

    :id: 7ef925ac-5aec-4e9d-b786-328a9b219c01

    :expectedresults: All expected CRUD actions finished successfully.

    :CaseImportance: High

    :BZ: 1662164
    """
    cr_name = gen_string('alpha')
    cr_description = gen_string('alpha')
    new_cr_name = gen_string('alpha')
    new_cr_description = gen_string('alpha')
    new_org = module_target_sat.api.Organization().create()
    new_loc = module_target_sat.api.Location().create()
    display_type = choice(('VNC', 'SPICE'))
    console_passwords = choice((True, False))
    module_target_sat.configure_libvirt_cr()
    with session:
        session.computeresource.create(
            {
                'name': cr_name,
                'description': cr_description,
                'provider': FOREMAN_PROVIDERS['libvirt'],
                'provider_content.url': LIBVIRT_URL,
                'provider_content.display_type': display_type,
                'provider_content.console_passwords': console_passwords,
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_location.name],
            }
        )
        cr_values = session.computeresource.read(cr_name)
        assert cr_values['name'] == cr_name
        assert cr_values['description'] == cr_description
        assert cr_values['provider_content']['url'] == LIBVIRT_URL
        assert cr_values['provider_content']['display_type'] == display_type
        assert cr_values['provider_content']['console_passwords'] == console_passwords
        assert cr_values['organizations']['resources']['assigned'] == [module_org.name]
        assert cr_values['locations']['resources']['assigned'] == [module_location.name]
        session.computeresource.edit(
            cr_name,
            {
                'name': new_cr_name,
                'description': new_cr_description,
                'organizations.resources.assigned': [new_org.name],
                'locations.resources.assigned': [new_loc.name],
            },
        )
        assert not session.computeresource.search(cr_name)
        cr_values = session.computeresource.read(new_cr_name)
        assert cr_values['name'] == new_cr_name
        assert cr_values['description'] == new_cr_description
        assert set(cr_values['organizations']['resources']['assigned']) == {
            module_org.name,
            new_org.name,
        }
        assert set(cr_values['locations']['resources']['assigned']) == {
            module_location.name,
            new_loc.name,
        }
        # check that the compute resource is listed in one of the default compute profiles
        profile_cr_values = session.computeprofile.list_resources(COMPUTE_PROFILE_SMALL)
        profile_cr_names = [cr['Compute Resource'] for cr in profile_cr_values]
        assert f'{new_cr_name} ({FOREMAN_PROVIDERS["libvirt"]})' in profile_cr_names
        session.computeresource.update_computeprofile(
            new_cr_name,
            COMPUTE_PROFILE_SMALL,
            {'provider_content.cpus': '16', 'provider_content.memory': '8192'},
        )
        cr_profile_values = session.computeresource.read_computeprofile(
            new_cr_name, COMPUTE_PROFILE_SMALL
        )
        assert cr_profile_values['compute_profile'] == COMPUTE_PROFILE_SMALL
        assert (
            cr_profile_values['compute_resource']
            == f'{new_cr_name} ({FOREMAN_PROVIDERS["libvirt"]})'
        )
        assert cr_profile_values['provider_content']['cpus'] == '16'
        assert cr_profile_values['provider_content']['memory'] == '8192 MB'
        session.computeresource.delete(new_cr_name)
        assert not session.computeresource.search(new_cr_name)


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.rhel_ver_match('[8]')
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
@pytest.mark.parametrize('pxe_loader', ['uefi', 'secureboot'], indirect=True)
def test_positive_provision_end_to_end(
    request,
    pxe_loader,
    setting_update,
    module_sca_manifest_org,
    module_location,
    provisioning_hostgroup,
    module_libvirt_provisioning_sat,
    module_provisioning_rhel_content,
):
    """Provision Host on libvirt compute resource, and delete it afterwards

    :id: 2678f95f-0c0e-4b46-a3c1-3f9a954d3bde

    :expectedresults: Host is provisioned successfully

    :customerscenario: true

    :BZ: 1243223, 2236693

    :Verifies: SAT-22491, SAT-25808

    :parametrized: yes
    """
    sat = module_libvirt_provisioning_sat.sat
    hostname = gen_string('alpha').lower()
    cr = sat.api.LibvirtComputeResource(
        provider=FOREMAN_PROVIDERS['libvirt'],
        url=LIBVIRT_URL,
        display_type='VNC',
        location=[module_location],
        organization=[module_sca_manifest_org],
    ).create()

    existing_params = provisioning_hostgroup.group_parameters_attributes
    provisioning_hostgroup.group_parameters_attributes = [
        {'name': 'remote_execution_connect_by_ip', 'value': 'true', 'parameter_type': 'boolean'},
    ] + existing_params
    provisioning_hostgroup.update(['group_parameters_attributes'])

    with sat.ui_session() as session:
        session.organization.select(module_sca_manifest_org.name)
        session.location.select(module_location.name)
        session.host.create(
            {
                'host.name': hostname,
                'host.organization': module_sca_manifest_org.name,
                'host.location': module_location.name,
                'host.hostgroup': provisioning_hostgroup.name,
                'host.inherit_deploy_option': False,
                'host.deploy': f'{cr.name} (Libvirt)',
                'provider_content.virtual_machine.memory': '6144',
                'interfaces.interface.network_type': 'Physical (Bridge)',
                'interfaces.interface.network': f'br-{settings.provisioning.vlan_id}',
                'additional_information.comment': 'Libvirt provision using valid data',
            }
        )
        name = f'{hostname}.{module_libvirt_provisioning_sat.domain.name}'
        request.addfinalizer(lambda: sat.provisioning_cleanup(name))
        assert session.host.search(name)[0]['Name'] == name

        # Check on Libvirt, if VM exists
        result = sat.execute(
            f'su foreman -s /bin/bash -c "virsh -c {LIBVIRT_URL} list --state-running"'
        )
        assert hostname in result.stdout
        # Wait for provisioning to complete and report status back to Satellite
        wait_for(
            lambda: session.host_new.get_host_statuses(name)['Build']['Status']
            != 'Pending installation',
            timeout=1800,
            delay=30,
            fail_func=session.browser.refresh,
            silent_failure=True,
            handle_exception=True,
        )
        values = session.host_new.get_host_statuses(name)
        assert values['Build']['Status'] == 'Installed'

        # Verify SecureBoot is enabled on host after provisioning is completed successfully
        if pxe_loader.vm_firmware == 'uefi_secure_boot':
            host = sat.api.Host().search(query={'host': hostname})[0].read()
            provisioning_host = ContentHost(host.ip)
            # Wait for the host to be rebooted and SSH daemon to be started.
            provisioning_host.wait_for_connection()
            assert 'SecureBoot enabled' in provisioning_host.execute('mokutil --sb-state').stdout

        session.host.delete(name)
        assert not sat.api.Host().search(query={'search': f'name="{name}"'})


@pytest.mark.stubbed
def test_positive_image_end_to_end():
    """Perform end to end testing for compute resource libvirt component image.

    :id: 62a5c52f-dd15-45e7-8200-c64bb335474f

    :expectedresults: All expected CRUD actions finished successfully.

    :CaseImportance: High

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_associate_with_custom_profile():
    """Associate custom default (3-Large) compute profile to libvirt compute resource.

    :id: e7698154-62ff-492b-8e56-c5dc70f0c9df

    :steps:
        1. Create a compute resource of type libvirt.
        2. Select the created libvirt CR.
        3. Click Compute Profile tab.
        4. Edit (3-Large) with valid configurations and submit.

    :expectedresults: The Compute Resource created and associated to compute profile (3-Large)
        with provided values.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_associate_with_custom_profile_with_template():
    """Associate custom default (3-Large) compute profile to libvirt compute
     resource, with template

    :id: bb9794cc-6335-4621-92fd-fdc815f23263

    :steps:
        1. Create a compute resource of type libvirt.
        2 Select the created rhev CR.
        3. Click Compute Profile tab.
        4. Edit (3-Large) with valid configuration and template and submit.

    :expectedresults: The Compute Resource created and opened successfully

    :CaseImportance: Medium

    :CaseAutomation: NotAutomated
    """
