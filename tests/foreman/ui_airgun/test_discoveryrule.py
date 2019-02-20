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
from fauxfactory import gen_integer, gen_ipaddr, gen_string
from nailgun import entities

from robottelo.api.utils import create_discovered_host
from robottelo.decorators import fixture, run_in_one_thread, tier2, upgrade


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


@fixture(scope='module')
def manager_loc():
    return entities.Location().create()


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture
def module_discovery_env(module_org, module_loc):
    discovery_loc = entities.Setting().search(
        query={'search': 'name="discovery_location"'})[0]
    default_discovery_loc = discovery_loc.value
    discovery_loc.value = module_loc.name
    discovery_loc.update(['value'])
    discovery_org = entities.Setting().search(
        query={'search': 'name="discovery_organization"'})[0]
    default_discovery_org = discovery_org.value
    discovery_org.value = module_org.name
    discovery_org.update(['value'])
    yield
    discovery_loc.value = default_discovery_loc
    discovery_loc.update(['value'])
    discovery_org.value = default_discovery_org
    discovery_org.update(['value'])


@fixture
def manager_user(manager_loc, module_loc, module_org):
    manager_role = entities.Role().search(
        query={'search': 'name="Discovery Manager"'}
    )[0]
    password = gen_string('alphanumeric')
    manager_user = entities.User(
        login=gen_string('alpha'),
        role=[manager_role],
        password=password,
        location=[module_loc, manager_loc],
        organization=[module_org],
    ).create()
    manager_user.password = password
    return manager_user


@fixture
def reader_user(module_loc, module_org):
    password = gen_string('alphanumeric')
    reader_role = entities.Role().search(
        query={'search': 'name="Discovery Reader"'}
    )[0]
    reader_user = entities.User(
        login=gen_string('alpha'),
        role=[reader_role],
        password=password,
        organization=[module_org],
        location=[module_loc],
    ).create()
    reader_user.password = password
    return reader_user


@tier2
def test_positive_create_rule_with_non_admin_user(manager_loc, manager_user,
                                                  module_org, test_name):
    """Create rule with non-admin user by associating discovery_manager role

    :id: 6a03983b-363d-4646-b277-34af5f5abc55

    :expectedresults: Rule should be created successfully.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    search = gen_string('alpha')
    hg = entities.HostGroup(organization=[module_org]).create()
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
        })
        dr_val = session.discoveryrule.read(name)
        assert dr_val['primary']['name'] == name
        assert dr_val['primary']['host_group'] == hg.name


@tier2
def test_positive_delete_rule_with_non_admin_user(manager_loc, manager_user,
                                                  module_org, test_name):
    """Delete rule with non-admin user by associating discovery_manager role

    :id: 7fa56bab-82d7-46c9-a4fa-c44ef173c703

    :expectedresults: Rule should be deleted successfully.

    :CaseLevel: Integration
    """
    hg = entities.HostGroup(organization=[module_org]).create()
    dr = entities.DiscoveryRule(
        hostgroup=hg,
        organization=[module_org],
        location=[manager_loc]
    ).create()
    with Session(
            test_name,
            user=manager_user.login,
            password=manager_user.password
    ) as session:
        dr_val = session.discoveryrule.read_all()
        assert dr.name in [rule['Name'] for rule in dr_val]
        session.discoveryrule.delete(dr.name)
        dr_val = session.discoveryrule.read_all()
        assert dr.name not in [rule['Name'] for rule in dr_val]


@tier2
def test_positive_view_existing_rule_with_non_admin_user(module_loc,
                                                         module_org,
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
    hg = entities.HostGroup(organization=[module_org]).create()
    dr = entities.DiscoveryRule(
        hostgroup=hg,
        organization=[module_org],
        location=[module_loc]
    ).create()
    with Session(
            test_name,
            user=reader_user.login,
            password=reader_user.password
    ) as session:
        dr_val = session.discoveryrule.read_all()
        assert dr.name in [rule['Name'] for rule in dr_val]


@tier2
def test_negative_delete_rule_with_non_admin_user(module_loc, module_org,
                                                  reader_user, test_name):
    """Delete rule with non-admin user by associating discovery_reader role

    :id: 23a7627c-6a9b-493b-871f-698543adf1d2

    :expectedresults: User should validation error and rule should not be
        deleted successfully.

    :CaseLevel: Integration
    """
    hg = entities.HostGroup(organization=[module_org]).create()
    dr = entities.DiscoveryRule(
        hostgroup=hg,
        organization=[module_org],
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
        assert dr.name in [rule['Name'] for rule in dr_val]


@run_in_one_thread
@tier2
def test_positive_list_host_based_on_rule_search_query(
        session, module_org, module_loc, module_discovery_env):
    """List all the discovered hosts resolved by given rule's search query
    e.g. all discovered hosts with cpu_count = 2, and list rule's associated
    hosts.

    :id: f7473fa2-7349-42d3-9cdb-f74b55d2f440

    :Steps:

        1. discovered host with cpu_count = 2
        2. Define a rule 'rule1' with search query cpu_count = 2
        3. Click on 'Discovered Hosts' from rule1
        4. Auto Provision the discovered host
        5. Click on 'Associated Hosts' from rule1

    :expectedresults:

        1. After step 3, the rule's Discovered host should be listed.
        2. The rule's Associated Host should be listed.

    :CaseLevel: Integration
    """
    ip_address = gen_ipaddr()
    cpu_count = gen_integer(2, 10)
    rule_search = 'cpu_count = {0}'.format(cpu_count)
    # any way create a host to be sure that this org has more than one host
    host = entities.Host(organization=module_org, location=module_loc).create()
    host_group = entities.HostGroup(
        organization=[module_org],
        location=[module_loc],
        medium=host.medium,
        root_pass=gen_string('alpha'),
        operatingsystem=host.operatingsystem,
        ptable=host.ptable,
        domain=host.domain,
        architecture=host.architecture,
    ).create()
    discovery_rule = entities.DiscoveryRule(
        hostgroup=host_group,
        search_=rule_search,
        organization=[module_org],
        location=[module_loc]
    ).create()
    discovered_host = create_discovered_host(
        ip_address=ip_address,
        options={'physicalprocessorcount': cpu_count}
    )
    # create an other discovered host with an other cpu count
    create_discovered_host(options={'physicalprocessorcount': cpu_count+1})
    provisioned_host_name = '{0}.{1}'.format(
        discovered_host['name'], host.domain.read().name)
    with session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_loc.name)
        values = session.discoveryrule.read_all()
        assert discovery_rule.name in [rule['Name'] for rule in values]
        values = session.discoveryrule.read_discovered_hosts(
            discovery_rule.name)
        assert values['searchbox'] == rule_search
        assert len(values['table']) == 1
        assert values['table'][0]['IP Address'] == ip_address
        assert values['table'][0]['CPUs'] == str(cpu_count)
        # auto provision the discovered host
        session.discoveredhosts.apply_action(
            'Auto Provision', [discovered_host['name']])
        assert not session.discoveredhosts.search(
            'name = "{0}"'.format(discovered_host['name']))
        values = session.discoveryrule.read_associated_hosts(
            discovery_rule.name)
        assert (values['searchbox']
                == 'discovery_rule = "{0}"'.format(discovery_rule.name))
        assert len(values['table']) == 1
        assert values['table'][0]['Name'] == provisioned_host_name
        values = session.host.get_details(provisioned_host_name)
        assert (values['properties']['properties_table']['IP Address']
                == ip_address)


@tier2
@upgrade
def test_positive_end_to_end(session, module_org, module_loc):
    """Perform end to end testing for discovery rule component.

    :id: dd35e566-dc3a-43d3-939c-a33ae528740f

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    rule_name = gen_string('alpha')
    search = 'cpu_count = {0}'.format(gen_integer(1, 5))
    hg_name = gen_string('alpha')
    hostname = gen_string('alpha')
    hosts_limit = str(gen_integer(0, 100))
    priority = str(gen_integer(1, 100))
    new_rule_name = gen_string('alpha')
    new_search = 'cpu_count = {0}'.format(gen_integer(6, 10))
    new_hg_name = gen_string('alpha')
    new_hostname = gen_string('alpha')
    new_hosts_limit = str(gen_integer(101, 200))
    new_priority = str(gen_integer(101, 200))
    entities.HostGroup(name=hg_name, organization=[module_org], location=[module_loc]).create()
    entities.HostGroup(name=new_hg_name, organization=[module_org], location=[module_loc]).create()
    new_org = entities.Organization().create()
    new_loc = entities.Location().create()
    with session:
        session.discoveryrule.create({
            'primary.name': rule_name,
            'primary.search': search,
            'primary.host_group': hg_name,
            'primary.hostname': hostname,
            'primary.hosts_limit': hosts_limit,
            'primary.priority': priority,
            'primary.enabled': False,
            'organizations.resources.assigned': [module_org.name],
            'locations.resources.assigned': [module_loc.name],
        })
        values = session.discoveryrule.read(rule_name)
        assert values['primary']['name'] == rule_name
        assert values['primary']['search'] == search
        assert values['primary']['host_group'] == hg_name
        assert values['primary']['hostname'] == hostname
        assert values['primary']['hosts_limit'] == hosts_limit
        assert values['primary']['priority'] == priority
        assert values['primary']['enabled'] is False
        assert values['organizations']['resources']['assigned'] == [module_org.name]
        assert values['locations']['resources']['assigned'] == [module_loc.name]
        session.discoveryrule.update(rule_name, {
            'primary.name': new_rule_name,
            'primary.search': new_search,
            'primary.host_group': new_hg_name,
            'primary.hostname': new_hostname,
            'primary.hosts_limit': new_hosts_limit,
            'primary.priority': new_priority,
            'primary.enabled': True,
            'organizations.resources.assigned': [new_org.name],
            'locations.resources.assigned': [new_loc.name],
        })
        rules = session.discoveryrule.read_all()
        assert rule_name not in [rule['Name'] for rule in rules]
        values = session.discoveryrule.read(new_rule_name)
        assert values['primary']['name'] == new_rule_name
        assert values['primary']['search'] == new_search
        assert values['primary']['host_group'] == new_hg_name
        assert values['primary']['hostname'] == new_hostname
        assert values['primary']['hosts_limit'] == new_hosts_limit
        assert values['primary']['priority'] == new_priority
        assert values['primary']['enabled'] is True
        assert {new_org.name, module_org.name} == set(
            values['organizations']['resources']['assigned'])
        assert {new_loc.name, module_loc.name} == set(
            values['locations']['resources']['assigned'])
        session.discoveryrule.delete(new_rule_name)
        rules = session.discoveryrule.read_all()
        assert new_rule_name not in [rule['Name'] for rule in rules]
