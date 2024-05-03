"""Tests for parameters

:Requirement: Parameters

:CaseAutomation: Automated

:CaseComponent: Parameters

:Team: Rocket

:CaseImportance: Critical
"""

from fauxfactory import gen_string
import pytest


@pytest.mark.tier1
@pytest.mark.e2e
@pytest.mark.upgrade
def test_positive_parameter_precedence_impact(
    request, module_org, module_location, module_target_sat
):
    """Check parameter precedences for Global, Hostgroup, and Host parameters

    :id: 8dd6c4e8-4ec9-4bee-8a04-f5788960979b

    :steps:
        1. Create Global Parameter
        2. Create Host Group with parameter
        3. Create host and verify global parameter is assigned
        4. Assign hostgroup to host created above and verify hostgroup parameter is assigned.
        5. Add parameter on the host directly, and verify that this should take precedence
            over Host group and Global Parameter

    :expectedresults: Host parameter take precedence over hostgroup and global parameter,
        and hostgroup take precedence over global parameter when there are no host parameters
    """
    param_name = gen_string('alpha')
    param_value = gen_string('alpha')

    cp = module_target_sat.api.CommonParameter(name=param_name, value=param_value).create()
    request.addfinalizer(cp.delete)

    hg = module_target_sat.api.HostGroup(
        organization=[module_org],
        group_parameters_attributes=[{'name': param_name, 'value': param_value}],
    ).create()
    request.addfinalizer(hg.delete)

    host = module_target_sat.api.Host(organization=module_org, location=module_location).create()
    request.addfinalizer(host.delete)
    result = [res for res in host.all_parameters if res['name'] == param_name]
    assert result[0]['name'] == param_name
    assert result[0]['associated_type'] == 'global'

    host.hostgroup = hg

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
