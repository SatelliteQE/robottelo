# -*- encoding: utf-8 -*-
"""Test class for Puppet Environment UI

:Requirement: Environment

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: Low

:Upstream: No
"""
from nailgun import entities

from robottelo.constants import DEFAULT_CV, ENVIRONMENT
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2, upgrade


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


@upgrade
@tier2
def test_positive_end_to_end(session, module_org, module_loc):
    """Perform end to end testing for puppet environment component

    :id: 2ef32b2d-acdd-4cb1-a760-da4fd1166167

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    with session:
        session.puppetenvironment.create({
            'environment.name': name,
            'locations.resources.assigned': [module_loc.name],
            'organizations.resources.assigned': [module_org.name],
        })
        assert session.puppetenvironment.search(name)[0]['Name'] == name
        env_values = session.puppetenvironment.read(name)
        assert env_values['environment']['name'] == name
        assert env_values['organizations']['resources']['assigned'][0] == module_org.name
        assert env_values['locations']['resources']['assigned'][0] == module_loc.name
        session.puppetenvironment.update(name, {'environment.name': new_name})
        assert session.puppetenvironment.search(new_name)[0]['Name'] == new_name
        session.puppetenvironment.delete(new_name)
        assert not session.puppetenvironment.search(new_name)


@tier2
def test_positive_availability_for_host_in_multiple_orgs(session, module_loc):
    """New environment that present in different organizations should be
    visible for any created host in these organizations

    :id: badcfdd8-48a2-4abf-bef0-d4ff5c0f4c87

    :customerscenario: true

    :expectedresults: Environment can be used for any new host and any
        organization where it is present in

    :BZ: 543178

    :CaseLevel: Integration

    :CaseImportance: High
    """
    env_name = gen_string('alpha')
    orgs = [entities.Organization().create() for _ in range(2)]
    with session:
        session.puppetenvironment.create({
            'environment.name': env_name,
            'locations.resources.assigned': [module_loc.name],
            'organizations.resources.assigned': [org.name for org in orgs],
        })
        for org in orgs:
            session.organization.select(org_name=org.name)
            assert session.puppetenvironment.search(env_name)[0]['Name'] == env_name
            host = entities.Host(location=module_loc, organization=org)
            host.create_missing()
            os_name = u'{0} {1}'.format(
                host.operatingsystem.name, host.operatingsystem.major)
            session.host.create({
                'host.name': host.name,
                'host.organization': org.name,
                'host.location': module_loc.name,
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
            })
            host_name = u'{0}.{1}'.format(host.name, host.domain.name)
            assert session.host.search(host_name)[0]['Name'] == host_name
            values = session.host.get_details(host_name)
            assert values['properties']['properties_table']['Puppet Environment'] == env_name
            assert values['properties']['properties_table']['Organization'] == org.name


@tier2
def test_positive_availability_for_hostgroup_in_multiple_orgs(session, module_loc):
    """New environment that present in different organizations should be
    visible for any created hostgroup in these organizations

    :id: 07ff316e-16c2-493e-a987-73d59f8e81c7

    :customerscenario: true

    :expectedresults: Environment can be used for any new hostgroup and any
        organization where it is present in

    :BZ: 543178

    :CaseLevel: Integration

    :CaseImportance: High
    """
    env_name = gen_string('alpha')
    orgs_names = [entities.Organization().create().name for _ in range(2)]
    with session:
        session.puppetenvironment.create({
            'environment.name': env_name,
            'locations.resources.assigned': [module_loc.name],
            'organizations.resources.assigned': orgs_names,
        })
        for org in orgs_names:
            host_group_name = gen_string('alpha')
            session.organization.select(org_name=org)
            assert session.puppetenvironment.search(env_name)[0]['Name'] == env_name
            session.hostgroup.create({
                'host_group.name': host_group_name,
                'host_group.puppet_environment': env_name,
            })
            assert session.hostgroup.search(host_group_name)[0]['Name'] == host_group_name
            hostgroup_values = session.hostgroup.read(host_group_name)
            assert hostgroup_values['host_group']['name'] == host_group_name
            assert org in hostgroup_values['organizations']['resources']['assigned']
            assert hostgroup_values['host_group']['puppet_environment'] == env_name
