"""Test class for Puppet Environment UI

:Requirement: Environment

:CaseAutomation: Automated

:CaseComponent: Puppet

:Team: Rocket

:CaseImportance: Low

"""

import pytest

from robottelo.constants import DEFAULT_CV, ENVIRONMENT
from robottelo.utils.datafactory import gen_string


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_end_to_end(session_puppet_enabled_sat, module_puppet_org, module_puppet_loc):
    """Perform end to end testing for puppet environment component

    :id: 2ef32b2d-acdd-4cb1-a760-da4fd1166167

    :expectedresults: All expected CRUD actions finished successfully

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    with session_puppet_enabled_sat.ui_session() as session:
        session.puppetenvironment.create(
            {
                'environment.name': name,
                'locations.resources.assigned': [module_puppet_loc.name],
                'organizations.resources.assigned': [module_puppet_org.name],
            }
        )
        found_envs = session.puppetenvironment.search(name)
        assert name in [env['Name'] for env in found_envs]
        env_values = session.puppetenvironment.read(name)
        assert env_values['environment']['name'] == name
        assert module_puppet_org.name in env_values['organizations']['resources']['assigned']
        assert module_puppet_loc.name in env_values['locations']['resources']['assigned']
        session.puppetenvironment.update(name, {'environment.name': new_name})
        found_envs = session.puppetenvironment.search(new_name)
        assert new_name in [env['Name'] for env in found_envs]
        session.puppetenvironment.delete(new_name)
        assert not session.puppetenvironment.search(new_name)


@pytest.mark.tier2
def test_positive_availability_for_host_and_hostgroup_in_multiple_orgs(
    session_puppet_enabled_sat, module_puppet_loc
):
    """An environment that is present in different organizations should be
    visible for any created host and hostgroup in those organizations

    :id: badcfdd8-48a2-4abf-bef0-d4ff5c0f4c87

    :customerscenario: true

    :expectedresults: Environment can be used for any new host and any
        organization where it is present in

    :BZ: 543178

    :CaseImportance: High
    """
    env_name = gen_string('alpha')
    orgs = [session_puppet_enabled_sat.api.Organization().create() for _ in range(2)]
    with session_puppet_enabled_sat.ui_session() as session:
        session.puppetenvironment.create(
            {
                'environment.name': env_name,
                'locations.resources.assigned': [module_puppet_loc.name],
                'organizations.resources.assigned': [org.name for org in orgs],
            }
        )
        session.location.select(loc_name=module_puppet_loc.name)
        for org in orgs:
            session.organization.select(org_name=org.name)
            assert session.puppetenvironment.search(env_name)[0]['Name'] == env_name
            host = session_puppet_enabled_sat.api.Host(location=module_puppet_loc, organization=org)
            host.create_missing()
            os_name = f'{host.operatingsystem.name} {host.operatingsystem.major}'
            session.host.create(
                {
                    'host.name': host.name,
                    'host.organization': org.name,
                    'host.location': module_puppet_loc.name,
                    'host.lce': ENVIRONMENT,
                    'host.content_view': DEFAULT_CV,
                    'host.puppet_environment': env_name,
                    'operating_system.architecture': host.architecture.name,
                    'operating_system.operating_system': os_name,
                    'operating_system.media_type': 'All Media',
                    'operating_system.media': host.medium.name,
                    'operating_system.ptable': host.ptable.name,
                    'operating_system.root_password': host.root_pass,
                    'interfaces.interface.interface_type': 'Interface',
                    'interfaces.interface.device_identifier': gen_string('alpha'),
                    'interfaces.interface.mac': host.mac,
                    'interfaces.interface.domain': host.domain.name,
                    'interfaces.interface.primary': True,
                }
            )
            host_name = f'{host.name}.{host.domain.name}'
            values = session.host.get_details(host_name, widget_names='properties')
            assert env_name in values['properties']['properties_table']['Puppet Environment']
            assert org.name in values['properties']['properties_table']['Organization']

            host_group_name = gen_string('alpha')
            session.hostgroup.create(
                {'host_group.name': host_group_name, 'host_group.puppet_environment': env_name}
            )
            hostgroup_values = session.hostgroup.read(
                host_group_name, widget_names=['host_group', 'organizations']
            )
            assert hostgroup_values['host_group']['name'] == host_group_name
            assert org.name in hostgroup_values['organizations']['resources']['assigned']
            assert hostgroup_values['host_group']['puppet_environment'] == env_name
