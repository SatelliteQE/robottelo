"""Test class for Foreman Discovery Rules

:Requirement: Discoveryrule

:CaseAutomation: Automated

:CaseComponent: DiscoveryPlugin

:Team: Rocket

:CaseImportance: High

"""

from fauxfactory import gen_integer, gen_ipaddr, gen_string
import pytest


@pytest.fixture
def module_discovery_env(module_org, module_location, module_target_sat):
    discovery_loc = module_target_sat.update_setting('discovery_location', module_location.name)
    discovery_org = module_target_sat.update_setting('discovery_organization', module_org.name)
    yield
    module_target_sat.update_setting('discovery_location', discovery_loc)
    module_target_sat.update_setting('discovery_organization', discovery_org)


@pytest.fixture(scope='module')
def manager_user(module_location, module_org, module_target_sat):
    manager_role = module_target_sat.api.Role().search(
        query={'search': 'name="Discovery Manager"'}
    )[0]
    password = gen_string('alphanumeric')
    manager_user = module_target_sat.api.User(
        login=gen_string('alpha'),
        role=[manager_role],
        password=password,
        location=[module_location],
        organization=[module_org],
    ).create()
    manager_user.password = password
    return manager_user


@pytest.fixture(scope='module')
def reader_user(module_location, module_org, module_target_sat):
    password = gen_string('alphanumeric')
    # Applying Discovery reader_role to the user
    role = module_target_sat.api.Role().search(query={'search': 'name="Discovery Reader"'})[0]
    reader_user = module_target_sat.api.User(
        login=gen_string('alpha'),
        role=[role],
        password=password,
        organization=[module_org],
        location=[module_location],
    ).create()
    reader_user.password = password
    return reader_user


def gen_int32(min_value=1):
    max_value = (2**31) - 1
    return gen_integer(min_value=min_value, max_value=max_value)


@pytest.mark.e2e
def test_positive_crud_with_non_admin_user(
    module_location, manager_user, module_org, module_target_sat
):
    """CRUD with non-admin user by associating discovery_manager role

    :id: 6a03983b-363d-4646-b277-34af5f5abc55

    :expectedresults: All crud operations should work with non_admin user.
    """
    rule_name = gen_string('alpha')
    search = gen_string('alpha')
    priority = str(gen_integer(1, 20))
    new_rule_name = gen_string('alpha')
    new_search = gen_string('alpha')
    new_hg_name = gen_string('alpha')
    new_priority = str(gen_integer(101, 200))
    hg = module_target_sat.api.HostGroup(organization=[module_org]).create()
    new_hg_name = module_target_sat.api.HostGroup(organization=[module_org]).create()
    with module_target_sat.ui_session(
        user=manager_user.login, password=manager_user.password
    ) as session:
        session.location.select(loc_name=module_location.name)
        session.discoveryrule.create(
            {
                'primary.name': rule_name,
                'primary.search': search,
                'primary.host_group': hg.name,
                'primary.priority': priority,
            }
        )

        values = session.discoveryrule.read(rule_name, widget_names='primary')
        assert values['primary']['name'] == rule_name
        assert values['primary']['search'] == search
        assert values['primary']['host_group'] == hg.name
        assert values['primary']['priority'] == priority
        session.discoveryrule.update(
            rule_name,
            {
                'primary.name': new_rule_name,
                'primary.search': new_search,
                'primary.host_group': new_hg_name.name,
                'primary.priority': new_priority,
            },
        )
        values = session.discoveryrule.read(
            new_rule_name,
            widget_names='primary',
        )
        assert values['primary']['name'] == new_rule_name
        assert values['primary']['search'] == new_search
        assert values['primary']['host_group'] == new_hg_name.name
        assert values['primary']['priority'] == new_priority

        session.discoveryrule.delete(new_rule_name)
        dr_val = session.discoveryrule.read_all()
        assert 'No Discovery Rules found in this context' in dr_val


def test_negative_delete_rule_with_non_admin_user(
    request, module_location, module_org, module_target_sat, reader_user
):
    """Delete rule with non-admin user by associating discovery_reader role

    :id: 23a7627c-6a9b-493b-871f-698543adf1d2

    :expectedresults: User should validation error and rule should not be
        deleted successfully.
    """
    hg_name = gen_string('alpha')
    rule_name = gen_string('alpha')
    search = gen_string('alpha')
    hg = module_target_sat.api.HostGroup(
        name=hg_name, organization=[module_org], location=[module_location]
    ).create()
    dr = module_target_sat.api.DiscoveryRule(
        name=rule_name,
        search_=search,
        hostgroup=hg.id,
        organization=[module_org],
        location=[module_location],
    ).create()

    # teardown
    @request.addfinalizer
    def _finalize():
        dr = module_target_sat.api.DiscoveryRule().search(query={'search': f'name={rule_name}'})
        if dr:
            dr[0].delete()
        hg.delete()

    with module_target_sat.ui_session(
        user=reader_user.login, password=reader_user.password
    ) as session:
        with pytest.raises(ValueError):  # noqa: PT011 - TODO Adarsh determine better exception
            session.discoveryrule.delete(dr.name)
        dr_val = session.discoveryrule.read_all()
        assert dr.name in [rule['Name'] for rule in dr_val]


@pytest.mark.run_in_one_thread
def test_positive_list_host_based_on_rule_search_query(
    request,
    session,
    module_org,
    module_location,
    module_discovery_env,
    target_sat,
):
    """List all the discovered hosts resolved by given rule's search query
    e.g. all discovered hosts with cpu_count = 2, and list rule's associated
    hosts.

    :id: f7473fa2-7349-42d3-9cdb-f74b55d2f440

    :steps:
        1. discovered host with cpu_count = 2
        2. Define a rule 'rule1' with search query cpu_count = 2
        3. Click on 'Discovered Hosts' from rule1
        4. Auto Provision the discovered host
        5. Click on 'Associated Hosts' from rule1

    :expectedresults:
        1. After step 3, the rule's Discovered host should be listed.
        2. The rule's Associated Host should be listed.

    :BZ: 1731112
    """
    ip_address = gen_ipaddr(ipv6=target_sat.network_type.has_ipv6)
    cpu_count = gen_integer(2, 10)
    rule_name = gen_string('alpha')
    rule_search = f'cpu_count = {cpu_count}'
    # any way create a host to be sure that this org has more than one host
    host = target_sat.api.Host(organization=module_org, location=module_location).create()
    host_group = target_sat.api.HostGroup(
        organization=[module_org],
        location=[module_location],
        medium=host.medium,
        root_pass=gen_string('alpha'),
        operatingsystem=host.operatingsystem,
        ptable=host.ptable,
        domain=host.domain,
        architecture=host.architecture,
    ).create()
    discovery_rule = target_sat.api.DiscoveryRule(
        name=rule_name,
        hostgroup=host_group,
        search_=rule_search,
        organization=[module_org],
        location=[module_location],
        priority=gen_int32(),
    ).create()
    discovered_host = target_sat.api_factory.create_discovered_host(
        ip_address=ip_address, options={'physicalprocessorcount': cpu_count}
    )

    # teardown
    @request.addfinalizer
    def _finalize():
        host.delete()
        dr = target_sat.api.DiscoveryRule().search(query={'search': f'name={rule_name}'})
        if dr:
            dr[0].delete()
        target_sat.api.Host(id=discovered_host['id']).delete()
        host_group.delete()

    with session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        values = session.discoveryrule.read_all()
        assert discovery_rule.name in [rule['Name'] for rule in values]
        values = session.discoveryrule.read_discovered_hosts(discovery_rule.name)
        assert values['searchbox'] == rule_search
        assert len(values['table']) == 1
        lookup = "IPv6" if not target_sat.network_type.has_ipv4 else "IPv4"
        assert values['table'][0][lookup] == ip_address
        assert values['table'][0]['CPUs'] == str(cpu_count)
        # auto provision the discovered host
        result = target_sat.api.DiscoveredHost(id=discovered_host['id']).auto_provision()
        assert f'provisioned with rule {discovery_rule.name}' in result['message']
        values = session.discoveryrule.read_associated_hosts(discovery_rule.name)
        host_name = values['table'][0]['Name']
        assert values['searchbox'] == f'discovery_rule = "{discovery_rule.name}"'
        assert len(values['table']) == 1
        values = session.host_new.get_details(host_name, widget_names='overview')
        assert values['overview']['details']['details']['ipv4_address'] == ip_address


@pytest.mark.e2e
@pytest.mark.upgrade
def test_positive_end_to_end(session, module_org, module_location, module_target_sat):
    """Perform end to end testing for discovery rule component.

    :id: dd35e566-dc3a-43d3-939c-a33ae528740f

    :expectedresults: All expected CRUD actions finished successfully

    :CaseImportance: Critical
    """
    rule_name = gen_string('alpha')
    search = gen_string('alpha')
    hg_name = gen_string('alpha')
    hostname = gen_string('alpha')
    hosts_limit = str(gen_integer(0, 100))
    priority = str(gen_integer(1, 100))
    new_rule_name = gen_string('alpha')
    new_search = gen_string('alpha')
    new_hg_name = gen_string('alpha')
    new_hostname = gen_string('alpha')
    new_hosts_limit = str(gen_integer(101, 200))
    new_priority = str(gen_integer(101, 200))
    module_target_sat.api.HostGroup(
        name=hg_name, organization=[module_org], location=[module_location]
    ).create()
    module_target_sat.api.HostGroup(
        name=new_hg_name, organization=[module_org], location=[module_location]
    ).create()
    new_org = module_target_sat.api.Organization().create()
    new_loc = module_target_sat.api.Location().create()
    with session:
        session.discoveryrule.create(
            {
                'primary.name': rule_name,
                'primary.search': search,
                'primary.host_group': hg_name,
                'primary.hostname': hostname,
                'primary.hosts_limit': hosts_limit,
                'primary.priority': priority,
                'primary.enabled': False,
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_location.name],
            }
        )
        values = session.discoveryrule.read(
            rule_name, widget_names=['primary', 'organizations', 'locations']
        )
        assert values['primary']['name'] == rule_name
        assert values['primary']['search'] == search
        assert values['primary']['host_group'] == hg_name
        assert values['primary']['hostname'] == hostname
        assert values['primary']['hosts_limit'] == hosts_limit
        assert values['primary']['priority'] == priority
        assert values['primary']['enabled'] is False
        assert values['organizations']['resources']['assigned'] == [module_org.name]
        assert values['locations']['resources']['assigned'] == [module_location.name]
        session.discoveryrule.update(
            rule_name,
            {
                'primary.name': new_rule_name,
                'primary.search': new_search,
                'primary.host_group': new_hg_name,
                'primary.hostname': new_hostname,
                'primary.hosts_limit': new_hosts_limit,
                'primary.priority': new_priority,
                'primary.enabled': True,
                'organizations.resources.assigned': [new_org.name],
                'locations.resources.assigned': [new_loc.name],
            },
        )
        rules = session.discoveryrule.read_all()
        assert rule_name not in [rule['Name'] for rule in rules]
        values = session.discoveryrule.read(
            new_rule_name, widget_names=['primary', 'organizations', 'locations']
        )
        assert values['primary']['name'] == new_rule_name
        assert values['primary']['search'] == new_search
        assert values['primary']['host_group'] == new_hg_name
        assert values['primary']['hostname'] == new_hostname
        assert values['primary']['hosts_limit'] == new_hosts_limit
        assert values['primary']['priority'] == new_priority
        assert values['primary']['enabled'] is True
        assert {new_org.name, module_org.name} == set(
            values['organizations']['resources']['assigned']
        )
        assert {new_loc.name, module_location.name} == set(
            values['locations']['resources']['assigned']
        )
        session.discoveryrule.delete(new_rule_name)
        rules = session.discoveryrule.read_all()
        assert 'No Discovery Rules found in this context' in rules
