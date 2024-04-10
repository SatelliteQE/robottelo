"""Test for Compute Resource UI

:Requirement: Computeresource Libvirt

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-libvirt

:Team: Rocket

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

import pytest
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.constants import COMPUTE_PROFILE_SMALL
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import LIBVIRT_RESOURCE_URL

pytestmark = [pytest.mark.skip_if_not_set('libvirt')]

LIBVIRT_URL = LIBVIRT_RESOURCE_URL % settings.libvirt.libvirt_hostname


@pytest.mark.tier2
@pytest.mark.e2e
def test_positive_end_to_end(session, module_target_sat, module_org, module_location):
    """Perform end to end testing for compute resource Libvirt component.

    :id: 7ef925ac-5aec-4e9d-b786-328a9b219c01

    :expectedresults: All expected CRUD actions finished successfully.

    :CaseLevel: Integration

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
