"""Tests for parameters

:Requirement: Parameters

:CaseAutomation: Automated

:CaseComponent: Parameters

:Team: Rocket

:CaseImportance: Critical
"""
from fauxfactory import gen_string
import pytest


@pytest.fixture
def param_name():
    """Generate name string for common parameter and return to test cases"""
    """Generate name for common parameter"""
    return gen_string('alpha')


@pytest.fixture
def param_value():
    """Generate value string for common parameter and return to test cases"""
    """Generate value for common parameter"""
    return gen_string('alpha')


@pytest.fixture
def cp(param_name, param_value, module_target_sat):
    """Create common parameter object, yields it for test cases, delete object before teardown"""
    """Create common parameter"""
    cp = module_target_sat.api.CommonParameter(name=param_name, value=param_value).create()

    yield cp

    cp.delete()


@pytest.fixture
def host(param_name, param_value, module_org, module_location, module_target_sat, cp, hostgroup):
    """Create host object, yeilds it for test cases, delete object before teardown"""
    """Create host"""
    host = module_target_sat.api.Host(organization=module_org, location=module_location).create()

    yield host

    host.delete()


@pytest.fixture
def hostgroup(param_name, param_value, module_org, module_target_sat):
    """Create hostgroup object, yeilds it for test cases, delete object before teardown"""
    """Create hostgroup"""
    hg = module_target_sat.api.HostGroup(
        organization=[module_org],
        group_parameters_attributes=[{'name': param_name, 'value': param_value}],
    ).create()

    yield hg

    hg.delete()


@pytest.mark.tier1
@pytest.mark.e2e
@pytest.mark.upgrade
def test_positive_parameter_precedence_impact(
    request, host, hostgroup, cp, param_name, param_value
):
    """Check parameter precedences for Global, Hostgroup, and Host parameters

    :id: 8dd6c4e8-4ec9-4bee-8a04-f5788960979b

    :setup:
        1. Create Global Parameter
        2. Create host and verify global parameter is assigned
        3. Create Host Group with parameter

    :steps:
        1. Assign hostgroup to host created above and verify hostgroup parameter is assigned.
        2. Add parameter on the host directly, and verify that this should take precedence
            over Host group and Global Parameter

    :expectedresults: Host parameter take precedence over hostgroup and global parameter,
        and hostgroup take precedence over global parameter when there are no host parameters
    """
    result = [res for res in host.all_parameters if res['name'] == param_name]
    assert result[0]['name'] == param_name
    assert result[0]['associated_type'] == 'global'

    host.hostgroup = hostgroup
    host = host.update(['hostgroup'])
    result = [res for res in host.all_parameters if res['name'] == param_name]
    assert result[0]['name'] == param_name
    assert result[0]['associated_type'] != 'global'
    assert result[0]['associated_type'] == 'host group'

    host.host_parameters_attributes = [{'name': param_name, 'value': param_value}]
    host = host.update(['host_parameters_attributes'])
    result = [res for res in host.all_parameters if res['name'] == param_name]
    assert result[0]['name'] == param_name
    assert result[0]['associated_type'] != 'global'
    assert result[0]['associated_type'] != 'host group'
    assert result[0]['associated_type'] == 'host'
