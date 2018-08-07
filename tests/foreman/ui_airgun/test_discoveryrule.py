# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery Rules

:Requirement: Discoveryrule

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from pytest import raises

from airgun.session import Session
from fauxfactory import gen_integer, gen_string
from nailgun import entities

from robottelo.decorators import fixture, stubbed, tier2


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


@fixture(scope='module')
def manager_loc():
    return entities.Location().create()


@fixture
def module_organ():
    return entities.Organization().create()


@fixture
def manager_user(manager_loc, module_loc, module_organ):
    manager_role = entities.Role().search(
        query={'search': 'name="Discovery Manager"'}
    )[0]
    password = gen_string('alphanumeric')
    manager_user = entities.User(
        login=gen_string('alpha'),
        role=[manager_role],
        password=password,
        location=[module_loc, manager_loc],
        organization=[module_organ],
    ).create()
    manager_user.password = password
    yield manager_user


@fixture
def reader_user(module_loc, module_organ):
    password = gen_string('alphanumeric')
    reader_role = entities.Role().search(
        query={'search': 'name="Discovery Reader"'}
    )[0]
    reader_user = entities.User(
        login=gen_string('alpha'),
        role=[reader_role],
        password=password,
        organization=[module_organ],
        location=[module_loc],
    ).create()
    reader_user.password = password
    yield reader_user


def test_positive_create(session, module_organ):
    name = gen_string('alpha')
    search = '{}\t'.format(gen_string('alpha'))
    hg = entities.HostGroup(organization=[module_organ]).create()
    with session:
        session.organization.select(org_name=module_organ.name)
        session.discoveryrule.create({
            'primary.name': name,
            'primary.search': search,
            'primary.host_group': hg.name,
            'primary.hostname': gen_string('alpha'),
            'primary.hosts_limit': str(gen_integer(1, 100)),
            'primary.priority': str(gen_integer(1, 100)),
            'primary.enabled': False,
        })
        dr_val = session.discoveryrule.read_all()
        assert dr_val[0]['Name'] == name


def test_positive_delete(session, module_organ):
    hg = entities.HostGroup(organization=[module_organ]).create()
    dr = entities.DiscoveryRule(hostgroup=hg,
                                organization=[module_organ]).create()
    with session:
        session.organization.select(org_name=module_organ.name)
        session.discoveryrule.delete(dr.name)
        assert not session.discoveryrule.read_all()


def test_positive_update(session, module_loc, module_organ):
    hg = entities.HostGroup(organization=[module_organ]).create()
    dr = entities.DiscoveryRule(hostgroup=hg,
                                organization=[module_organ]).create()
    with session:
        session.organization.select(org_name=module_organ.name)
        session.discoveryrule.update(
            dr.name, {'locations.resources.assigned': [module_loc.name]})
        dr_val = session.discoveryrule.read(dr.name)
        assert (dr_val
                ['locations']['resources']['assigned'][0] == module_loc.name)


def test_positive_disable_and_enable(session, module_organ):
    hg = entities.HostGroup(organization=[module_organ]).create()
    dr = entities.DiscoveryRule(hostgroup=hg,
                                organization=[module_organ]).create()
    with session:
        session.organization.select(org_name=module_organ.name)
        # enable checkbox is true, by default
        session.discoveryrule.disable(dr.name)
        dr_val = session.discoveryrule.read_all()
        assert dr_val[0]['Enabled'] == 'false'
        session.discoveryrule.enable(dr.name)
        dr_val = session.discoveryrule.read_all()
        assert dr_val[0]['Enabled'] == 'true'


def test_positive_associated_hosts(session, module_loc, module_organ):
    host = entities.Host(organization=module_organ,
                         location=module_loc).create()
    hg = entities.HostGroup(organization=[module_organ]).create()
    dr = entities.DiscoveryRule(hostgroup=hg,
                                organization=[module_organ]).create()
    with session:
        session.organization.select(org_name=module_organ.name)
        assoc_hosts = session.discoveryrule.associated_hosts(dr.name,
                                                             host.name)
        assert assoc_hosts[0]['Name'] == host.name


@tier2
def test_positive_create_rule_with_non_admin_user(manager_loc, manager_user,
                                                  module_organ, test_name):
    """Create rule with non-admin user by associating discovery_manager role

    :id: 6a03983b-363d-4646-b277-34af5f5abc55

    :expectedresults: Rule should be created successfully.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    search = '{}\t'.format(gen_string('alpha'))
    hg = entities.HostGroup(organization=[module_organ]).create()
    with Session(
            test_name,
            user=manager_user.login,
            password=manager_user.password
    ) as session:
        session.location.select(loc_name=manager_loc.name)
        session.discoveryrule.create({
            'primary.name': name,
            'primary.search': search,
            'primary.host_group': hg.name,
            'primary.priority': str(gen_integer(1, 100)),
        })
        dr_val = session.discoveryrule.read_all()
        assert dr_val[0]['Name'] == name


@tier2
def test_positive_delete_rule_with_non_admin_user(manager_loc, manager_user,
                                                  module_organ, test_name):
    """Delete rule with non-admin user by associating discovery_manager role

    :id: 7fa56bab-82d7-46c9-a4fa-c44ef173c703

    :expectedresults: Rule should be deleted successfully.

    :CaseLevel: Integration
    """
    hg = entities.HostGroup(organization=[module_organ]).create()
    dr = entities.DiscoveryRule(
        hostgroup=hg,
        organization=[module_organ],
        location=[manager_loc]
    ).create()
    with Session(
            test_name,
            user=manager_user.login,
            password=manager_user.password
    ) as session:
        session.discoveryrule.delete(dr.name)
        assert not session.discoveryrule.read_all()


@tier2
def test_positive_view_existing_rule_with_non_admin_user(module_loc,
                                                         module_organ,
                                                         reader_user,
                                                         test_name):
    """Existing rule should be viewed to non-admin user by associating
    discovery_reader role.

    :id: 0f5b0221-43be-47bc-8619-749824c4e54f

    :Steps:

        1. create a rule with admin user
        2. create a non-admin user and assign 'Discovery Reader' role
        3. Login with non-admin user

    :expectedresults: Rule should be visible to non-admin user.

    :CaseLevel: Integration
    """
    hg = entities.HostGroup(organization=[module_organ]).create()
    dr = entities.DiscoveryRule(
        hostgroup=hg,
        organization=[module_organ],
        location=[module_loc]
    ).create()
    with Session(
            test_name,
            user=reader_user.login,
            password=reader_user.password
    ) as session:
        dr_val = session.discoveryrule.read_all()
        assert dr_val[0]['Name'] == dr.name


@tier2
def test_negative_delete_rule_with_non_admin_user(module_loc, module_organ,
                                                  reader_user, test_name):
    """Delete rule with non-admin user by associating discovery_reader role

    :id: 23a7627c-6a9b-493b-871f-698543adf1d2

    :expectedresults: User should validation error and rule should not be
        deleted successfully.

    :CaseLevel: Integration
    """
    hg = entities.HostGroup(organization=[module_organ]).create()
    dr = entities.DiscoveryRule(
        hostgroup=hg,
        organization=[module_organ],
        location=[module_loc]
    ).create()
    with Session(
            test_name,
            user=reader_user.login,
            password=reader_user.password
    ) as session:
        with raises(ValueError):
            session.discoveryrule.delete(dr.name)
        dr_val = session.discoveryrule.read_all()
        assert dr_val[0]['Name'] == dr.name


@stubbed()
@tier2
def test_positive_list_host_based_on_rule_search_query():
    """List all the discovered hosts resolved by given rule's search query
    e.g. all hosts with cpu_count = 1

    :id: f7473fa2-7349-42d3-9cdb-f74b55d2f440

    :Steps:

        1. discovered a host with cpu_count = 2
        2. Define a rule 'rule1' with search query cpu_count = 2
        3. Click on 'Discovered Hosts' from rule1

    :expectedresults: All hosts based on rule's search query( w/ cpu_count
        = 2) should be listed

    :caseautomation: notautomated

    :CaseLevel: Integration
    """
