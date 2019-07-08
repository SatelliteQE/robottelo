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
from airgun.session import Session
from nailgun import entities
from pytest import raises
from random import choice, uniform
from requests import HTTPError

from robottelo.api.utils import (
    create_role_permissions,
    delete_puppet_class,
    publish_puppet_module,
)
from robottelo.constants import CUSTOM_PUPPET_REPO, DEFAULT_LOC, ENVIRONMENT
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, run_in_one_thread, tier2
from robottelo.helpers import get_nailgun_config

PM_NAME = 'ui_test_classparameters'
PUPPET_MODULES = [
    {'author': 'robottelo', 'name': PM_NAME}]

pytestmark = [run_in_one_thread]


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    default_loc_id = entities.Location().search(
        query={'search': 'name="{}"'.format(DEFAULT_LOC)})[0].id
    return entities.Location(id=default_loc_id).read()


@fixture(scope='module')
def content_view(module_org):
    return publish_puppet_module(
        PUPPET_MODULES, CUSTOM_PUPPET_REPO, module_org)


@fixture(scope='module')
def puppet_env(content_view, module_org):
    return entities.Environment().search(
        query={'search': u'content_view="{0}" and organization_id={1}'.format(
            content_view.name, module_org.id)}
    )[0]


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
def module_host(
        module_org, module_loc, content_view, puppet_env, puppet_class):
    lce = entities.LifecycleEnvironment().search(
        query={
            'search': 'organization_id="{0}" and name="{1}"'.format(
                module_org.id, ENVIRONMENT)
        })[0]
    host = entities.Host(
        organization=module_org,
        location=module_loc,
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
def test_positive_end_to_end(session, puppet_class, sc_params_list):
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
        {
            u'sc_type': 'string',
            u'value': gen_string('alphanumeric'),
        },
        {
            u'sc_type': 'boolean',
            u'value': choice(['true', 'false']),
        },
        {
            u'sc_type': 'integer',
            u'value': gen_string('numeric', 5).lstrip('0'),
        },
        {
            u'sc_type': 'real',
            u'value': str(uniform(-1000, 1000)),
        },
        {
            u'sc_type': 'array',
            u'value': u'["{0}","{1}","{2}"]'.format(
                gen_string('alpha'),
                gen_string('numeric').lstrip('0'),
                gen_string('html'),
            ),
        },
        {
            u'sc_type': 'hash',
            u'value': '{0}: {1}'.format(
                gen_string('alpha'), gen_string('alpha')),
        },
        {
            u'sc_type': 'yaml',
            u'value': '--- {0}=>{1}'.format(
                gen_string('alpha'), gen_string('alpha')),
        },
        {
            u'sc_type': 'json',
            u'value': u'{{"{0}":"{1}","{2}":"{3}"}}'.format(
                gen_string('alpha'),
                gen_string('numeric').lstrip('0'),
                gen_string('alpha'),
                gen_string('alphanumeric')
            ),
        },
    ]
    with session:
        assert session.sc_parameter.search(
            sc_param.parameter)[0]['Parameter'] == sc_param.parameter
        for data in data_list:
            session.sc_parameter.update(
                sc_param.parameter,
                {
                    'parameter.override': True,
                    'parameter.parameter_type': data['sc_type'],
                    'parameter.default_value': data['value'],
                }
            )
            sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
            # Application is adding some data for yaml and hash types once
            # smart class parameter is updated
            if data['sc_type'] == 'yaml':
                data['value'] = '{}{}'.format(data['value'], '\n...\n')
            elif data['sc_type'] == 'hash':
                data['value'] = '{}{}'.format(data['value'], '\n')
            assert sc_parameter_values['parameter']['parameter_type'] == data['sc_type']
            assert sc_parameter_values['parameter']['default_value']['value'] == data['value']
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.description': desc,
                'parameter.puppet_class': puppet_class.name,
                'parameter.parameter_type': 'string',
                'parameter.default_value': validation_value,
                'parameter.optional_input_validators.validator_type': 'regexp',
                'parameter.optional_input_validators.validator_rule': '[0-9]',
                'parameter.prioritize_attribute_order.order': override_priority,
                'parameter.matchers': [
                    {
                        'Attribute type': {
                            'matcher_attribute_type': 'os',
                            'matcher_attribute_value': 'x86'
                        },
                        'Value': override_value
                    },
                ]
            }
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values['parameter']['description'] == desc
        assert sc_parameter_values['parameter']['default_value']['value'] == validation_value
        assert sc_parameter_values[
            'parameter']['optional_input_validators']['validator_type'] == 'regexp'
        assert sc_parameter_values[
            'parameter']['optional_input_validators']['validator_rule'] == '[0-9]'
        assert sc_parameter_values[
            'parameter']['prioritize_attribute_order']['order'] == override_priority
        assert sc_parameter_values[
            'parameter']['matchers']['table'][0]['Value']['value'] == override_value


@tier2
def test_positive_search_with_non_admin_user(test_name, sc_params_list):
    """Search for specific smart class parameter using non admin user

    :id: 79bd4071-1baa-44af-91dd-1e093445af29

    :expectedresults: Specified smart class parameter can be found in the
        system

    :BZ: 1391556

    :CaseLevel: Integration
    """
    sc_param = sc_params_list.pop()
    username = gen_string('alpha')
    password = gen_string('alpha')
    required_user_permissions = {
        'Puppetclass': [
            'view_puppetclasses',
        ],
        'PuppetclassLookupKey': [
            'view_external_parameters',
            'create_external_parameters',
            'edit_external_parameters',
            'destroy_external_parameters',
        ],
    }
    role = entities.Role().create()
    create_role_permissions(role, required_user_permissions)
    entities.User(
        login=username,
        password=password,
        role=[role],
        admin=False
    ).create()
    # assert that the user is not an admin one and cannot read the current
    # role info (note: view_roles is not in the required permissions)
    cfg = get_nailgun_config()
    cfg.auth = (username, password)
    with raises(HTTPError) as context:
        entities.Role(cfg, id=role.id).read()
    assert '403 Client Error: Forbidden' in str(context.value)
    with Session(test_name, user=username, password=password) as session:
        assert session.sc_parameter.search(
            sc_param.parameter)[0]['Parameter'] == sc_param.parameter


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
            'parameter']['matchers']['table'][0]['Value']['value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value']['value'] == override_value2
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
def test_positive_update_with_long_priority_list(session, sc_params_list):
    """Smart class parameter priority order list can contain more than 255
    character inside of it

    :id: f5e7847a-1f4b-455d-aa73-6b02774b6168

    :customerscenario: true

    :steps:
        1.  Check the Override checkbox.
        2.  Set some default Value.
        3.  Set long priority order list

    :expectedresults: Smart class parameter is updated successfully and has
        proper priority list

    :BZ: 1458817

    :CaseImportance: Medium

    :CaseLevel: Integration
    """
    sc_param = sc_params_list.pop()
    order_value = '\n'.join([gen_string('alpha').lower() for _ in range(60)])
    assert len(order_value) > 255
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.default_value': gen_string('alpha'),
                'parameter.prioritize_attribute_order.order': order_value,
            }
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values[
            'parameter']['prioritize_attribute_order']['order'] == order_value


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
                'parameter.parameter_type': 'array',
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
            'parameter']['matchers']['table'][0]['Value']['value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value']['value'] == override_value2
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
                'parameter.parameter_type': 'array',
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
            'parameter']['matchers']['table'][0]['Value']['value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value']['value'] == override_value2
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
                'parameter.parameter_type': 'array',
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
            'parameter']['matchers']['table'][0]['Value']['value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value']['value'] == override_value2
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
                'parameter.parameter_type': 'array',
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
                'parameter.parameter_type': 'array',
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
            'parameter']['matchers']['table'][0]['Value']['value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value']['value'] == override_value2
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
                'parameter.parameter_type': 'array',
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
            'parameter']['matchers']['table'][0]['Value']['value'] == override_value
        assert sc_parameter_values[
            'parameter']['matchers']['table'][1]['Value']['value'] == override_value2
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
                'parameter.parameter_type': 'array',
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
                'parameter.parameter_type': 'yaml',
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


@tier2
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
                            'matcher_attribute_value': module_host.name
                        },
                        'Value': override_value
                    },
                ]
            }
        )
        host_sc_parameter_value = session.host.get_puppet_class_parameter_value(
            module_host.name, sc_param.parameter)
        assert host_sc_parameter_value['hidden'] is False
        assert host_sc_parameter_value['overridden'] is True
        assert host_sc_parameter_value['value'] == override_value
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            sc_param.parameter,
            dict(value=new_override_value)
        )
        host_sc_parameter_value = session.host.get_puppet_class_parameter_value(
            module_host.name, sc_param.parameter)
        assert host_sc_parameter_value['value'] == new_override_value
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert len(sc_parameter_values['parameter']['matchers']['table']) == 1
        property_matcher = sc_parameter_values['parameter']['matchers']['table'][0]
        assert property_matcher['Attribute type']['matcher_attribute_type'] == 'fqdn'
        assert property_matcher['Attribute type']['matcher_attribute_value'] == module_host.name
        assert property_matcher['Value']['value'] == new_override_value


@tier2
def test_positive_impact_parameter_delete_attribute(
        session, sc_params_list, puppet_env, puppet_class):
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
    hostgroup = entities.HostGroup(name=hg_name, environment=puppet_env).create()
    hostgroup.add_puppetclass(data={'puppetclass_id': puppet_class.id})
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
                            'matcher_attribute_value': hg_name
                        },
                        'Value': matcher_value
                    },
                ]
            }
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert len(sc_parameter_values['parameter']['matchers']['table']) == 1
        assert sc_parameter_values[
            'parameter']['matchers']['table'][0]['Value']['value'] == matcher_value
        assert session.sc_parameter.search(
            sc_param.parameter)[0]['Number of Overrides'] == '1'
        hostgroup.delete()
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert len(sc_parameter_values['parameter']['matchers']['table']) == 0
        assert session.sc_parameter.search(
            sc_param.parameter)[0]['Number of Overrides'] == '0'
        hostgroup = entities.HostGroup(name=hg_name, environment=puppet_env).create()
        hostgroup.add_puppetclass(data={'puppetclass_id': puppet_class.id})
        assert session.sc_parameter.search(
            sc_param.parameter)[0]['Number of Overrides'] == '0'


@tier2
def test_positive_hide_default_value_in_attribute(session, sc_params_list, module_host):
    """Hide the default value of parameter in attribute.

    :id: a44d35df-877c-469b-b82c-e5f85e592e8d

    :steps:

        1.  Check the override checkbox for the parameter.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate parameter on host/hostgroup.

    :expectedresults:

        1.  In host/hostgroup, the parameter value shown in hidden state.
        2.  The button for unhiding the value is displayed and accessible.
        3.  The button for overriding the value is displayed and
            accessible.

    :CaseLevel: Integration
    """
    sc_param = sc_params_list.pop()
    param_default_value = gen_string('alpha')
    param_new_value = gen_string('alpha')
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.parameter_type': 'string',
                'parameter.default_value': param_default_value,
                'parameter.hidden': True,
            }
        )
        host_sc_parameter_value = session.host.get_puppet_class_parameter_value(
            module_host.name, sc_param.parameter)
        assert host_sc_parameter_value['hidden'] is True
        assert host_sc_parameter_value['overridden'] is False
        assert host_sc_parameter_value['value'] == param_default_value
        assert '***' in host_sc_parameter_value['hidden_value']
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            sc_param.parameter,
            dict(value=param_new_value, overridden=True, hidden=False)
        )
        host_sc_parameter_value = session.host.get_puppet_class_parameter_value(
            module_host.name, sc_param.parameter)
        # the variable is defined as hidden and should be always hidden, even if we push un-hide
        # button in host, the unhide button in host is only to show the value, but should not
        # enforce the unhide rule.
        assert host_sc_parameter_value['hidden'] is True
        assert host_sc_parameter_value['overridden'] is True
        assert host_sc_parameter_value['value'] == param_new_value


@tier2
def test_positive_unhide_default_value_in_attribute(session, sc_params_list, module_host):
    """Unhide the default value of parameter in attribute.

    :id: 76611ba0-e583-4c4b-b794-005a21240d26

    :steps:

        1.  Check the override checkbox for the parameter.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate parameter on host/hostgroup.
        6.  In host/hostgroup, Click Unhide button icon.

    :expectedresults:

        1.  In host/hostgroup, the parameter value shown in unhidden state.
        2.  The button for hiding the value is displayed and accessible.
        3.  The button for overriding the value is displayed and
            accessible.
        4.  In parameter, the default value is still hidden.

    :CaseLevel: Integration
    """
    sc_param = sc_params_list.pop()
    param_default_value = gen_string('alpha')
    with session:
        session.sc_parameter.update(
            sc_param.parameter,
            {
                'parameter.override': True,
                'parameter.parameter_type': 'string',
                'parameter.default_value': param_default_value,
                'parameter.hidden': True,
            }
        )
        host_sc_parameter_value = session.host.get_puppet_class_parameter_value(
            module_host.name, sc_param.parameter)
        assert host_sc_parameter_value['hidden'] is True
        assert host_sc_parameter_value['overridden'] is False
        assert host_sc_parameter_value['value'] == param_default_value
        assert '***' in host_sc_parameter_value['hidden_value']
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            sc_param.parameter,
            dict(overridden=True, hidden=False)
        )
        sc_parameter_values = session.sc_parameter.read(sc_param.parameter)
        assert sc_parameter_values['parameter']['key'] == sc_param.parameter
        assert sc_parameter_values['parameter']['default_value']['hidden'] is True


@tier2
def test_positive_update_hidden_value_in_attribute(session, sc_params_list, module_host):
    """Update the hidden default value of parameter in attribute.

    :id: c10c20bd-0284-4e5d-b789-fddd3b81b81b

    :steps:

        1.  Check the override checkbox for the parameter.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate parameter on host/hostgroup.
        6.  In host/hostgroup, update the parameter value.

    :expectedresults:

        1.  In host/hostgroup, the parameter value is updated.
        2.  The parameter Value displayed as hidden.
        3.  In parameter, new matcher created for fqdn/hostgroup.
        4.  And the value shown hidden.

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
            }
        )
        host_sc_parameter_value = session.host.get_puppet_class_parameter_value(
            module_host.name, sc_param.parameter)
        assert host_sc_parameter_value['hidden'] is True
        assert host_sc_parameter_value['overridden'] is False
        assert host_sc_parameter_value['value'] == param_default_value
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            sc_param.parameter,
            dict(value=host_override_value, overridden=True, hidden=False)
        )
        host_sc_parameter_value = session.host.get_puppet_class_parameter_value(
            module_host.name, sc_param.parameter)
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
            if (matcher['Attribute type']['matcher_attribute_type'] == 'fqdn'
                and matcher['Attribute type']['matcher_attribute_value'] == module_host.name)
        ][0]
        assert host_matcher['Value']['value'] == host_override_value
        assert host_matcher['Value']['hidden'] is True
