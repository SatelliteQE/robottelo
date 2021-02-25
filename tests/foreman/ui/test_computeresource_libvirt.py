"""Test for Compute Resource UI

:Requirement: Computeresource Libvirt

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-libvirt

:Assignee: lhellebr

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import COMPUTE_PROFILE_SMALL
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import LIBVIRT_RESOURCE_URL
from robottelo.decorators import setting_is_set

if not setting_is_set('compute_resources'):
    pytest.skip(
        'skipping tests due to missing compute_resources settings', allow_module_level=True
    )


@pytest.fixture(scope='module')
def module_libvirt_url():
    return LIBVIRT_RESOURCE_URL % settings.compute_resources.libvirt_hostname


@pytest.mark.on_premises_provisioning
@pytest.mark.tier2
def test_positive_end_to_end(session, module_org, module_loc, module_libvirt_url):
    """Perform end to end testing for compute resource Libvirt component.

    :id: 4f4650c8-32f3-4dab-b3bf-9c54d0cda3b2

    :expectedresults: All expected CRUD actions finished successfully.

    :CaseLevel: Integration

    :CaseImportance: High

    :BZ: 1662164
    """
    cr_name = gen_string('alpha')
    cr_description = gen_string('alpha')
    new_cr_name = gen_string('alpha')
    new_cr_description = gen_string('alpha')
    new_org = entities.Organization().create()
    new_loc = entities.Location().create()
    display_type = choice(('VNC', 'SPICE'))
    console_passwords = choice((True, False))
    with session:
        session.computeresource.create(
            {
                'name': cr_name,
                'description': cr_description,
                'provider': FOREMAN_PROVIDERS['libvirt'],
                'provider_content.url': module_libvirt_url,
                'provider_content.display_type': display_type,
                'provider_content.console_passwords': console_passwords,
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_loc.name],
            }
        )
        cr_values = session.computeresource.read(cr_name)
        assert cr_values['name'] == cr_name
        assert cr_values['description'] == cr_description
        assert cr_values['provider_content']['url'] == module_libvirt_url
        assert cr_values['provider_content']['display_type'] == display_type
        assert cr_values['provider_content']['console_passwords'] == console_passwords
        assert cr_values['organizations']['resources']['assigned'] == [module_org.name]
        assert cr_values['locations']['resources']['assigned'] == [module_loc.name]
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
            module_loc.name,
            new_loc.name,
        }
        # check that the compute resource is listed in one of the default compute profiles
        profile_cr_values = session.computeprofile.list_resources(COMPUTE_PROFILE_SMALL)
        profile_cr_names = [cr['Compute Resource'] for cr in profile_cr_values]
        assert '{} ({})'.format(new_cr_name, FOREMAN_PROVIDERS['libvirt']) in profile_cr_names
        session.computeresource.update_computeprofile(
            new_cr_name,
            COMPUTE_PROFILE_SMALL,
            {'provider_content.cpus': '16', 'provider_content.memory': '8 GB'},
        )
        cr_profile_values = session.computeresource.read_computeprofile(
            new_cr_name, COMPUTE_PROFILE_SMALL
        )
        assert cr_profile_values['compute_profile'] == COMPUTE_PROFILE_SMALL
        assert cr_profile_values['compute_resource'] == '{} ({})'.format(
            new_cr_name, FOREMAN_PROVIDERS['libvirt']
        )
        assert cr_profile_values['provider_content']['cpus'] == '16'
        assert cr_profile_values['provider_content']['memory'] == '8 GB'
        session.computeresource.delete(new_cr_name)
        assert not session.computeresource.search(new_cr_name)
