# -*- encoding: utf-8 -*-
"""Test class for Puppet Smart Variables

:Requirement: Variables

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
import yaml
from nailgun import entities

from robottelo.api.utils import publish_puppet_module
from robottelo.constants import CUSTOM_PUPPET_REPO, DEFAULT_LOC, ENVIRONMENT
from robottelo.datafactory import gen_string
from robottelo.decorators import tier2, upgrade, fixture

PUPPET_MODULES = [
    {'author': 'robottelo', 'name': 'ui_test_variables'}]


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
    # We need to have at least one variable created to unblock WebUI for Smart
    # Variable interface page
    if len(entities.SmartVariable(
            puppetclass=puppet_class_entity).search({'puppetclass'})) == 0:
        entities.SmartVariable(puppetclass=puppet_class_entity).create()
    return puppet_class_entity


@fixture(scope='module')
def puppet_subclasses(puppet_env):
    return entities.PuppetClass().search(query={
        'search': u'name ~ "{0}::" and environment = "{1}"'.format(
            PUPPET_MODULES[0]['name'], puppet_env.name)
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
@upgrade
def test_positive_create_with_host(session, puppet_class, module_host):
    """Creates a Smart Variable and associate it with host.

    :id: 4a8589bf-7b11-48e8-a25d-984bea2ba676

    :steps: Creates a smart variable with valid name and default value.

    :expectedresults:

        1. The smart Variable is created successfully.
        2. In YAML output of associated host, the variable with name and
           its default value is displayed.
        3. In Host-> variables tab, the smart variable should be displayed
           with its respective puppet class.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    value = gen_string('alpha')
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': value,
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['parameters'][name]
        assert output_scp == value
        host_values = session.host.read(module_host.name)
        smart_variable = next((
            item
            for item in host_values['parameters']['puppet_class_parameters']
            if item['Name'] == name
        ))
        assert smart_variable['Puppet Class'] == puppet_class.name
        assert smart_variable['Value']['value'] == value


@tier2
def test_positive_create_matcher(session, puppet_class, module_host):
    """Create a Smart Variable with matcher.

    :id: 42113584-d2db-4b91-8775-06bffee36be4

    :steps:

        1. Create a smart Variable with valid name and default value.
        2. Create a matcher for Host attribute with valid value.

    :expectedresults:

        1. The smart Variable with matcher is created successfully.
        2. In YAML output, the variable name with overrided value for host
           is displayed.
        3. In Host-> variables tab, the variable name with overrided value
           for host is displayed.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    default_value = gen_string('alpha')
    override_value = gen_string('alphanumeric')
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': default_value,
            'variable.matchers': [
                {
                    'Attribute type': {
                        'matcher_attribute_type': 'fqdn',
                        'matcher_attribute_value': module_host.name
                    },
                    'Value': override_value
                }
            ]
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['parameters'][name]
        assert output_scp == override_value
        host_values = session.host.read(module_host.name)
        smart_variable = next((
            item
            for item in host_values['parameters']['puppet_class_parameters']
            if item['Name'] == name
        ))
        assert smart_variable['Value']['value'] == override_value


@tier2
def test_positive_create_matcher_attribute_priority(
        session, puppet_class, module_host, domain):
    """Matcher Value set on Attribute Priority for Host - alternate
    priority.

    :id: 65144295-f0ca-4bd0-ae01-96c50ca829fe

    :steps:

        1.  Create variable with some default value.
        2.  Set some attribute(other than fqdn) as top priority attribute.
            Note - The fqdn/host should have this attribute.
        3.  Create first matcher for fqdn with valid details.
        4.  Create second matcher for attribute of step 2 with valid
            details.
        5.  Submit the change.
        6.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the value only for step 4 matcher.
        2.  The YAML output doesn't have value for fqdn/host matcher.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    override_value = gen_string('alphanumeric')
    override_value2 = gen_string('alphanumeric')
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': gen_string('alpha'),
            'variable.prioritize_attribute_order.order': '\n'.join(
                ['domain', 'hostgroup', 'os', 'fqdn']),
            'variable.matchers': [
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
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['parameters'][name]
        assert output_scp == override_value2


@tier2
@upgrade
def test_positive_create_with_long_priority_list(session, puppet_class):
    """Smart variable priority order list can contain more than 255 character inside of it.

    :id: 440923cb-9d81-40c8-9d81-7bf22f503cf5

    :customerscenario: true

    :steps:
        1.  Create variable with some default value.
        2.  Set long priority order list

    :expectedresults: Smart variable is created successfully and has proper priority list.

    :BZ: 1458817

    :CaseImportance: Medium
    """
    name = gen_string('alpha')
    order_value = '\n'.join([gen_string('alpha').lower() for _ in range(60)])
    assert len(order_value) > 255
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': gen_string('alpha'),
            'variable.prioritize_attribute_order.order': order_value,
        })
        values = session.smartvariable.read(name)
        assert values['variable']['prioritize_attribute_order']['order'] == order_value


@tier2
@upgrade
def test_positive_create_matcher_merge_override(session, puppet_class, module_host, domain):
    """Merge the values of all the associated matchers.

    :id: b9c9b1c7-ff9a-4080-aeee-3b61b5414332

    :steps:

        1.  Create variable with some default value.
        2.  Create first matcher for attribute fqdn with valid details.
        3.  Create second matcher for other attribute with valid details.
            Note - The fqdn/host should have this attribute.
        4.  Select 'Merge overrides' checkbox.
        5.  Submit the change.
        6.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values merged from all the associated
            matchers.
        2.  The YAML output doesn't have the default value of variable.
        3.  Duplicate values in YAML output if any are displayed.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    override_value = '[80, 90]'
    override_value2 = '[90, 100]'
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': '[20]',
            'variable.parameter_type': 'array',
            'variable.prioritize_attribute_order.merge_overrides': True,
            'variable.matchers': [
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
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        assert output['parameters'][name] == [80, 90, 90, 100]


@tier2
@upgrade
def test_negative_create_matcher_merge_override(session, puppet_class, module_host):
    """Attempt to merge the values from non associated matchers.

    :id: 3cc2a7b3-7b46-4c8c-b719-79c004ae04c6

    :steps:

        1.  Create variable with some default value.
        2.  Create first matcher for attribute fqdn with valid details.
        3.  Create second matcher for other attribute with valid details.
            Note - The fqdn/host should not have this attribute.
        4.  Select 'Merge overrides' checkbox.
        5.  Submit the change.
        6.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values only for fqdn.
        2.  The YAML output doesn't have the values for attribute which are
            not associated to host.
        3.  The YAML output doesn't have the default value of variable.
        4.  Duplicate values in YAML output if any are displayed.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    override_value = '[80, 90]'
    override_value2 = '[90, 100]'
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': '[20]',
            'variable.parameter_type': 'array',
            'variable.prioritize_attribute_order.merge_overrides': True,
            'variable.matchers': [
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
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        assert output['parameters'][name] == [80, 90]


@tier2
@upgrade
def test_positive_create_matcher_merge_default(session, puppet_class, module_host, domain):
    """Merge the values of all the associated matchers + default value.

    :id: 21d8fde8-0844-4384-b86a-30547c82b221

    :steps:

        1.  Create variable with some default value.
        2.  Create first matcher for attribute fqdn with valid details.
        3.  Create second matcher for other attribute with valid details.
            Note - The fqdn/host should have this attribute.
        4.  Select 'Merge overrides' checkbox.
        5.  Select 'Merge default' checkbox.
        6.  Submit the change.
        7.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values merged from all the associated
            matchers.
        2.  The YAML output has the default value of variable.
        3.  Duplicate values in YAML output if any are displayed.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    override_value = '[80, 90]'
    override_value2 = '[90, 100]'
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': '[test]',
            'variable.parameter_type': 'array',
            'variable.prioritize_attribute_order.merge_overrides': True,
            'variable.prioritize_attribute_order.merge_default': True,
            'variable.matchers': [
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
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        assert output['parameters'][name] == ['test', 80, 90, 90, 100]


@tier2
def test_negative_create_matcher_merge_default(session, puppet_class, module_host, domain):
    """Empty default value is not shown in merged values.

    :id: 98f8fe63-d125-4d27-a15a-2550c9e5f0ff

    :steps:

        1.  Create variable with empty default value.
        2.  Create first matcher for attribute fqdn with valid details.
        3.  Create second matcher for other attribute with valid details.
            Note - The fqdn/host should have this attribute.
        4.  Select 'Merge overrides' checkbox.
        5.  Select 'Merge default' checkbox.
        6.  Submit the change.
        7.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values merged from all the associated
            matchers.
        2.  The YAML output doesn't have the empty default value of
            variable.
        3.  Duplicate values in YAML output if any are displayed.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    override_value = '[80, 90]'
    override_value2 = '[90, 100]'
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': '[]',
            'variable.parameter_type': 'array',
            'variable.prioritize_attribute_order.merge_overrides': True,
            'variable.prioritize_attribute_order.merge_default': True,
            'variable.matchers': [
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
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        assert output['parameters'][name] == [80, 90, 90, 100]


@tier2
@upgrade
def test_positive_create_matcher_avoid_duplicate(session, puppet_class, module_host, domain):
    """Merge the values of all the associated matchers, remove duplicates.

    :id: 75fc514f-70dd-4cc1-8069-221e9edda89a

    :steps:

        1.  Create variable with type array and value.
        2.  Create first matcher for attribute fqdn with some value.
        3.  Create second matcher for other attribute with same value as
            fqdn matcher.
            Note - The fqdn/host should have this attribute.
        4.  Select 'Merge overrides' checkbox.
        5.  Select 'Merge default' checkbox.
        6.  Select 'Avoid Duplicates' checkbox.
        7.  Submit the change.
        8.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values merged from all the associated
            matchers.
        2.  The YAML output has the default value of variable.
        3.  Duplicate values in YAML output are removed / not displayed.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    override_value = '[80, 90]'
    override_value2 = '[90, 100]'
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': '[20]',
            'variable.parameter_type': 'array',
            'variable.prioritize_attribute_order.merge_overrides': True,
            'variable.prioritize_attribute_order.merge_default': True,
            'variable.prioritize_attribute_order.avoid_duplicates': True,
            'variable.matchers': [
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
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        assert output['parameters'][name] == [20, 80, 90, 100]


@tier2
def test_negative_create_matcher_avoid_duplicate(session, puppet_class, module_host, domain):
    """Duplicates not removed as they were not really present.

    :id: 050c7cef-eed6-4a61-b567-371f398647a2

    :steps:

        1.  Create variable with type array and value.
        2.  Create first matcher for attribute fqdn with some value.
        3.  Create second matcher for other attribute with other value than
            fqdn matcher and default value.
            Note - The fqdn/host should have this attribute.
        4.  Select 'Merge overrides' checkbox.
        5.  Select 'Merge default' checkbox.
        6.  Select 'Avoid Duplicates' checkbox.
        7.  Submit the change.
        8.  Go to YAML output of associated host.

    :expectedresults:

        1.  The YAML output has the values merged from all matchers.
        2.  The YAML output has the default value of variable.
        3.  No value removed as duplicate value.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    override_value = '[70, 80]'
    override_value2 = '[90, 100]'
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': '[20]',
            'variable.parameter_type': 'array',
            'variable.prioritize_attribute_order.merge_overrides': True,
            'variable.prioritize_attribute_order.merge_default': True,
            'variable.prioritize_attribute_order.avoid_duplicates': True,
            'variable.matchers': [
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
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        assert output['parameters'][name] == [20, 70, 80, 90, 100]


@tier2
@upgrade
def test_positive_delete(session, puppet_class, module_host):
    """Deletes a Smart Variable from Smart Variables Menu.

    :id: 19fedbdf-48a1-46a7-b184-615a0efd7b4e

    :steps: Deletes a smart Variable from Configure - Smart Variables menu.

    :expectedresults:

        1. The smart Variable is deleted successfully.
        2. In YAML output of associated Host, the variable should be
           removed.
        3. In Host-> variables tab, the smart variable should be removed.

    :CaseLevel: Integration
    """
    name = gen_string('alpha')
    value = gen_string('alpha')
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': value,
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        # Verify that that smart variable is present in YAML output
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        assert name in output['parameters']
        # Verify that smart variable is present on Host page
        host_values = session.host.read(module_host.name, 'parameters.puppet_class_parameters')
        smart_variables = [
            item
            for item in host_values['parameters']['puppet_class_parameters']
            if item['Name'] == name
        ]
        assert smart_variables
        session.smartvariable.delete(name)
        assert not session.smartvariable.search(name)
        # Verify that that smart variable is not present in YAML output
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        assert name not in output['parameters']
        # Verify that smart variable is not present on Host page
        host_values = session.host.read(module_host.name, 'parameters.puppet_class_parameters')
        smart_variables = [
            item
            for item in host_values['parameters']['puppet_class_parameters']
            if item['Name'] == name
        ]
        assert not smart_variables


@tier2
def test_positive_impact_delete_attribute(session, puppet_env, puppet_class):
    """Impact on variable after deleting associated attribute.

    :id: 26ce3c25-0deb-415d-a2f5-0eacaf354f92

    :steps:

        1.  Create a variable with matcher for some attribute.
        2.  Delete the attribute.
        3.  Recreate the attribute with same name as earlier.

    :expectedresults:

        1.  The matcher for deleted attribute removed from variable.
        2.  On recreating attribute, the matcher should not reappear in
            variable.

    :CaseLevel: Integration
    """
    variable_name = gen_string('alpha')
    hostgroup_name = gen_string('alpha')
    hostgroup = entities.HostGroup(name=hostgroup_name, environment=puppet_env).create()
    hostgroup.add_puppetclass(data={'puppetclass_id': puppet_class.id})
    with session:
        session.smartvariable.create({
            'variable.key': variable_name,
            'variable.puppet_class': puppet_class.name,
            'variable.matchers': [
                {
                    'Attribute type': {
                        'matcher_attribute_type': 'hostgroup',
                        'matcher_attribute_value': hostgroup_name
                    },
                    'Value': gen_string('alpha')
                },
            ]
        })
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        assert values[0]['Number of Overrides'] == '1'
        hostgroup.delete()
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        assert values[0]['Number of Overrides'] == '0'
        hostgroup = entities.HostGroup(name=hostgroup_name, environment=puppet_env).create()
        hostgroup.add_puppetclass(data={'puppetclass_id': puppet_class.id})
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        assert values[0]['Number of Overrides'] == '0'


@tier2
def test_positive_override_from_attribute(session, module_host, puppet_class):
    """Impact on variable on overriding the variable value from attribute.

    :id: 0d4a6b5f-09d8-4d64-ae4b-efa152815ea8

    :steps:

        1.  Create a variable.
        2.  From host/hostgroup, override the variable value.
        3.  Submit the changes.

    :expectedresults:

        1.  The host/hostgroup is saved with changes.

    :CaseLevel: Integration
    """
    variable_name = gen_string('alpha')
    variable_value = gen_string('alpha')
    with session:
        session.smartvariable.create({
            'variable.key': variable_name,
            'variable.puppet_class': puppet_class.name,
        })
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        assert values[0]['Number of Overrides'] == '0'
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            variable_name,
            dict(value=variable_value, overridden=True)
        )
        host_smart_variable_value = session.host.get_puppet_class_parameter_value(
            module_host.name, variable_name)
        assert host_smart_variable_value['value'] == variable_value
        assert host_smart_variable_value['overridden'] is True
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        assert values[0]['Number of Overrides'] == '1'


@tier2
def test_positive_override_default_value_from_attribute(session, module_host, puppet_class):
    """Override smart variable that has default value with a new value from
    attribute(host) page

    :id: a76dcb34-b005-4998-99e9-418b2e821a00

    :steps:

        1.  Create a variable with array type and default value
        2.  From host/hostgroup, override the variable value.
        3.  Submit the changes.

    :expectedresults:

        1.  The host/hostgroup is saved with changes and variable value has
            been changed
        2.  Smart variable should be treated as overridden

    :BZ: 1405118

    :CaseLevel: Integration
    """
    variable_name = gen_string('alpha')
    variable_default_value = '[20,30]'
    variable_new_value = '[90,100,120]'
    with session:
        session.smartvariable.create({
            'variable.key': variable_name,
            'variable.puppet_class': puppet_class.name,
            'variable.parameter_type': 'array',
            'variable.default_value': variable_default_value,
        })
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        assert values[0]['Number of Overrides'] == '0'
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            variable_name,
            dict(value=variable_new_value, overridden=True)
        )
        host_smart_variable_value = session.host.get_puppet_class_parameter_value(
            module_host.name, variable_name)
        assert host_smart_variable_value['value'] == variable_new_value
        assert host_smart_variable_value['overridden'] is True
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        assert values[0]['Number of Overrides'] == '1'


@tier2
def test_negative_create_override_from_attribute(session, module_host, puppet_class):
    """No impact on variable on overriding the variable with invalid value
    from attribute.

    :id: 18071443-a511-49c4-9ca9-04c7594b831d

    :steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  From host/hostgroup, attempt to override the variable with some
            other key type of value.

    :expectedresults:

        1.  Error thrown for invalid type value.
        2.  No matcher for fqdn/hostgroup is created inside variable.

    :CaseLevel: Integration
    """
    variable_name = gen_string('alpha')
    variable_default_value = gen_string('numeric').lstrip('0')
    variable_new_value = gen_string('alpha')
    with session:
        session.smartvariable.create({
            'variable.key': variable_name,
            'variable.puppet_class': puppet_class.name,
            'variable.parameter_type': 'integer',
            'variable.default_value': variable_default_value,
        })
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        assert values[0]['Number of Overrides'] == '0'
        with pytest.raises(AssertionError) as context:
            session.host.set_puppet_class_parameter_value(
                module_host.name,
                variable_name,
                dict(value=variable_new_value, overridden=True)
            )
        assert 'Validation errors present on page' in str(context.value)
        session.host.search(module_host.name)
        host_smart_variable_value = session.host.get_puppet_class_parameter_value(
            module_host.name, variable_name)
        assert host_smart_variable_value['value'] == variable_default_value
        assert host_smart_variable_value['overridden'] is False
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        assert values[0]['Number of Overrides'] == '0'


@tier2
def test_positive_update_matcher_from_attribute(session, module_host, puppet_class):
    """Impact on variable on editing the variable value from attribute.

    :id: e98a8404-5e32-4d2e-af81-4339d214658a

    :steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  Create a matcher for fqdn/hostgroup with valid details.
        4.  From host/hostgroup, edit the variable value.
        5.  Submit the changes.

    :expectedresults:

        1.  The host/hostgroup is saved with changes.
        2.  Matcher value in variable is updated from fqdn/hostgroup.

    :CaseLevel: Integration
    """
    variable_name = gen_string('alpha')
    variable_value = gen_string('numeric').lstrip('0')
    variable_matcher_value = gen_string('numeric').lstrip('0')
    variable_new_value = gen_string('numeric').lstrip('0')
    with session:
        session.smartvariable.create({
            'variable.key': variable_name,
            'variable.puppet_class': puppet_class.name,
            'variable.parameter_type': 'integer',
            'variable.default_value': variable_value,
            'variable.matchers': [
                {
                    'Attribute type': {
                        'matcher_attribute_type': 'fqdn',
                        'matcher_attribute_value': module_host.name
                    },
                    'Value': variable_matcher_value
                },
            ]
        })
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        # note that we should not enforce override, the variable should already be displayed as
        # overridden
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            variable_name,
            dict(value=variable_new_value)
        )
        host_smart_variable_value = session.host.get_puppet_class_parameter_value(
            module_host.name, variable_name)
        assert host_smart_variable_value['value'] == variable_new_value
        values = session.smartvariable.read(variable_name)
        assert len(values['variable']['matchers']['table']) == 1
        property_matcher = values['variable']['matchers']['table'][0]
        assert property_matcher['Attribute type']['matcher_attribute_type'] == 'fqdn'
        assert property_matcher['Attribute type']['matcher_attribute_value'] == module_host.name
        assert property_matcher['Value']['value'] == variable_new_value


@tier2
def test_negative_update_matcher_from_attribute(session, module_host, puppet_class):
    """No impact on variable on editing the variable with invalid value
    from attribute.

    :id: bd4a2535-57dd-49a8-b8b5-c5e8de652aa7

    :steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  Create a matcher for fqdn/hostgroup with valid details.
        4.  From host/hostgroup, attempt to edit the variable with invalid
            value.

    :expectedresults:

        1.  Error thrown for invalid value.
        2.  Matcher value in variable is not updated from fqdn/hostgroup.

    :CaseLevel: Integration
    """
    variable_name = gen_string('alpha')
    variable_default_value = gen_string('numeric').lstrip('0')
    variable_matcher_value = gen_string('numeric').lstrip('0')
    variable_new_value = gen_string('alpha')
    with session:
        session.smartvariable.create({
            'variable.key': variable_name,
            'variable.puppet_class': puppet_class.name,
            'variable.parameter_type': 'integer',
            'variable.default_value': variable_default_value,
            'variable.matchers': [
                {
                    'Attribute type': {
                        'matcher_attribute_type': 'fqdn',
                        'matcher_attribute_value': module_host.name
                    },
                    'Value': variable_matcher_value
                },
            ]
        })
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        with pytest.raises(AssertionError) as context:
            # note that we should not enforce override, the variable should already be displayed as
            # overridden
            session.host.set_puppet_class_parameter_value(
                module_host.name,
                variable_name,
                dict(value=variable_new_value)
            )
        assert 'Validation errors present on page' in str(context.value)
        # assert that the host smart variable new value has not been assigned
        session.host.search(module_host.name)
        host_smart_variable_value = session.host.get_puppet_class_parameter_value(
            module_host.name, variable_name)
        assert host_smart_variable_value['value'] == variable_matcher_value
        # assert that the smart variable matcher value has not changed and new value has not been
        # assigned
        values = session.smartvariable.read(variable_name)
        assert len(values['variable']['matchers']['table']) == 1
        property_matcher = values['variable']['matchers']['table'][0]
        assert property_matcher['Attribute type']['matcher_attribute_type'] == 'fqdn'
        assert property_matcher['Attribute type']['matcher_attribute_value'] == module_host.name
        assert property_matcher['Value']['value'] == variable_matcher_value
        assert property_matcher['Value']['value'] != variable_new_value


@tier2
def test_positive_hide_default_value_in_attribute(session, module_host, puppet_class):
    """Hide the default value of variable in attribute.

    :id: 3b9661f9-f7f7-4dbe-8b08-1a712db6a83d

    :steps:

        1.  Create a variable.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate variable on host/hostgroup.
        6.  Submit the changes.

    :expectedresults:

        1.  In host/hostgroup, the variable value shown in hidden state.
        2.  The button for unhiding the value is displayed and accessible.
        3.  The button for overriding the value is displayed and
            accessible.

    :CaseLevel: Integration
    """
    variable_name = gen_string('alpha')
    variable_default_value = gen_string('alpha')
    variable_new_value = gen_string('alpha')
    with session:
        session.smartvariable.create({
            'variable.key': variable_name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': variable_default_value,
            'variable.hidden': True,
        })
        assert session.smartvariable.search(variable_name)[0]['Variable'] == variable_name
        host_smart_variable_value = session.host.get_puppet_class_parameter_value(
            module_host.name, variable_name)
        assert host_smart_variable_value['hidden'] is True
        assert host_smart_variable_value['overridden'] is False
        assert host_smart_variable_value['value'] == variable_default_value
        assert '***' in host_smart_variable_value['hidden_value']
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            variable_name,
            dict(value=variable_new_value, overridden=True, hidden=False)
        )
        host_smart_variable_value = session.host.get_puppet_class_parameter_value(
            module_host.name, variable_name)
        # the variable is defined as hidden and should be always hidden, even if we push un-hide
        # button in host, the unhide button in host is only to show the value, but should not
        # enforce the unhide rule.
        assert host_smart_variable_value['hidden'] is True
        assert host_smart_variable_value['overridden'] is True
        assert host_smart_variable_value['value'] == variable_new_value


@tier2
def test_positive_unhide_default_value_in_attribute(session, module_host, puppet_class):
    """Unhide the default value of variable in attribute.

    :id: 5d7c1eb2-3f98-4dfd-aac0-ff740b7f82ec

    :steps:

        1.  Create a variable.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate variable on host/hostgroup.
        6.  In host/hostgroup, Click Unhide button icon.

    :expectedresults:

        1.  In host/hostgroup, the variable value shown in unhidden state.
        2.  The button for hiding the value is displayed and accessible.
        3.  The button for overriding the value is displayed and
            accessible.
        4.  In variable, the default value is still hidden.

    :CaseLevel: Integration
    """
    variable_name = gen_string('alpha')
    variable_default_value = gen_string('alpha')
    with session:
        session.smartvariable.create({
            'variable.key': variable_name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': variable_default_value,
            'variable.hidden': True,
        })
        assert session.smartvariable.search(variable_name)[0]['Variable'] == variable_name
        host_smart_variable_value = session.host.get_puppet_class_parameter_value(
            module_host.name, variable_name)
        assert host_smart_variable_value['hidden'] is True
        assert host_smart_variable_value['overridden'] is False
        assert host_smart_variable_value['value'] == variable_default_value
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            variable_name,
            dict(overridden=True, hidden=False)
        )
        values = session.smartvariable.read(variable_name)
        assert values['variable']['key'] == variable_name
        assert values['variable']['default_value']['hidden'] is True


@tier2
def test_positive_update_hidden_value_in_attribute(session, module_host, puppet_class):
    """Update the hidden default value of variable in attribute.

    :id: 2f506d47-aed5-45ad-a6fb-133ece18eb14

    :steps:

        1.  Create a variable.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate variable on host/hostgroup.
        6.  In host/hostgroup, update the variable value.

    :expectedresults:

        1.  In host/hostgroup, the variable value is updated.
        2.  The variable Value displayed as hidden.
        3.  In variable, new matcher created for fqdn/hostgroup.
        4.  And the value shown hidden.

    :CaseLevel: Integration
    """
    variable_name = gen_string('alpha')
    variable_default_value = gen_string('alpha')
    host_override_value = gen_string('alpha')
    with session:
        session.smartvariable.create({
            'variable.key': variable_name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': variable_default_value,
            'variable.hidden': True,
        })
        assert session.smartvariable.search(variable_name)[0]['Variable'] == variable_name
        host_smart_variable_value = session.host.get_puppet_class_parameter_value(
            module_host.name, variable_name)
        assert host_smart_variable_value['hidden'] is True
        assert host_smart_variable_value['overridden'] is False
        assert host_smart_variable_value['value'] == variable_default_value
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            variable_name,
            dict(value=host_override_value, overridden=True, hidden=False)
        )
        host_smart_variable_value = session.host.get_puppet_class_parameter_value(
            module_host.name, variable_name)
        assert host_smart_variable_value['hidden'] is True
        assert host_smart_variable_value['overridden'] is True
        assert host_smart_variable_value['value'] == host_override_value
        values = session.smartvariable.read(variable_name)
        assert values['variable']['key'] == variable_name
        assert values['variable']['default_value']['value'] == variable_default_value
        assert values['variable']['default_value']['hidden'] is True
        host_matcher = [
            matcher
            for matcher in values['variable']['matchers']['table']
            if (matcher['Attribute type']['matcher_attribute_type'] == 'fqdn'
                and matcher['Attribute type']['matcher_attribute_value'] == module_host.name)
        ][0]
        assert host_matcher['Value']['value'] == host_override_value
        assert host_matcher['Value']['hidden'] is True
