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
import yaml
from nailgun import entities

from robottelo.api.utils import publish_puppet_module
from robottelo.constants import CUSTOM_PUPPET_REPO, DEFAULT_LOC_ID, ENVIRONMENT
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2, upgrade

PUPPET_MODULES = [
    {'author': 'robottelo', 'name': 'ui_test_variables'}]


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location(id=DEFAULT_LOC_ID).read()


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


def test_positive_create(session, puppet_class):
    """Creates a Smart Variable using different names.

    :id: ee4a0e3c-9a41-4fe9-8730-faab663b9ed1

    :steps: Creates a smart variable with valid name

    :expectedresults: The smart variable is created successfully.

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    with session:
        session.smartvariable.create({
            'variable.key': name,
            'variable.puppet_class': puppet_class.name
        })
        assert session.smartvariable.search(name)[0]['Variable'] == name
        sv_values = session.smartvariable.read(name)
        assert sv_values['variable']['key'] == name


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
        assert smart_variable['Value'] == value


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
        assert smart_variable['Value'] == override_value


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
