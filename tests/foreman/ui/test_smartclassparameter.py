"""Test class for Smart/Puppet Class Parameter

:Requirement: Classparameters

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice
from random import uniform

import pytest
import yaml
from nailgun import entities

from robottelo.constants import DEFAULT_LOC
from robottelo.constants import ENVIRONMENT
from robottelo.datafactory import gen_string

PM_NAME = 'generic_1'

pytestmark = [pytest.mark.run_in_one_thread, pytest.mark.skip_if_open("BZ:1996035")]


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_loc():
    default_loc_id = entities.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0].id
    return entities.Location(id=default_loc_id).read()


@pytest.fixture(scope='module')
def sc_params_list(module_puppet_classes):
    return entities.SmartClassParameters().search(
        query={'search': f'puppetclass="{module_puppet_classes[0].name}"', 'per_page': '1000'}
    )


@pytest.fixture(scope='module')
def module_host(
    module_org,
    module_loc,
    module_env_search,
    module_puppet_classes,
    default_smart_proxy,
):
    lce = entities.LifecycleEnvironment().search(
        query={'search': f'organization_id="{module_org.id}" and name="{ENVIRONMENT}"'}
    )[0]
    host = entities.Host(
        organization=module_org,
        location=module_loc,
        content_facet_attributes={
            'lifecycle_environment_id': lce.id,
        },
        environment=module_env_search,
        puppetclass=module_puppet_classes,
        puppet_proxy=default_smart_proxy,
        puppet_ca_proxy=default_smart_proxy,
    ).create()
    return host


@pytest.fixture(scope='module')
def domain(module_host):
    return entities.Domain(id=module_host.domain.id).read()


@pytest.mark.tier2
def test_positive_end_to_end(session, module_puppet_classes, sc_params_list):
    """Perform end to end testing for smart class parameter component

    :id: 05ccb04e-5d21-44cc-a01c-807469be06c0

    :expectedresults: All expected basic actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    sc_param = sc_params_list.pop()
    override_priority = '\n'.join(['os', 'hostgroup', 'fqdn', 'domain'])
    override_value = gen_string('alphanumeric')
    desc = gen_string('alpha')
    validation_value = gen_string('numeric')
    data_list = [
        {'sc_type': 'string', 'value': gen_string('alphanumeric')},
        {'sc_type': 'boolean', 'value': choice(['true', 'false'])},
        {'sc_type': 'integer', 'value': gen_string('numeric', 5).lstrip('0')},
        {'sc_type': 'real', 'value': str(uniform(-1000, 1000))},
        {
            'sc_type': 'array',
            'value': (
                f'["{gen_string("alpha")}",'
                f'"{gen_string("numeric").lstrip("0")}",'
                f'"{gen_string("html")}"]'
            ),
        },
        {'sc_type': 'hash', 'value': f'{gen_string("alpha")}: {gen_string("alpha")}'},
        {'sc_type': 'yaml', 'value': f'{gen_string("alpha")}: {gen_string("alpha")}'},
        {
            'sc_type': 'json',
            'value': (
                f'{{"{gen_string("alpha")}":"{gen_string("numeric").lstrip("0")}",'
                f'"{gen_string("alpha")}":"{gen_string("alphanumeric")}"}}'
            ),
        },
    ]
    with session:
        assert session.sc_parameter.search(sc_param.parameter)[0]['Parameter'] == sc_param.parameter
        for data in data_list:
            session.sc_parameter.update(
                sc_param.parameter,
                {
                    'parameter.override': True,
                    'parameter.parameter_type': data['sc_type'],
                    'parameter.default_value': data['value'],
                },
            )
            sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
            # Application is adding some data for yaml and hash types once
            # smart class parameter is updated
            if data['sc_type'] == 'yaml' or data['sc_type'] == 'hash':
                data['value'] = f'{data["value"]}\n'
            assert sc_parameter_values['parameter']['parameter_type'] == data['sc_type']
            assert sc_parameter_values['parameter']['default_value']['value'] == data['value']
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.description': desc,
                'parameter.puppet_class': module_puppet_classes[0].name,
                'parameter.parameter_type': 'string',
                'parameter.default_value': validation_value,
                'parameter.optional_input_validators.validator_type': 'regexp',
                'parameter.optional_input_validators.validator_rule': '[0-9]',
                'parameter.prioritize_attribute_order.order': override_priority,
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'os',
                            'matcher_attribute_value': 'x86',
                        },
                        'Value': override_value,
                    }
                ],
            },
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values['parameter']['description'] == desc
        assert sc_parameter_values['parameter']['default_value']['value'] == validation_value
        assert (
            sc_parameter_values['parameter']['optional_input_validators']['validator_type']
            == 'regexp'
        )
        assert (
            sc_parameter_values['parameter']['optional_input_validators']['validator_rule']
            == '[0-9]'
        )
        assert (
            sc_parameter_values['parameter']['prioritize_attribute_order']['order']
            == override_priority
        )
        assert (
            sc_parameter_values['parameter']['matchers']['table'][0]['Value']['value']
            == override_value
        )


@pytest.mark.tier2
def test_positive_create_matcher_attribute_priority(session, sc_params_list, module_host, domain):
    """Matcher Value set on Attribute Priority for Host.

    :id: b83afe54-207e-4d6b-b705-1f3601c484a6

    :steps:
        1.  Check the Override checkbox.
        2.  Set some default Value.
        3.  Set fqdn as top priority attribute.
        4.  Create first matcher for fqdn with valid details.
        5.  Create second matcher for some attribute with valid details.
            Note - The fqdn/host should have this attribute.
        6.  Submit the change.
        7.  Go to YAML output of associated host.
        8.  Resubmit the same form to check bz-1241249

    :expectedresults: The YAML output has the value only for fqdn matcher.

    :CaseLevel: Integration

    :BZ: 1241249

    :CaseImportance: Critical
    """
    sc_param = sc_params_list.pop()
    override_value = gen_string('alphanumeric')
    override_value2 = "['<%= @host.domain %>', '<%= @host.mac %>']"
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.default_value': gen_string('alphanumeric'),
                'parameter.prioritize_attribute_order.order': '\n'.join(
                    ['fqdn', 'hostgroup', 'os', 'domain']
                ),
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'fqdn',
                            'matcher_attribute_value': module_host.name,
                        },
                        'Value': override_value,
                    },
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'domain',
                            'matcher_attribute_value': domain.name,
                        },
                        'Value': override_value2,
                    },
                ],
            },
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert (
            sc_parameter_values['parameter']['matchers']['table'][0]['Value']['value']
            == override_value
        )
        assert (
            sc_parameter_values['parameter']['matchers']['table'][1]['Value']['value']
            == override_value2
        )
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == override_value
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.prioritize_attribute_order.order': '\n'.join(
                    ['domain', 'hostgroup', 'os', 'fqdn']
                )
            },
        )
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == str([domain.name, module_host.mac])

        # That update operation will change nothing, but submit the same form
        session.sc_parameter.update(sc_param.parameter, {'parameter.override': True})
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == str([domain.name, module_host.mac])


@pytest.mark.tier2
def test_positive_create_matcher_avoid_duplicate(session, sc_params_list, module_host, domain):
    """Merge the values of all the associated matchers, remove duplicates.

    :id: c8557813-2c09-4196-b1c1-f7e609aa0310

    :steps:
        1.  Check the Override checkbox.
        2.  Set some default Value of array type.
        3.  Create first matcher for attribute fqdn with some value.
        4.  Create second matcher for other attribute with same value as
            fqdn matcher.
            Note - The fqdn/host should have this attribute.
        5.  Select 'Merge overrides' checkbox.
        6.  Select 'Merge default' checkbox.
        7.  Select 'Avoid Duplicates' checkbox.
        8.  Submit the change.
        9.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values merged from all the associated
            matchers.
        2.  The YAML output has the default value of parameter.
        3.  Duplicate values in YAML output are removed / not displayed.

    :CaseImportance: Critical

    :BZ: 1734022
    """
    sc_param = sc_params_list.pop()
    override_value = '[80,90]'
    override_value2 = '[90,100]'
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.default_value': '[20]',
                'parameter.parameter_type': 'array',
                'parameter.prioritize_attribute_order.merge_overrides': True,
                'parameter.prioritize_attribute_order.merge_default': True,
                'parameter.prioritize_attribute_order.avoid_duplicates': True,
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'fqdn',
                            'matcher_attribute_value': module_host.name,
                        },
                        'Value': override_value,
                    },
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'domain',
                            'matcher_attribute_value': domain.name,
                        },
                        'Value': override_value2,
                    },
                ],
            },
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert (
            sc_parameter_values['parameter']['matchers']['table'][0]['Value']['value']
            == override_value
        )
        assert (
            sc_parameter_values['parameter']['matchers']['table'][1]['Value']['value']
            == override_value2
        )
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == [20, 80, 90, 100]


@pytest.mark.tier2
def test_positive_update_matcher_from_attribute(session, sc_params_list, module_host):
    """Impact on parameter on editing the parameter value from attribute.

    :id: a7b3ecde-a311-421c-be4b-0f72ab1f44ba

    :steps:

        1.  Check the override checkbox for the parameter.
        2.  Associate parameter with fqdn/hostgroup.
        3.  Create a matcher for fqdn/hostgroup with valid details.
        4.  From host/hostgroup, edit the parameter value.
        5.  Submit the changes.

    :expectedresults:

        1.  The host/hostgroup is saved with changes.
        2.  Matcher value in parameter is updated from fqdn/hostgroup.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    sc_param = sc_params_list.pop()
    param_default_value = gen_string('numeric').lstrip('0')
    override_value = gen_string('numeric').lstrip('0')
    new_override_value = gen_string('numeric').lstrip('0')
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.parameter_type': 'integer',
                'parameter.default_value': param_default_value,
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'fqdn',
                            'matcher_attribute_value': module_host.name,
                        },
                        'Value': override_value,
                    }
                ],
            },
        )
        host_sc_parameter_value = session.host.get_puppet_class_parameter_value(
            module_host.name, sc_param.parameter
        )
        assert host_sc_parameter_value['hidden'] is False
        assert host_sc_parameter_value['overridden'] is True
        assert host_sc_parameter_value['value'] == override_value
        session.host.set_puppet_class_parameter_value(
            module_host.name, sc_param.parameter, dict(value=new_override_value)
        )
        host_sc_parameter_value = session.host.get_puppet_class_parameter_value(
            module_host.name, sc_param.parameter
        )
        assert host_sc_parameter_value['value'] == new_override_value
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert len(sc_parameter_values['parameter']['matchers']['table']) == 1
        property_matcher = sc_parameter_values['parameter']['matchers']['table'][0]
        assert property_matcher['Attribute type']['matcher_attribute_type'] == 'fqdn'
        assert property_matcher['Attribute type']['matcher_attribute_value'] == module_host.name
        assert property_matcher['Value']['value'] == new_override_value


@pytest.mark.tier2
def test_positive_impact_parameter_delete_attribute(
    session, sc_params_list, module_env_search, module_puppet_classes
):
    """Impact on parameter after deleting associated attribute.

    :id: 5d9bed6d-d9c0-4eb3-aaf7-bdda1f9203dd

    :steps:
        1.  Override the parameter and create a matcher for some attribute.
        2.  Delete the attribute.
        3.  Recreate the attribute with same name as earlier.

    :expectedresults:
        1.  The matcher for deleted attribute removed from parameter.
        2.  On recreating attribute, the matcher should not reappear
            in parameter.

    :CaseLevel: Integration
    """
    sc_param = sc_params_list.pop()
    matcher_value = gen_string('alpha')
    hg_name = gen_string('alpha')
    hostgroup = entities.HostGroup(name=hg_name, environment=module_env_search).create()
    hostgroup.add_puppetclass(data={'puppetclass_id': module_puppet_classes[0].id})
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.default_value': gen_string('alpha'),
                'parameter.parameter_type': 'string',
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'hostgroup',
                            'matcher_attribute_value': hg_name,
                        },
                        'Value': matcher_value,
                    }
                ],
            },
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert len(sc_parameter_values['parameter']['matchers']['table']) == 1
        assert (
            sc_parameter_values['parameter']['matchers']['table'][0]['Value']['value']
            == matcher_value
        )
        assert session.sc_parameter.search(sc_param.parameter)[0]['Number of Overrides'] == '1'
        hostgroup.delete()
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert len(sc_parameter_values['parameter']['matchers']['table']) == 0
        assert session.sc_parameter.search(sc_param.parameter)[0]['Number of Overrides'] == '0'
        hostgroup = entities.HostGroup(name=hg_name, environment=module_env_search).create()
        hostgroup.add_puppetclass(data={'puppetclass_id': module_puppet_classes[0].id})
        assert session.sc_parameter.search(sc_param.parameter)[0]['Number of Overrides'] == '0'


@pytest.mark.tier2
def test_positive_hidden_value_in_attribute(session, sc_params_list, module_host):
    """Update the hidden default value of parameter in attribute. Then unhide.

    :id: c10c20bd-0284-4e5d-b789-fddd3b81b81b

    :steps:

        1.  Check the override checkbox for the parameter.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate parameter on host/hostgroup.
        6.  In host/hostgroup, update the parameter value.
        7.  Unhide the variable.

    :expectedresults:

        1.  In host/hostgroup, the parameter value is updated.
        2.  The parameter Value displayed as hidden.
        3.  In parameter, new matcher created for fqdn/hostgroup.
        4.  And the value shown hidden.
        5.  Parameter is successfully unhidden.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    sc_param = sc_params_list.pop()
    param_default_value = gen_string('alpha')
    host_override_value = gen_string('alpha')
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.parameter_type': 'string',
                'parameter.default_value': param_default_value,
                'parameter.hidden': True,
            },
        )
        host_sc_parameter_value = session.host.get_puppet_class_parameter_value(
            module_host.name, sc_param.parameter
        )
        assert host_sc_parameter_value['hidden'] is True
        assert host_sc_parameter_value['overridden'] is False
        assert host_sc_parameter_value['value'] == param_default_value
        # Update
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            sc_param.parameter,
            dict(value=host_override_value, overridden=True, hidden=False),
        )
        host_sc_parameter_value = session.host.get_puppet_class_parameter_value(
            module_host.name, sc_param.parameter
        )
        assert host_sc_parameter_value['hidden'] is True
        assert host_sc_parameter_value['overridden'] is True
        assert host_sc_parameter_value['value'] == host_override_value
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values['parameter']['key'] == sc_param.parameter
        assert sc_parameter_values['parameter']['default_value']['value'] == param_default_value
        assert sc_parameter_values['parameter']['default_value']['hidden'] is True
        host_matcher = [
            matcher
            for matcher in sc_parameter_values['parameter']['matchers']['table']
            if (
                matcher['Attribute type']['matcher_attribute_type'] == 'fqdn'
                and matcher['Attribute type']['matcher_attribute_value'] == module_host.name
            )
        ][0]
        assert host_matcher['Value']['value'] == host_override_value
        assert host_matcher['Value']['hidden'] is True
        # Unhide
        session.host.set_puppet_class_parameter_value(
            module_host.name, sc_param.parameter, dict(overridden=True, hidden=False)
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values['parameter']['key'] == sc_param.parameter
        assert sc_parameter_values['parameter']['default_value']['hidden'] is True
