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
from robottelo.utils.issue_handlers import is_open

pytestmark = [pytest.mark.skip_if_not_set('libvirt')]

LIBVIRT_URL = LIBVIRT_RESOURCE_URL % settings.libvirt.libvirt_hostname


@pytest.mark.tier2
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


@pytest.mark.on_premises_provisioning
@pytest.mark.tier4
@pytest.mark.rhel_ver_match('[^6]')
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
def test_positive_provision_end_to_end(
    request,
    session,
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

    :parametrized: yes
    """
    sat = module_libvirt_provisioning_sat.sat
    hostname = gen_string('alpha').lower()
    os_major_ver = module_provisioning_rhel_content.os.major
    cpu_mode = 'host-passthrough' if is_open('BZ:2236693') and os_major_ver == '9' else 'default'
    cr = sat.api.LibvirtComputeResource(
        provider=FOREMAN_PROVIDERS['libvirt'],
        url=LIBVIRT_URL,
        display_type='VNC',
        location=[module_location],
        organization=[module_sca_manifest_org],
    ).create()
    with session:
        session.host.create(
            {
                'host.name': hostname,
                'host.organization': module_sca_manifest_org.name,
                'host.location': module_location.name,
                'host.hostgroup': provisioning_hostgroup.name,
                'host.inherit_deploy_option': False,
                'host.deploy': f'{cr.name} (Libvirt)',
                'provider_content.virtual_machine.memory': '6144',
                'provider_content.virtual_machine.cpu_mode': cpu_mode,
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
            lambda: session.host.get_details(name)['properties']['properties_table']['Build']
            != 'Pending installation clear',
            timeout=1800,
            delay=30,
            fail_func=session.browser.refresh,
            silent_failure=True,
            handle_exception=True,
        )
        assert (
            session.host.get_details(name)['properties']['properties_table']['Build']
            == 'Installed clear'
        )
        session.host.delete(name)
        assert not sat.api.Host().search(query={'search': f'name="{name}"'})
