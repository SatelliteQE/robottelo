# -*- encoding: utf-8 -*-
"""Test class for Puppet Smart Variables

:Requirement: Variables

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import yaml
from nailgun import entities

from robottelo.api.utils import publish_puppet_module
from robottelo.constants import CUSTOM_PUPPET_REPO, DEFAULT_LOC, ENVIRONMENT
from robottelo.datafactory import gen_string
from robottelo.decorators import tier2, upgrade, fixture
from robottelo.helpers import is_open

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
def test_positive_create_matcher_attribute_priority_override_from_attribute(
        session, puppet_class, module_host, domain):
    """Matcher Value set on Attribute Priority for Host - alternate
    priority. Override from attribute

    :id: 65144295-f0ca-4bd0-ae01-96c50ca829fe

    :steps:

        1.  Create variable with some default value.
        2.  Set some attribute(other than fqdn) as top priority attribute.
            Note - The fqdn/host should have this attribute.
        3.  Make priority list longer than 255 chars (bz 1458817)
        4.  Create first matcher for fqdn with valid details.
        5.  Create second matcher for attribute of step 2 with valid
            details.
        6.  Submit the change.
        7.  Go to YAML output of associated host.
        8.  Then, from host edit the variable value.

    :expectedresults:

        1.  The YAML output has the value only for step 4 matcher.
        2.  The YAML output doesn't have value for fqdn/host matcher.
        3.  Matcher value in variable is updated from the host.

    :BZ: 1458817

    :CaseLevel: Integration
    """
    variable_name = gen_string('alpha')
    override_value = gen_string('alphanumeric')
    override_value2 = gen_string('alphanumeric')
    fake_order_items = [gen_string('alpha').lower() for _ in range(60)]
    variable_new_value = gen_string('numeric').lstrip('0')

    with session:
        session.smartvariable.create({
            'variable.key': variable_name,
            'variable.puppet_class': puppet_class.name,
            'variable.default_value': gen_string('alpha'),
            'variable.prioritize_attribute_order.order': '\n'.join(
                ['domain', 'hostgroup', 'os', 'fqdn'] + fake_order_items),
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
        assert session.smartvariable.search(variable_name)[0]['Variable'] == variable_name
        output = yaml.load(session.host.read_yaml_output(module_host.name))
        output_scp = output['parameters'][variable_name]
        assert output_scp == override_value2

        # update matcher from attribute
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            variable_name,
            dict(value=variable_new_value)
        )
        host_smart_variable_value = session.host.get_puppet_class_parameter_value(
            module_host.name, variable_name)
        assert host_smart_variable_value['value'] == variable_new_value
        values = session.smartvariable.read(variable_name)
        assert len(values['variable']['matchers']['table']) == 2
        property_matcher = values['variable']['matchers']['table'][0]
        assert property_matcher['Attribute type']['matcher_attribute_type'] == 'domain'
        hostname = module_host.name.split(".")[1]
        assert property_matcher['Attribute type']['matcher_attribute_value'] == hostname
        assert property_matcher['Value']['value'] == override_value2


@tier2
@upgrade
def test_positive_create_matcher_prioritize_and_delete(session, puppet_class, module_host, domain):
    """Merge the values of all the associated matchers, remove duplicates.
    Delete smart variable.

    :id: 75fc514f-70dd-4cc1-8069-221e9edda89a

    :BZ: 1734022, 1745938

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
        9.  Then delete the smart variable

    :expectedresults:

        1.  The YAML output has the values merged from all the associated
            matchers.
        2.  The YAML output has the default value of variable.
        3.  Duplicate values in YAML output are removed / not displayed.
        4.  In Host-> variables tab, the smart variable should be displayed
            with its respective puppet class.
        5. The smart Variable is deleted successfully.
        6. In YAML output of associated Host, the variable should be
           removed.
        7. In Host-> variables tab, the smart variable should be removed.

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
        host_values = session.host.read(module_host.name, widget_names='parameters')
        smart_variable = next((
            item
            for item in host_values['parameters']['puppet_class_parameters']
            if item['Name'] == name
        ))
        if not is_open('BZ:1745938'):
            assert smart_variable['Puppet Class'] == puppet_class.name
            assert smart_variable['Value']['value'] == [20, 80, 90, 100]
        # Delete smart variable
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
def test_positive_impact_update_delete_attribute(session, module_host, puppet_env, puppet_class):
    """Impact on variable after updating associated attribute.
    Deleting an attribute.

    :id: 26ce3c25-0deb-415d-a2f5-0eacaf354f92

    :steps:

        1.  Create a variable with matcher for some attribute.
        2.  From host, override the variable value.
        3.  Delete the attribute.
        4.  Recreate the attribute with same name as earlier.

    :expectedresults:

        1.  The host is saved with changes.
        2.  The matcher for deleted attribute removed from variable.
        3.  On recreating attribute, the matcher should not reappear in
            variable.

    :CaseLevel: Integration
    """
    variable_name = gen_string('alpha')
    variable_value = gen_string('alpha')
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

        # update
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
        assert values[0]['Number of Overrides'] == '2'

        # delete
        hostgroup.delete()
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        assert values[0]['Number of Overrides'] == '1'
        hostgroup = entities.HostGroup(name=hostgroup_name, environment=puppet_env).create()
        hostgroup.add_puppetclass(data={'puppetclass_id': puppet_class.id})
        values = session.smartvariable.search(variable_name)
        assert values[0]['Variable'] == variable_name
        assert values[0]['Number of Overrides'] == '1'


@tier2
def test_positive_hidden_value_in_attribute(session, module_host, puppet_class):
    """Hide, update and unhide the hidden default value of variable in attribute.

    :id: 2f506d47-aed5-45ad-a6fb-133ece18eb14

    :steps:

        1.  Create a variable.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate variable on host/hostgroup.
        6.  In host, update the variable value.
        7.  Unhide the variable

    :expectedresults:

        1.  In host/hostgroup, the variable value is updated.
        2.  The variable Value displayed as hidden.
        3.  In variable, new matcher created for fqdn/hostgroup.
        4.  And the value shown hidden
        5.  After unhide, in host/hostgroup, the variable value shown
            in unhidden state.
        6.  The button for hiding the value is displayed and accessible.
        7.  The button for overriding the value is displayed and
            accessible.
        8.  In variable, the default value is still hidden.

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
        # Update
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
        # Unhide
        session.host.set_puppet_class_parameter_value(
            module_host.name,
            variable_name,
            dict(overridden=True, hidden=False)
        )
        values = session.smartvariable.read(variable_name)
        assert values['variable']['key'] == variable_name
        assert values['variable']['default_value']['hidden'] is True
