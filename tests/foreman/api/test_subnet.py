"""Tests for the ``subnets`` paths.


An API reference is available here:
http://theforeman.org/api/apidoc/v2/1.15.html


:Requirement: Subnet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Networking

:Assignee: rdrazny

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import re

import pytest
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.utils.datafactory import gen_string
from robottelo.utils.datafactory import generate_strings_list
from robottelo.utils.datafactory import invalid_values_list
from robottelo.utils.datafactory import parametrized


@pytest.mark.tier1
def test_positive_create_with_parameter():
    """Subnet can be created along with parameters

    :id: ec581cb5-8c48-4b9c-b536-302c0b7ec30f

    :steps: Create Subnet with parameter that has single key and single
        value

    :expectedresults: The Subnet is created with parameter
    """
    parameter = [{'name': gen_string('alpha'), 'value': gen_string('alpha')}]
    subnet = entities.Subnet(subnet_parameters_attributes=parameter).create()
    assert subnet.subnet_parameters_attributes[0]['name'] == parameter[0]['name']
    assert subnet.subnet_parameters_attributes[0]['value'] == parameter[0]['value']


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(generate_strings_list()))
def test_positive_add_parameter(name):
    """Parameters can be created in subnet

    :id: c1dae6f4-45b1-45db-8529-d7918e41a99b

    :parametrized: yes

    :steps:

        1. Create Subnet with all the details
        2. Create subnet parameter with single key and single value

    :expectedresults: The parameter should be created in subnet

    :CaseImportance: Medium
    """
    subnet = entities.Subnet().create()
    value = gen_string('utf8')
    subnet_param = entities.Parameter(subnet=subnet.id, name=name, value=value).create()
    assert subnet_param.name == name
    assert subnet_param.value == value


@pytest.mark.tier1
def test_positive_add_parameter_with_values_and_separator():
    """Subnet parameters can be created with values separated by comma

    :id: b3de6f96-7c39-4c44-b91c-a6d141f5dd6a

    :steps:

        1. Create Subnet with all the details
        2. Create subnet parameter having single key and values
            separated with comma

    :expectedresults: The parameter with values separated by comma should
        be saved in subnet

    :CaseImportance: Low
    """
    subnet = entities.Subnet().create()
    name = gen_string('alpha')
    values = ', '.join(generate_strings_list())
    subnet_param = entities.Parameter(name=name, subnet=subnet.id, value=values).create()
    assert subnet_param.name == name
    assert subnet_param.value == values


@pytest.mark.tier1
@pytest.mark.parametrize(
    'separator', **parametrized({'comma': ',', 'slash': '/', 'dash': '-', 'pipe': '|'})
)
def test_positive_create_with_parameter_and_valid_separator(separator):
    """Subnet parameters can be created with name with valid separators

    :id: d1e2d75a-a1e8-4767-93f1-0bb1b75e10a0

    :parametrized: yes

    :steps:
        1. Create Subnet with all the details
        2. Create subnet parameter having key with name separated
            by valid separators(e.g fwd slash) and value

    :expectedresults: The parameter with name separated by valid
        separators should be saved in subnet

    :CaseImportance: Low
    """
    name = f'{separator}'.join(generate_strings_list())
    subnet = entities.Subnet().create()
    value = gen_string('utf8')
    subnet_param = entities.Parameter(name=name, subnet=subnet.id, value=value).create()
    assert subnet_param.name == name
    assert subnet_param.value == value


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(invalid_values_list() + ['name with space']))
def test_negative_create_with_parameter_and_invalid_separator(name):
    """Subnet parameters can not be created with name with invalid
    separators

    :id: 08d10b75-a0db-4a11-a915-965a2a207d16

    :parametrized: yes

    :steps:

        1. Create Subnet with all the details
        2. Create subnet parameter having key with name separated by
            invalid separators(e.g spaces) and value

    :expectedresults:

        1. The parameter with name separated by invalid separators
            should not be saved in subnet
        2. An error for invalid name should be thrown.

    :CaseImportance: Low
    """
    subnet = entities.Subnet().create()
    with pytest.raises(HTTPError):
        entities.Parameter(name=name, subnet=subnet.id).create()


@pytest.mark.tier1
def test_negative_create_with_duplicated_parameters():
    """Attempt to create multiple parameters with same key name for the
    same subnet

    :id: aa69bdcc-e833-41e4-8f72-7139bdd64daa

    :steps:

        1. Create Subnet with all the details
        2. Create Multiple parameters having duplicate key names

    :expectedresults:

        1. The subnet parameters should not be created with duplicate
            names
        2. An error for duplicate parameter should be thrown

    :CaseImportance: Low
    """
    subnet = entities.Subnet().create()
    entities.Parameter(name='duplicateParameter', subnet=subnet.id).create()
    with pytest.raises(HTTPError) as context:
        entities.Parameter(name='duplicateParameter', subnet=subnet.id).create()
    assert re.search("Name has already been taken", context.value.response.text)


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_inherit_subnet_parmeters_in_host():
    """Host inherits parameters from subnet

    :id: e372a594-f758-40ef-95ec-867937e44b63

    :steps:
        1. Create valid subnet with a valid parameter
        2. Create host with above subnet
        3. Assign hosts primary interface with subnet
        4. List inherited subnet parameters in above host

    :expectedresults:

        1. The parameters from subnet should be displayed in
            host parameters
        2. The parameters from subnet should be displayed in
            host enc output

    :CaseLevel: System

    :CaseImportance: Medium

    :BZ: 1470014
    """


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_subnet_parameters_override_from_host():
    """Subnet parameters values can be overridden from host

    :id: b977dbb7-b2e5-41a4-a0e9-2084deec6935

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host with above subnet
        3. Assign hosts primary interface with subnet
        4. Override subnet parameter value from host with some other value

    :expectedresults:

        1. The subnet parameters should override from host
        2. The new value should be assigned to parameter
        3. The parameter and value should be accessible as host parameters

    :CaseLevel: Integration

    :CaseImportance: Medium

    :BZ: 1470014
    """


@pytest.mark.tier3
def test_positive_subnet_parameters_override_impact_on_subnet():
    """Override subnet parameter from host impact on subnet parameter

    :id: 6fe963ed-93a3-496e-bfd9-599bf91a61f3

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host with above subnet
        3. Assign hosts primary interface with subnet
        4. Override subnet parameter value from host with some other value

    :expectedresults: The override value of subnet parameter from host
        should not change actual value in subnet parameter

    :CaseLevel: System

    :CaseImportance: Medium
    """

    # Create subnet with valid parameters
    parameter = [{'name': gen_string('alpha'), 'value': gen_string('alpha')}]
    org = entities.Organization().create()
    loc = entities.Location(organization=[org]).create()
    org_subnet = entities.Subnet(
        location=[loc], organization=[org], subnet_parameters_attributes=parameter
    ).create()
    assert org_subnet.subnet_parameters_attributes[0]['name'] == parameter[0]['name']
    assert org_subnet.subnet_parameters_attributes[0]['value'] == parameter[0]['value']
    # Create host with above subnet
    host = entities.Host(location=loc, organization=org, subnet=org_subnet).create()
    assert host.subnet.read().name == org_subnet.name
    parameter_new_value = [
        {
            'name': org_subnet.subnet_parameters_attributes[0]['name'],
            'value': gen_string('alpha'),
        }
    ]
    host.host_parameters_attributes = parameter_new_value
    host = host.update(['host_parameters_attributes'])
    assert host.host_parameters_attributes[0]['value'] == parameter_new_value[0]['value']
    assert (
        host.host_parameters_attributes[0]['name']
        == org_subnet.subnet_parameters_attributes[0]['name']
    )
    assert org_subnet.read().subnet_parameters_attributes[0]['value'] == parameter[0]['value']


@pytest.mark.tier1
def test_positive_update_parameter():
    """Subnet parameter can be updated

    :id: 8c389c3f-60ef-4856-b8fc-c5b066c67a2f

    :steps:

        1. Create valid subnet with valid parameter
        2. Update above subnet parameter with new name and
            value

    :expectedresults: The parameter name and value should be updated

    :CaseImportance: Medium
    """
    parameter = [{'name': gen_string('alpha'), 'value': gen_string('alpha')}]
    subnet = entities.Subnet(subnet_parameters_attributes=parameter).create()
    update_parameter = [{'name': gen_string('utf8'), 'value': gen_string('utf8')}]
    subnet.subnet_parameters_attributes = update_parameter
    up_subnet = subnet.update(['subnet_parameters_attributes'])
    assert up_subnet.subnet_parameters_attributes[0]['name'] == update_parameter[0]['name']
    assert up_subnet.subnet_parameters_attributes[0]['value'] == update_parameter[0]['value']


@pytest.mark.tier1
@pytest.mark.parametrize('new_name', **parametrized(invalid_values_list() + ['name with space']))
def test_negative_update_parameter(new_name):
    """Subnet parameter can not be updated with invalid names

    :id: fcdbad13-ad96-4152-8e20-e023d61a2853

    :parametrized: yes

    :steps:

        1. Create valid subnet with valid parameter
        2. Update above subnet parameter with some invalid
            name. e.g name with spaces

    :expectedresults:

        1. The parameter should not be updated with invalid name
        2. An error for invalid name should be thrown

    :CaseImportance: Medium
    """
    subnet = entities.Subnet().create()
    sub_param = entities.Parameter(
        name=gen_string('utf8'), subnet=subnet.id, value=gen_string('utf8')
    ).create()
    with pytest.raises(HTTPError):
        sub_param.name = new_name
        sub_param.update(['name'])


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_update_subnet_parameter_host_impact():
    """Update in parameter name and value from subnet component updates
    the parameter in host inheriting that subnet

    :id: 64ac7873-ed36-4cad-a8db-5c9a4826868b

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host with the above subnet
        3. Update subnet parameter with new name and value

    :expectedresults:

        1. The inherited subnet parameter in host should have
            updated name and value
        2. The inherited subnet parameter in host enc should have
            updated name and value

    :CaseLevel: Integration

    :BZ: 1470014
    """


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete_subnet_parameter():
    """Subnet parameter can be deleted

    :id: 972b66ec-d506-4fcb-9786-c62f2f79ac1a

    :steps:

        1. Create valid subnet with valid parameter
        2. Delete the above subnet parameter

    :expectedresults: The parameter should be deleted from subnet
    """
    subnet = entities.Subnet().create()
    sub_param = entities.Parameter(subnet=subnet.id).create()
    sub_param.delete()
    with pytest.raises(HTTPError):
        sub_param.read()


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_delete_subnet_parameter_host_impact():
    """Deleting parameter from subnet component deletes the parameter in
    host inheriting that subnet

    :id: f5174e00-33cd-4008-8112-9c8190859244

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host with the above subnet
        3. Delete the above parameter from subnet
        4. List subnet parameters for above host

    :expectedresults:

        1. The parameter should be deleted from host
        2. The parameter should be deleted from host enc

    :CaseLevel: Integration

    :BZ: 1470014
    """


@pytest.mark.stubbed
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_delete_subnet_overridden_parameter_host_impact():
    """Deleting parameter from subnet component doesnt deletes its
    overridden parameter in host inheriting that subnet

    :id: e8f4a8e8-64ec-4a0f-aee4-14b6e984b470

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host with the above subnet
        3. Override subnet parameter value from host
        4. Delete the above parameter from subnet
        5. List host parameters

    :expectedresults:

        1. The parameter should not be deleted from host as it becomes
            host parameter now
        2. The parameter should not be deleted from host enc as well

    :CaseLevel: Integration

    :BZ: 1470014
    """


@pytest.mark.tier1
def test_positive_list_parameters():
    """Satellite lists all the subnet parameters

    :id: ce86d531-bf6b-45a9-81e3-67e1b3398f76

    :steps:

        1. Create subnet with all the details
        2. Add two parameters in subnet
        3. List parameters of subnet

    :expectedresults: The satellite should display all the subnet
        parameters
    """
    parameter = {'name': gen_string('alpha'), 'value': gen_string('alpha')}
    org = entities.Organization().create()
    loc = entities.Location(organization=[org]).create()
    org_subnet = entities.Subnet(
        location=[loc],
        organization=[org],
        ipam='DHCP',
        vlanid=gen_string('numeric', 3),
        subnet_parameters_attributes=[parameter],
    ).create()
    assert org_subnet.subnet_parameters_attributes[0]['name'] == parameter['name']
    assert org_subnet.subnet_parameters_attributes[0]['value'] == parameter['value']
    sub_param = entities.Parameter(
        name=gen_string('alpha'), subnet=org_subnet.id, value=gen_string('alpha')
    ).create()
    org_subnet = entities.Subnet(id=org_subnet.id).read()
    params_list = {
        param['name']: param['value']
        for param in org_subnet.subnet_parameters_attributes
        if param['name'] == sub_param.name
    }
    assert params_list[sub_param.name] == sub_param.value


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_subnet_parameter_priority():
    """Higher priority hosts component parameter overrides subnet parameter
     with same name

    :id: 75e35bd7-c9bb-4cf9-8b80-018b836f3dbe

    :steps:

        1. Create valid subnet with valid parameter
        2. Create host group with parameter with same name as above
            subnet parameter
        3. Create host with the above subnet and hostgroup
        4. List host parameters

    :expectedresults:

        1. Host should display the parameter with value inherited from
            higher priority component(HostGroup in this case)
        2. Host enc should display the parameter with value inherited from
            higher priority component(HostGroup in this case)

    :CaseLevel: System

    :CaseImportance: Low

    :BZ: 1470014
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_negative_component_overrides_subnet_parameter():
    """Lower priority hosts component parameter doesnt overrides subnet
    parameter with same name

    :id: 35d2a5de-07c7-40d6-8d65-a4f3e00ee429

    :steps:

        1. Create valid subnet with valid parameter
        2. Create domain with parameter with same name as above
            subnet parameter
        3. Create host with the above subnet and domain
        4. List host parameters

    :expectedresults:

        1. Host should not display the parameter with value inherited from
            lower priority component(domain in this case)
        2. Host enc should not display the parameter with value inherited
            from lower priority component(domain in this case)

    :CaseLevel: System

    :CaseImportance: Low

    :BZ: 1470014
    """
