# -*- encoding: utf-8 -*-
"""API Tests for foreman discovery feature

:Requirement: Discoveryrule

:CaseAutomation: Automated

:CaseComponent: DiscoveryPlugin

:TestType: Functional

:CaseLevel: Acceptance

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_choice
from fauxfactory import gen_integer
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.datafactory import valid_data_list
from robottelo.decorators import tier1


@pytest.fixture(scope="module")
def module_hostgroup(module_org):
    module_hostgroup = entities.HostGroup(organization=[module_org]).create()
    yield module_hostgroup
    module_hostgroup.delete()


@pytest.fixture(scope="module")
def module_location(module_location):
    yield module_location
    module_location.delete()


@pytest.fixture(scope="module")
def module_org(module_org):
    yield module_org
    module_org.delete()


@tier1
def test_positive_end_to_end_crud(module_org, module_location, module_hostgroup):
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
    discovery_rule = entities.DiscoveryRule(
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


@tier1
def test_negative_create_with_invalid_host_limit_and_priority():
    """Create a discovery rule with invalid host limit and priority

    :id: e3c7acb1-ac56-496b-ac04-2a83f66ec290

    :expectedresults: Validation error should be raised
    """
    with pytest.raises(HTTPError):
        entities.DiscoveryRule(max_count=gen_string('alpha')).create()
    with pytest.raises(HTTPError):
        entities.DiscoveryRule(priority=gen_string('alpha')).create()
