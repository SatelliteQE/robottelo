"""API Tests for foreman discovery feature

:Requirement: Discoveryrule

:CaseAutomation: Automated

:CaseComponent: DiscoveryPlugin

:Team: Rocket

:CaseImportance: High

"""

from fauxfactory import gen_choice, gen_integer, gen_string
import pytest
from requests.exceptions import HTTPError

from robottelo.utils.datafactory import valid_data_list


@pytest.fixture(scope='module')
def module_hostgroup(module_org, module_target_sat):
    module_hostgroup = module_target_sat.api.HostGroup(organization=[module_org]).create()
    yield module_hostgroup
    module_hostgroup.delete()


@pytest.fixture(scope='module')
def module_location(module_location):
    yield module_location
    module_location.delete()


@pytest.fixture(scope='module')
def module_org(module_org):
    yield module_org
    module_org.delete()


@pytest.mark.tier1
@pytest.mark.e2e
def test_positive_end_to_end_crud(module_org, module_location, module_hostgroup, module_target_sat):
    """Create a new discovery rule with several attributes, update them
    and delete the rule itself.

    :id: 25366930-b7f4-4db8-a9c3-a470fe4f3583

    :expectedresults: Rule should be created, modified and deleted successfully
        with given attributes.

    :CaseImportance: Critical
    """
    # Create discovery rule
    searches = [
        'CPU_Count = 1',
        'disk_count < 5',
        'memory > 500',
        'model = KVM',
        'Organization = Default_Organization',
    ]
    name = gen_choice(list(valid_data_list().values()))
    search = gen_choice(searches)
    hostname = 'myhost-<%= rand(99999) %>'
    discovery_rule = module_target_sat.api.DiscoveryRule(
        name=name,
        search_=search,
        hostname=hostname,
        organization=[module_org],
        location=[module_location],
        hostgroup=module_hostgroup,
    ).create()
    assert name == discovery_rule.name
    assert hostname == discovery_rule.hostname
    assert search == discovery_rule.search_
    assert module_org.name == discovery_rule.organization[0].read().name
    assert module_location.name == discovery_rule.location[0].read().name
    assert discovery_rule.enabled is True

    # Update discovery rule
    name = gen_choice(list(valid_data_list().values()))
    search = 'Location = Default_Location'
    max_count = gen_integer(1, 100)
    enabled = False
    discovery_rule.name = name
    discovery_rule.search_ = search
    discovery_rule.max_count = max_count
    discovery_rule.enabled = enabled
    discovery_rule = discovery_rule.update(['name', 'search_', 'max_count', 'enabled'])
    assert name == discovery_rule.name
    assert search == discovery_rule.search_
    assert max_count == discovery_rule.max_count
    assert enabled == discovery_rule.enabled

    # Delete discovery rule
    discovery_rule.delete()
    with pytest.raises(HTTPError):
        discovery_rule.read()


@pytest.mark.tier1
def test_negative_create_with_invalid_host_limit_and_priority(module_target_sat):
    """Create a discovery rule with invalid host limit and priority

    :id: e3c7acb1-ac56-496b-ac04-2a83f66ec290

    :expectedresults: Validation error should be raised
    """
    with pytest.raises(HTTPError):
        module_target_sat.api.DiscoveryRule(max_count=gen_string('alpha')).create()
    with pytest.raises(HTTPError):
        module_target_sat.api.DiscoveryRule(priority=gen_string('alpha')).create()


@pytest.mark.tier3
def test_positive_update_and_provision_with_rule_priority(
    module_target_sat, module_discovery_hostgroup, discovery_location, discovery_org
):
    """Create multiple discovery rules with different priority and check
    rule with highest priority executed first

    :id: b91c4979-f8ce-4f6e-9474-9ccc4c3bc793

    :Setup: Multiple hosts should already be discovered

    :expectedresults: Host with lower count have higher priority and that
        rule should be executed first

    :CaseImportance: High
    """
    discovered_host = module_target_sat.api_factory.create_discovered_host()

    prio_rule = module_target_sat.api.DiscoveryRule(
        max_count=5,
        hostgroup=module_discovery_hostgroup,
        search_=f'name = {discovered_host["name"]}',
        location=[discovery_location],
        organization=[discovery_org],
        priority=1,
    ).create()

    rule = module_target_sat.api.DiscoveryRule(
        max_count=5,
        hostgroup=module_discovery_hostgroup,
        search_=f'name = {discovered_host["name"]}',
        location=[discovery_location],
        organization=[discovery_org],
        priority=10,
    ).create()

    result = module_target_sat.api.DiscoveredHost(id=discovered_host['id']).auto_provision()
    assert f'provisioned with rule {prio_rule.name}' in result['message']

    # Delete discovery rule
    for _ in rule, prio_rule:
        _.delete()
        with pytest.raises(HTTPError):
            _.read()


@pytest.mark.tier3
def test_positive_multi_provision_with_rule_limit(
    request, module_target_sat, module_discovery_hostgroup, discovery_location, discovery_org
):
    """Create a discovery rule with certain host limit and try to provision more than the passed limit

    :id: 553c8ebf-d1c1-4ac2-7948-d3664a5b450b

    :Setup: Hosts should already be discovered

    :expectedresults: Rule should only be applied to the number of the hosts passed as limit in the rule

    :CaseImportance: High
    """

    discovered_host1 = module_target_sat.api_factory.create_discovered_host()
    request.addfinalizer(module_target_sat.api.Host(id=discovered_host1['id']).delete)
    discovered_host2 = module_target_sat.api_factory.create_discovered_host()
    request.addfinalizer(module_target_sat.api.DiscoveredHost(id=discovered_host2['id']).delete)
    rule = module_target_sat.api.DiscoveryRule(
        max_count=1,
        hostgroup=module_discovery_hostgroup,
        search_=f'name = {discovered_host1["name"]}',
        location=[discovery_location],
        organization=[discovery_org],
        priority=1000,
    ).create()
    request.addfinalizer(rule.delete)
    result = module_target_sat.api.DiscoveredHost().auto_provision_all()
    assert '1 discovered hosts were provisioned' in result['message']
