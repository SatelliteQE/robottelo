# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Class Parameter

:Requirement: Classparameters

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import yaml
from nailgun import entities

from robottelo.api.utils import delete_puppet_class, publish_puppet_module
from robottelo.constants import CUSTOM_PUPPET_REPO, ENVIRONMENT
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2

PM_NAME = 'ui_test_classparameters'
PUPPET_MODULES = [
    {'author': 'robottelo', 'name': PM_NAME}]


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def content_view(module_org):
    return publish_puppet_module(
        PUPPET_MODULES, CUSTOM_PUPPET_REPO, module_org)


@fixture(scope='module')
def puppet_env(content_view):
    return entities.Environment().search(
        query={'search': u'content_view="{0}"'.format(content_view.name)})[0]


@fixture(scope='module')
def puppet_class(puppet_env):
    puppet_class_entity = entities.PuppetClass().search(query={
        'search': u'name = "{0}" and environment = "{1}"'.format(
            PUPPET_MODULES[0]['name'], puppet_env.name)})[0]
    yield puppet_class_entity
    delete_puppet_class(puppet_class_entity.name)


@fixture(scope='module')
def sc_params_list(puppet_class):
    return entities.SmartClassParameters().search(
        query={
            'search': 'puppetclass="{0}"'.format(puppet_class.name),
            'per_page': 1000
        })


@fixture(scope='module')
def module_host(module_org, content_view, puppet_env, puppet_class):
    lce = entities.LifecycleEnvironment().search(
        query={
            'search': 'organization_id="{0}" and name="{1}"'.format(
                module_org.id, ENVIRONMENT)
        })[0]
    host = entities.Host(
        organization=module_org,
        content_facet_attributes={
            'content_view_id': content_view.id,
            'lifecycle_environment_id': lce.id,
        }).create()
    host.environment = puppet_env
    host.update(['environment'])
    host.add_puppetclass(data={'puppetclass_id': puppet_class.id})
    return host


@fixture(scope='module')
def domain(module_host):
    return entities.Domain(id=module_host.domain.id).read()


@tier2
def test_positive_create_matcher_attribute_priority(
        session, sc_params_list, module_host, domain):
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

    :expectedresults: The YAML output has the value only for fqdn matcher.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    sc_param = sc_params_list.pop()
    override_value = gen_string('alphanumeric')
    override_value2 = gen_string('alphanumeric')
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.default_value': gen_string('alpha'),
                'parameter.prioritize_attribute_order.order': '\n'.join(
                    ['fqdn', 'hostgroup', 'os', 'domain']),
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'fqdn',
                            'matcher_attribute_value': module_host.name
                        },
                        'Value': override_value
                    },
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'domain',
                            'matcher_attribute_value': domain.name
                        },
                        'Value': override_value2
                    }
                ]
            }
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values[
            'parameter']['matchers']['table'][0]['Value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value'] == override_value2
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == override_value
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.prioritize_attribute_order.order': '\n'.join(
                    ['domain', 'hostgroup', 'os', 'fqdn']),
            }
        )
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == override_value2


@tier2
def test_positive_create_matcher_merge_override(
        session, sc_params_list, module_host, domain):
    """Merge the values of all the associated matchers.

    :id: adf9823b-714d-490f-8dfa-f4f9cc888be1

    :steps:
        1.  Check the Override checkbox.
        2.  Set some default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
            Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes if any.
            Note - The fqdn/host should have this attributes.
        6.  Select 'Merge overrides' checkbox.
        7.  Submit the change.
        8.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values merged from all the associated
            matchers.
        2.  The YAML output doesn't have the default value of parameter.
        3.  Duplicate values in YAML output if any are displayed.

    :CaseLevel: Integration

    :CaseImportance: Critical
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
                'parameter.key_type': 'array',
                'parameter.prioritize_attribute_order.merge_overrides': True,
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'fqdn',
                            'matcher_attribute_value': module_host.name
                        },
                        'Value': override_value
                    },
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'domain',
                            'matcher_attribute_value': domain.name
                        },
                        'Value': override_value2
                    }
                ]
            }
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values[
            'parameter']['matchers']['table'][0]['Value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value'] == override_value2
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == [80, 90, 90, 100]


@tier2
def test_negative_create_matcher_merge_override(
        session, sc_params_list, module_host):
    """Attempt to merge the values from non associated matchers.

    :id: 46326bd6-e51f-48e7-87b2-6d65ad602af9

    :steps:
        1.  Check the Override checkbox.
        2.  Set some default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
            Note - The fqdn/host should not have this attribute.
        5.  Create more matchers for some more attributes if any.
            Note - The fqdn/host should not have this attributes.
        6.  Select 'Merge overrides' checkbox.
        7.  Submit the change.
        8.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values only for fqdn.
        2.  The YAML output doesn't have the values for attribute
            which are not associated to host.
        3.  The YAML output doesn't have the default value of parameter.

    :CaseLevel: Integration

    :CaseImportance: Critical
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
                'parameter.key_type': 'array',
                'parameter.prioritize_attribute_order.merge_overrides': True,
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'fqdn',
                            'matcher_attribute_value': module_host.name
                        },
                        'Value': override_value
                    },
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'os',
                            'matcher_attribute_value': 'rhel2'
                        },
                        'Value': override_value2
                    }
                ]
            }
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values[
            'parameter']['matchers']['table'][0]['Value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value'] == override_value2
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == [80, 90]


@tier2
def test_positive_create_matcher_merge_default(
        session, sc_params_list, module_host, domain):
    """Merge the values of all the associated matchers + default value.

    :id: b79ce9fd-2497-4f6e-85cc-957077c4f097

    :steps:
        1.  Check the Override checkbox.
        2.  Set some default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
            Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes if any.
            Note - The fqdn/host should have this attributes.
        6.  Select 'Merge overrides' checkbox.
        7.  Select 'Merge default' checkbox.
        8.  Submit the change.
        9.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values merged from all
            the associated matchers.
        2.  The YAML output has the default value of parameter.
        3.  Duplicate values in YAML output if any are displayed.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    sc_param = sc_params_list.pop()
    override_value = '[80,90]'
    override_value2 = '[90,100]'
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.default_value': '[example]',
                'parameter.key_type': 'array',
                'parameter.prioritize_attribute_order.merge_overrides': True,
                'parameter.prioritize_attribute_order.merge_default': True,
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'fqdn',
                            'matcher_attribute_value': module_host.name
                        },
                        'Value': override_value
                    },
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'domain',
                            'matcher_attribute_value': domain.name
                        },
                        'Value': override_value2
                    }
                ]
            }
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values[
            'parameter']['matchers']['table'][0]['Value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value'] == override_value2
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == ['example', 80, 90, 90, 100]


@tier2
def test_negative_create_matcher_merge_default(
        session, sc_params_list, module_host, domain):
    """Empty default value is not shown in merged values.

    :id: b9c46949-34ea-4edd-ac3f-53708bf7885d

    :steps:
        1.  Check the Override checkbox.
        2.  Set empty default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
            Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes if any.
            Note - The fqdn/host should have this attributes.
        6.  Select 'Merge overrides' checkbox.
        7.  Select 'Merge default' checkbox.
        8.  Submit the change.
        9.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values merged from all
            the associated matchers.
        2.  The YAML output doesn't have the empty default value of
            parameter.
        3.  Duplicate values in YAML output if any are displayed.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    sc_param = sc_params_list.pop()
    override_value = '[80,90]'
    override_value2 = '[90,100]'
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.default_value': '[]',
                'parameter.key_type': 'array',
                'parameter.prioritize_attribute_order.merge_overrides': True,
                'parameter.prioritize_attribute_order.merge_default': True,
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'fqdn',
                            'matcher_attribute_value': module_host.name
                        },
                        'Value': override_value
                    },
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'domain',
                            'matcher_attribute_value': domain.name
                        },
                        'Value': override_value2
                    }
                ]
            }
        )
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == [80, 90, 90, 100]


@tier2
def test_positive_create_matcher_avoid_duplicate(
        session, sc_params_list, module_host, domain):
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
                'parameter.key_type': 'array',
                'parameter.prioritize_attribute_order.merge_overrides': True,
                'parameter.prioritize_attribute_order.merge_default': True,
                'parameter.prioritize_attribute_order.avoid_duplicates': True,
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'fqdn',
                            'matcher_attribute_value': module_host.name
                        },
                        'Value': override_value
                    },
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'domain',
                            'matcher_attribute_value': domain.name
                        },
                        'Value': override_value2
                    }
                ]
            }
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values[
            'parameter']['matchers']['table'][0]['Value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value'] == override_value2
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == [20, 80, 90, 100]


@tier2
def test_negative_create_matcher_avoid_duplicate(
        session, sc_params_list, module_host, domain):
    """Duplicates not removed as they were not really present.

    :id: f7a34928-c3a3-4b85-907b-f95c26240652

    :steps:
        1.  Check the Override checkbox.
        2.  Set some default Value of array type.
        3.  Create first matcher for attribute fqdn with some value.
        4.  Create second matcher for other attribute with other value than
            fqdn matcher and default value.
            Note - The fqdn/host should have this attribute.
        5.  Select 'Merge overrides' checkbox.
        6.  Select 'Merge default' checkbox.
        7.  Select 'Avoid Duplicates' checkbox.
        8.  Submit the change.
        9.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values merged from all matchers.
        2.  The YAML output has the default value of parameter.
        3.  No value removed as duplicate value.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    sc_param = sc_params_list.pop()
    override_value = '[70,80]'
    override_value2 = '[90,100]'
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.default_value': '[20]',
                'parameter.key_type': 'array',
                'parameter.prioritize_attribute_order.merge_overrides': True,
                'parameter.prioritize_attribute_order.merge_default': True,
                'parameter.prioritize_attribute_order.avoid_duplicates': True,
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'fqdn',
                            'matcher_attribute_value': module_host.name
                        },
                        'Value': override_value
                    },
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'domain',
                            'matcher_attribute_value': domain.name
                        },
                        'Value': override_value2
                    }
                ]
            }
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values[
            'parameter']['matchers']['table'][0]['Value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value'] == override_value2
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == [20, 70, 80, 90, 100]


@tier2
def test_positive_view_yaml_output_after_resubmit_array_type(
        session, sc_params_list, module_host, domain):
    """Validate yaml output for smart class parameter that opened few times
    in a row. Such output should be the same in case you submit form
    without any changes to the default value of the parameter

    :id: 55242e56-58ed-4957-b118-8de3be7402e3

    :customerscenario: true

    :steps:
        1.  Check the Override checkbox.
        2.  Set array key type.
        3.  Set default value to some host properties.
        4.  Submit the change.
        5.  Go to YAML output of associated host.
        6.  Open smart class parameter for edit, but don't change any value
        7.  Submit form
        8.  Go to YAML output of associated host.

    :expectedresults: The YAML output has same values before and after
        second edit.

    :BZ: 1241249

    :CaseLevel: Integration
    """
    sc_param = sc_params_list.pop()
    initial_value = "['<%= @host.domain %>', '<%= @host.mac %>']"
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.default_value': initial_value,
                'parameter.key_type': 'array',
            }
        )
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == [domain.name, module_host.mac]
        # That update operation will change nothing, but submit the same form
        session.sc_parameter.update(
            sc_param.parameter, {'parameter.override': True})
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == [domain.name, module_host.mac]


@tier2
def test_positive_view_yaml_output_after_resubmit_yaml_type(
        session, sc_params_list, module_host, domain):
    """Validate yaml output for smart class parameter that opened few times
    in a row. Such output should be the same in case you submit form
    without any changes to the default value of the parameter

    :id: 7cdb0bf2-9732-4d40-941f-d3a3f3fa7612

    :steps:
        1.  Check the Override checkbox.
        2.  Set yaml key type.
        3.  Set default value to some host properties.
        4.  Submit the change.
        5.  Go to YAML output of associated host.
        6.  Open smart class parameter for edit, but don't change any value
        7.  Submit form
        8.  Go to YAML output of associated host.

    :expectedresults: The YAML output has same values before and after
        second edit.

    :BZ: 1241249

    :CaseLevel: Integration
    """
    sc_param = sc_params_list.pop()
    initial_value = '- <%= @host.domain %>'
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.default_value': initial_value,
                'parameter.key_type': 'yaml',
            }
        )
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == [domain.name]
        # That update operation will change nothing, but submit the same form
        session.sc_parameter.update(
            sc_param.parameter, {'parameter.override': True})
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['classes'][PM_NAME][sc_param.parameter]
        assert output_scp == [domain.name]
