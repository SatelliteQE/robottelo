"""Test class for Puppet Environment UI

:Requirement: Environment

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: Low

:Upstream: No
"""
import pytest

from robottelo.constants import DEFAULT_CV
from robottelo.constants import ENVIRONMENT
from robottelo.datafactory import gen_string


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_end_to_end(session, module_org, module_location):
    """Perform end to end testing for puppet environment component

    :id: 2ef32b2d-acdd-4cb1-a760-da4fd1166167

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    with session:
        session.puppetenvironment.create(
            {
                'environment.name': name,
                'locations.resources.assigned': [module_location.name],
                'organizations.resources.assigned': [module_org.name],
            }
        )
        found_envs = session.puppetenvironment.search(name)
        assert name in [env['Name'] for env in found_envs]
        env_values = session.puppetenvironment.read(name)
        assert env_values['environment']['name'] == name
        assert env_values['organizations']['resources']['assigned'][0] == module_org.name
        assert env_values['locations']['resources']['assigned'][0] == module_location.name
        session.puppetenvironment.update(name, {'environment.name': new_name})
        found_envs = session.puppetenvironment.search(new_name)
        assert new_name in [env['Name'] for env in found_envs]
        session.puppetenvironment.delete(new_name)
        assert not session.puppetenvironment.search(new_name)


@pytest.mark.tier2
def test_positive_availability_for_host_and_hostgroup_in_multiple_orgs(
    session, default_sat, module_location
):
    """An environment that is present in different organizations should be
    visible for any created host and hostgroup in those organizations

    :id: badcfdd8-48a2-4abf-bef0-d4ff5c0f4c87

    :customerscenario: true

    :expectedresults: Environment can be used for any new host and any
        organization where it is present in

    :BZ: 543178

    :CaseLevel: Integration

    :CaseImportance: High
    """
    env_name = gen_string('alpha')
    orgs = [default_sat.api.Organization().create() for _ in range(2)]
    with session:
        session.puppetenvironment.create(
            {
                'environment.name': env_name,
                'locations.resources.assigned': [module_location.name],
                'organizations.resources.assigned': [org.name for org in orgs],
            }
        )
        for org in orgs:
            session.organization.select(org_name=org.name)
            assert session.puppetenvironment.search(env_name)[0]['Name'] == env_name
            host = default_sat.api.Host(location=module_location, organization=org)
            host.create_missing()
            os_name = f'{host.operatingsystem.name} {host.operatingsystem.major}'
            session.host.create(
                {
                    'host.name': host.name,
                    'host.organization': org.name,
                    'host.location': module_location.name,
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
            assert values['properties']['properties_table']['Puppet Environment'] == env_name
            assert values['properties']['properties_table']['Organization'] == org.name

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
