# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Variables

:Requirement: Smart_Variables

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import json
from random import choice, uniform

import yaml
from fauxfactory import gen_integer, gen_string
from nailgun import entities
from requests import HTTPError

from robottelo.api.utils import publish_puppet_module
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import APITestCase


@filtered_datapoint
def valid_sc_variable_data():
    """Returns a list of valid smart class variable types and values"""
    return [
        {
            u'sc_type': 'string',
            u'value': choice(generate_strings_list()),
        },
        {
            u'sc_type': 'boolean',
            u'value': choice([True, False]),
        },
        {
            u'sc_type': 'integer',
            u'value': gen_integer(),
        },
        {
            u'sc_type': 'real',
            u'value': uniform(-1000, 1000),
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
            u'value': '{{ "{0}": "{1}" }}'.format(
                gen_string('alpha'), gen_string('alpha')),
        },
        {
            u'sc_type': 'yaml',
            u'value': '--- {0}=>{1} ...'.format(
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


@filtered_datapoint
def invalid_sc_variable_data():
    """Returns a list of invalid smart class variable type and values"""
    return [
        {
            u'sc_type': 'boolean',
            u'value': gen_string('alphanumeric'),
        },
        {
            u'sc_type': 'integer',
            u'value': gen_string('utf8'),
        },
        {
            u'sc_type': 'real',
            u'value': gen_string('alphanumeric'),
        },
        {
            u'sc_type': 'array',
            u'value': gen_string('alpha'),
        },
        {
            u'sc_type': 'hash',
            u'value': gen_string('alpha'),
        },
        {
            u'sc_type': 'yaml',
            u'value': '{{{0}:{1}}}'.format(
                gen_string('alpha'), gen_string('alpha')),
        },
        {
            u'sc_type': 'json',
            u'value': u'{{{0}:{1},{2}:{3}}}'.format(
                gen_string('alpha'),
                gen_string('numeric').lstrip('0'),
                gen_string('alpha'),
                gen_string('alphanumeric')
            ),
        }
    ]


class SmartVariablesTestCase(APITestCase):
    """Implements Smart Variables tests in API"""

    @classmethod
    def setUpClass(cls):
        """Import some parametrized puppet classes. This is required to make
        sure that we have data to be able to perform interactions with smart
        class variables.
        """
        super(SmartVariablesTestCase, cls).setUpClass()
        cls.puppet_modules = [
            {'author': 'robottelo', 'name': 'api_test_variables'},
        ]
        cls.org = entities.Organization().create()
        cv = publish_puppet_module(
            cls.puppet_modules, CUSTOM_PUPPET_REPO, cls.org)
        cls.env = entities.Environment().search(
            query={'search': u'content_view="{0}"'.format(cv.name)}
        )[0]
        # Find imported puppet class
        cls.puppet_class = entities.PuppetClass().search(query={
            'search': u'name = "{0}" and environment = "{1}"'.format(
                cls.puppet_modules[0]['name'], cls.env.name)
        })[0]
        # And all its subclasses
        cls.puppet_subclasses = entities.PuppetClass().search(query={
            'search': u'name ~ "{0}::" and environment = "{1}"'.format(
                cls.puppet_modules[0]['name'], cls.env.name)
        })

    # TearDown brakes parallel tests run as every test depends on the same
    # puppet class that will be removed during TearDown.
    # Uncomment for developing or debugging and do not forget to import
    # `robottelo.api.utils.delete_puppet_class`.
    #
    # @classmethod
    # def tearDownClass(cls):
    #     """Removes puppet class."""
    #     super(SmartVariablesTestCase, cls).tearDownClass()
    #     delete_puppet_class(cls.puppet_class.name)

    @run_only_on('sat')
    @tier1
    def test_positive_create(self):
        """Create a Smart Variable with valid name

        :id: 4cd20cca-d419-43f5-9734-e9ae1caae4cb

        :steps: Create a smart Variable with Valid name and valid default value

        :expectedresults: The smart Variable is created successfully

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                smart_variable = entities.SmartVariable(
                    puppetclass=self.puppet_class,
                    variable=name,
                ).create()
                self.assertEqual(smart_variable.variable, name)

    @run_only_on('sat')
    @tier1
    def test_negative_create(self):
        """Create a Smart Variable with invalid name

        :id: d92f8bdd-93de-49ba-85a3-685aac9eda0a

        :steps: Create a smart Variable with invalid name and valid default
            value

        :expectedresults: The smart Variable is not created

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name), self.assertRaises(HTTPError):
                entities.SmartVariable(
                    puppetclass=self.puppet_class,
                    variable=name,
                ).create()

    @run_only_on('sat')
    @tier1
    def test_positive_delete_smart_variable_by_id(self):
        """Delete a Smart Variable by id

        :id: 6d8354db-a028-4ae0-bcb6-87aa1cb9ec5d

        :steps: Delete a smart Variable by id

        :expectedresults: The smart Variable is deleted successfully

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class
        ).create()
        smart_variable.delete()
        with self.assertRaises(HTTPError) as context:
            smart_variable.read()
        self.assertRegexpMatches(
            context.exception.response.text,
            "Smart variable not found by id"
        )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1375857)
    @tier1
    def test_positive_update_variable_puppet_class(self):
        """Update Smart Variable's puppet class.

        :id: 2312cb28-c3b0-4fbc-84cf-b66f0c0c64f0

        :steps:
            1. Create a smart variable with valid name.
            2. Update the puppet class associated to the smart variable created
               in step1.

        :expectedresults: The variable is updated with new puppet class.

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
        ).create()
        self.assertEqual(smart_variable.puppetclass.id, self.puppet_class.id)
        new_puppet = entities.PuppetClass().search(query={
            'search': 'name="{0}"'.format(choice(self.puppet_subclasses).name)
        })[0]
        smart_variable.puppetclass = new_puppet
        updated_sv = smart_variable.update(['puppetclass'])
        self.assertEqual(updated_sv.puppetclass.id, new_puppet.id)

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update Smart Variable's name

        :id: b8214eaa-e276-4fc4-8381-fb0386cda6a5

        :steps:
            1. Create a smart variable with valid name.
            2. Update smart variable name created in step1.

        :expectedresults: The variable is updated with new name.

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
        ).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                smart_variable.variable = new_name
                smart_variable = smart_variable.update(['variable'])
                self.assertEqual(smart_variable.variable, new_name)

    @run_only_on('sat')
    @tier1
    def test_negative_duplicate_name_variable(self):
        """Create Smart Variable with an existing name.

        :id: c49ad14d-913f-4adc-8ebf-88493556c027

        :steps:
            1. Create a smart Variable with Valid name and default value.
            2. Attempt to create a variable with same name from same/other
               class.

        :expectedresults: The variable with same name are not allowed to create
            from any class.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        entities.SmartVariable(
            variable=name,
            puppetclass=self.puppet_class,
        ).create()
        with self.assertRaises(HTTPError) as context:
            entities.SmartVariable(
                variable=name,
                puppetclass=self.puppet_class,
            ).create()
        self.assertRegexpMatches(
            context.exception.response.text,
            "Key has already been taken"
        )

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_list_variables_by_host_id(self):
        """List all the variables associated to Host by host id

        :id: 4fc1f249-5da7-493b-a1d3-4ce7b625ad96

        :expectedresults: All variables listed for Host

        :CaseLevel: Integration
        """
        entities.SmartVariable(puppetclass=self.puppet_class).create()
        host = entities.Host(organization=self.org).create()
        self.env.location = [host.location]
        self.env.update()
        host.environment = self.env
        host.update(['environment'])
        host.add_puppetclass(data={'puppetclass_id': self.puppet_class.id})
        self.assertGreater(len(host.list_smart_variables()['results']), 0)

    @run_only_on('sat')
    @tier2
    def test_positive_list_variables_by_hostgroup_id(self):
        """List all the variables associated to HostGroup by hostgroup id

        :id: db6861cc-b390-45bc-8c7d-cf10f46aecb3

        :expectedresults: All variables listed for HostGroup

        :CaseLevel: Integration
        """
        entities.SmartVariable(puppetclass=self.puppet_class).create()
        hostgroup = entities.HostGroup().create()
        hostgroup.add_puppetclass(
            data={'puppetclass_id': self.puppet_class.id})
        self.assertGreater(len(hostgroup.list_smart_variables()['results']), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_list_variables_by_puppetclass_id(self):
        """List all the variables associated to puppet class by puppet class id

        :id: cd743329-b354-4ddc-ada0-3ddd774e2701

        :expectedresults: All variables listed for puppet class

        :CaseImportance: Critical
        """
        self.assertGreater(len(self.puppet_class.list_smart_variables()), 0)

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_create_variable_type(self):
        """Create variable for variable types - Valid Value

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: 4c8b4134-33c1-4f7f-83f9-a751c49ae2da

        :steps: Create a variable with all valid key types and default values

        :expectedresults: Variable created with all given types successfully

        :CaseImportance: Critical
        """
        for data in valid_sc_variable_data():
            with self.subTest(data):
                smart_variable = entities.SmartVariable(
                    puppetclass=self.puppet_class,
                    variable_type=data['sc_type'],
                    default_value=data['value'],
                ).create()
                self.assertEqual(smart_variable.variable_type, data['sc_type'])
                if data['sc_type'] in ('json', 'hash', 'array'):
                    self.assertEqual(
                        smart_variable.default_value, json.loads(data['value'])
                    )
                elif data['sc_type'] == 'yaml':
                    self.assertEqual(
                        smart_variable.default_value, yaml.load(data['value']))
                else:
                    self.assertEqual(
                        smart_variable.default_value, data['value'])

    @run_only_on('sat')
    @tier1
    def test_negative_create_variable_type(self):
        """Negative variable Update for variable types - Invalid Value

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: 9709d67c-682f-4e6c-8b8b-f02f6c2d3b71

        :steps: Create a variable with all valid key types and invalid default
            values

        :expectedresults: Variable is not created for invalid value

        :CaseImportance: Critical
        """
        for data in invalid_sc_variable_data():
            with self.subTest(data):
                with self.assertRaises(HTTPError) as context:
                    entities.SmartVariable(
                        puppetclass=self.puppet_class,
                        variable_type=data['sc_type'],
                        default_value=data['value'],
                    ).create()
                self.assertRegexpMatches(
                    context.exception.response.text,
                    "Default value is invalid"
                )

    @run_only_on('sat')
    @tier1
    def test_positive_create_matcher_empty_value(self):
        """Create matcher with empty value with string type

        :id: a90b5bcd-f76c-4663-bf41-2f96e7e15c0f

        :steps: Create a matcher for variable with empty value and type string

        :expectedresults: Matcher is created with empty value

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            variable_type='string',
            override_value_order='is_virtual',
        ).create()
        entities.OverrideValue(
            smart_variable=smart_variable,
            match='is_virtual=true',
            value='',
        ).create()
        smart_variable = smart_variable.read()
        self.assertEqual(
            smart_variable.override_values[0]['match'], 'is_virtual=true')
        self.assertEqual(
            smart_variable.override_values[0]['value'], '')

    @run_only_on('sat')
    @tier1
    def test_negative_create_matcher_empty_value(self):
        """Create matcher with empty value with type other than string

        :id: ad24999f-1bed-4abb-a01f-3cb485d67968

        :steps: Create a matcher for variable with empty value and type any
            other than string

        :expectedresults: Matcher is not created for empty value

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=gen_integer(),
            variable_type='integer',
            override_value_order='is_virtual',
        ).create()
        with self.assertRaises(HTTPError) as context:
            entities.OverrideValue(
                smart_variable=smart_variable,
                match='is_virtual=true',
                value='',
            ).create()
        self.assertEqual(len(smart_variable.read().override_values), 0)
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Value is invalid integer"
        )

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_match_value(self):
        """Attempt to create matcher with invalid match value.

        :id: 625e3221-237d-4440-ab71-6d98cff67713

        :steps: Create a matcher for variable with invalid match value

        :expectedresults: Matcher is not created

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
        ).create()
        with self.assertRaises(HTTPError) as context:
            entities.OverrideValue(
                smart_variable=smart_variable,
                match='invalid_value',
                value=gen_string('alpha'),
            ).create()
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Match is invalid"
        )

    @run_only_on('sat')
    @tier1
    def test_negative_create_default_value_with_regex(self):
        """Create variable with non matching regex validator

        :id: 0c80bd58-26aa-4c2a-a087-ed3b88b226a7

        :steps:
            1. Create variable with default value that doesn't matches the
               regex of step 2
            2. Validate this value with regexp validator type and rule

        :expectedresults: Variable is not created for non matching value with
            regex

        :CaseImportance: Critical
        """
        value = gen_string('alpha')
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=value,
        ).create()
        smart_variable.default_value = gen_string('alpha')
        smart_variable.validator_type = 'regexp'
        smart_variable.validator_rule = '[0-9]'
        with self.assertRaises(HTTPError) as context:
            smart_variable.update([
                'default_value', 'validator_type', 'validator_rule'
            ])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Default value is invalid"
        )
        self.assertEqual(smart_variable.read().default_value, value)

    @run_only_on('sat')
    @tier1
    def test_positive_create_default_value_with_regex(self):
        """Create variable with matching regex validator

        :id: aa9803b9-9a45-4ad8-b502-e0e32fc4b7d8

        :steps:
            1. Create variable with default value that matches the regex of
               step 2
            2. Validate this value with regex validator type and rule

        :expectedresults: Variable is created for matching value with regex

        :CaseImportance: Critical
        """
        value = gen_string('numeric')
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=gen_string('alpha'),
        ).create()
        smart_variable.default_value = value
        smart_variable.validator_type = 'regexp'
        smart_variable.validator_rule = '[0-9]'
        smart_variable.update([
            'default_value', 'validator_type', 'validator_rule'
        ])
        smart_variable = smart_variable.read()
        self.assertEqual(smart_variable.default_value, value)
        self.assertEqual(smart_variable.validator_type, 'regexp')
        self.assertEqual(smart_variable.validator_rule, '[0-9]')

    @run_only_on('sat')
    @tier1
    def test_negative_create_matcher_value_with_regex(self):
        """Create matcher with non matching regexp validator

        :id: 8a0f9251-7992-4d1e-bace-7e32637bf56f

        :steps:
            1. Create a matcher with value that doesn't matches the regex of
               step 2
            2. Validate this value with regex validator type and rule

        :expectedresults: Matcher is not created for non matching value with
            regexp

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=gen_string('numeric'),
            validator_type='regexp',
            validator_rule='[0-9]',
        ).create()
        with self.assertRaises(HTTPError) as context:
            entities.OverrideValue(
                smart_variable=smart_variable,
                match='domain=example.com',
                value=gen_string('alpha'),
            ).create()
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Value is invalid"
        )
        self.assertEqual(len(smart_variable.read().override_values), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_create_matcher_value_with_regex(self):
        """Create matcher with matching regex validator

        :id: 3ad09261-eb55-4758-b915-84006c9e527c

        :steps:
            1. Create a matcher with value that matches the regex of step 2
            2. Validate this value with regex validator type and rule

        :expectedresults: Matcher is created for matching value with regex

        :CaseImportance: Critical
        """
        value = gen_string('numeric')
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=gen_string('numeric'),
            validator_type='regexp',
            validator_rule='[0-9]',
        ).create()
        entities.OverrideValue(
            smart_variable=smart_variable,
            match='domain=example.com',
            value=value,
        ).create()
        smart_variable = smart_variable.read()
        self.assertEqual(smart_variable.validator_type, 'regexp')
        self.assertEqual(smart_variable.validator_rule, '[0-9]')
        self.assertEqual(
            smart_variable.override_values[0]['match'], 'domain=example.com')
        self.assertEqual(
            smart_variable.override_values[0]['value'], value)

    @run_only_on('sat')
    @tier1
    def test_negative_create_default_value_with_list(self):
        """Create variable with non matching list validator

        :id: cacb83a5-3e50-490b-b94f-a5d27f44ae12

        :steps:

            1. Create variable with default value that doesn't matches the list
               validator of step 2
            2. Validate this value with list validator type and rule

        :expectedresults: Variable is not created for non matching value with
            list validator

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError) as context:
            entities.SmartVariable(
                puppetclass=self.puppet_class,
                default_value=gen_string('alphanumeric'),
                validator_type='list',
                validator_rule='5, test',
            ).create()
        self.assertRegexpMatches(
            context.exception.response.text,
            r"Default value \w+ is not one of"
        )

    @run_only_on('sat')
    @tier1
    def test_positive_create_default_value_with_list(self):
        """Create variable with matching list validator

        :id: 6bc2caa0-1300-4751-8239-34b96517465b

        :steps:

            1. Create variable with default value that matches the list
               validator of step 2
            2. Validate this value with list validator type and rule

        :expectedresults: Variable is created for matching value with list

        :CaseImportance: Critical
        """
        # Generate list of values
        values_list = [
            gen_string('alpha'),
            gen_string('alphanumeric'),
            gen_integer(min_value=100),
            choice(['true', 'false']),
        ]
        # Generate string from list for validator_rule
        values_list_str = ", ".join(str(x) for x in values_list)
        value = choice(values_list)
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=value,
            validator_type='list',
            validator_rule=values_list_str,
        ).create()
        self.assertEqual(smart_variable.default_value, str(value))
        self.assertEqual(smart_variable.validator_type, 'list')
        self.assertEqual(smart_variable.validator_rule, values_list_str)

    @run_only_on('sat')
    @tier1
    def test_negative_create_matcher_value_with_list(self):
        """Create matcher with non matching list validator

        :id: 0aff0fdf-5a62-49dc-abe1-b727459d030a

        :steps:

            1. Create a matcher with value that doesn't matches the list
               validator of step 2
            2. Validate this value with list validator type and rule

        :expectedresults: Matcher is not created for non matching value with
            list validator

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value='example',
            validator_type='list',
            validator_rule='test, example, 30',
        ).create()
        with self.assertRaises(HTTPError) as context:
            entities.OverrideValue(
                smart_variable=smart_variable,
                match='domain=example.com',
                value='not_in_list',
            ).create()
        self.assertRegexpMatches(
            context.exception.response.text,
            r"Validation failed: Value \w+ is not one of"
        )
        self.assertEqual(len(smart_variable.read().override_values), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_create_matcher_value_with_list(self):
        """Create matcher with matching list validator

        :id: f5eda535-6623-4130-bea0-97faf350a6a6

        :steps:

            1. Create a matcher with value that matches the list validator of
               step 2
            2. Validate this value with list validator type and rule

        :expectedresults: Matcher is created for matching value with list
            validator

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value='example',
            validator_type='list',
            validator_rule='test, example, 30',
        ).create()
        entities.OverrideValue(
            smart_variable=smart_variable,
            match='domain=example.com',
            value=30,
        ).create()
        smart_variable = smart_variable.read()
        self.assertEqual(smart_variable.validator_type, 'list')
        self.assertEqual(smart_variable.validator_rule, 'test, example, 30')
        self.assertEqual(
            smart_variable.override_values[0]['match'], 'domain=example.com')
        self.assertEqual(
            smart_variable.override_values[0]['value'], '30')

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1375643)
    @tier1
    def test_negative_create_matcher_value_with_default_type(self):
        """Create matcher with non matching type of default value

        :id: 790c63d7-4e8a-4187-8566-3d85d57f9a4f

        :steps:

            1. Create variable with valid type and value
            2. Create a matcher with value that doesn't matches the default
               type

        :expectedresults: Matcher is not created for non matching the type of
            default value

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=True,
            variable_type='boolean',
        ).create()
        with self.assertRaises(HTTPError) as context:
            entities.OverrideValue(
                smart_variable=smart_variable,
                match='domain=example.com',
                value=50,
            ).create()
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Value is invalid"
        )
        self.assertEqual(smart_variable.read().default_value, True)

    @run_only_on('sat')
    @tier1
    def test_positive_create_matcher_value_with_default_type(self):
        """Create matcher with matching type of default value

        :id: 99057f05-62cb-4230-b16c-d96ca6a5ae91

        :steps:

            1. Create variable with valid type and value
            2. Create a matcher with value that matches the default value type

        :expectedresults: Matcher is created for matching the type of default
            value

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=True,
            variable_type='boolean',
            override_value_order='is_virtual',
        ).create()
        entities.OverrideValue(
            smart_variable=smart_variable,
            match='is_virtual=true',
            value=False,
        ).create()
        smart_variable = smart_variable.read()
        self.assertEqual(
            smart_variable.override_values[0]['match'], 'is_virtual=true')
        self.assertEqual(
            smart_variable.override_values[0]['value'], False)

    @run_only_on('sat')
    @tier1
    def test_negative_create_matcher_non_existing_attribute(self):
        """Create matcher for non existing attribute

        :id: 23b16e7f-0626-467e-b53b-35e1634cc30d

        :steps: Create matcher for non existing attribute

        :expectedresults: Matcher is not created for non existing attribute

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
        ).create()
        with self.assertRaises(HTTPError) as context:
            entities.OverrideValue(
                smart_variable=smart_variable,
                match='hostgroup=nonexistingHG',
                value=gen_string('alpha')
            ).create()
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Match hostgroup=nonexistingHG does not match "
            "an existing host group"
        )
        self.assertEqual(len(smart_variable.read().override_values), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_create_matcher(self):
        """Create matcher for attribute in variable

        :id: f0b3d51a-cf9a-4b43-9567-eb12cd973299

        :steps: Create a matcher with all valid values

        :expectedresults: The matcher has been created successfully

        :CaseImportance: Critical
        """
        value = gen_string('alpha')
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
        ).create()
        entities.OverrideValue(
            smart_variable=smart_variable,
            match='domain=example.com',
            value=value,
        ).create()
        smart_variable = smart_variable.read()
        self.assertEqual(
            smart_variable.override_values[0]['match'], 'domain=example.com')
        self.assertEqual(
            smart_variable.override_values[0]['value'], value)

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_variable_attribute_priority(self):
        """Variable value set on Attribute Priority for Host

        :id: 78474b5e-7a50-4de0-b22c-3413ac06d067

        :bz: 1362372

        :steps:

            1. Create variable with some valid value and type
            2. Set fqdn as top priority attribute
            3. Create first matcher for fqdn with valid details
            4. Create second matcher for some attribute with valid details Note
               - The FQDN/host should have this attribute
            5. Check ENC output of associated host.

        :expectedresults: The ENC output shows variable value of fqdn matcher
            only

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_variable_attribute_priority(self):
        """Matcher Value set on Attribute Priority
        for Host - alternate priority

        :id: f6ef2193-5d63-43f1-8d91-e30984b2c0c5

        :bz: 1362372

        :steps:

            1. Create variable with valid value and type
            2. Set some attribute(other than fqdn) as top priority attribute
               Note - The fqdn/host should have this attribute
            3. Create first matcher for fqdn with valid details
            4. Create second matcher for attribute of step 3 with valid details
            5. Check ENC output of associated host.

        :expectedresults: The ENC output shows variable value of step 4 matcher
            only

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    @upgrade
    def test_positive_update_variable_merge_override(self):
        """Merge the values of all the associated matchers

        Note - This TC is only for array and hash key types

        :id: bb37995e-71f9-441c-b4d5-79e5b5ff3973

        :bz: 1362372

        :steps:

            1. Create variable with valid value and type
            2. Create first matcher for attribute fqdn with valid details
            3. Create second matcher for other attribute with valid details.
               Note - The fqdn/host should have this attribute
            4. Create more matchers for some more attributes if any Note - The
               fqdn/host should have this attributes
            5. Set 'merge overrides' to True
            6. Check ENC output of associated host

        :expectedresults:

            1. The ENC output shows variable values merged from all the
               associated matchers
            2. The variable doesn't show the default value of variable.
            3. Duplicate values in any are displayed

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_variable_merge_override(self):
        """Merge the override values from non associated matchers

        Note - This TC is only for array and hash key types

        :id: afcb7ef4-38dd-484b-8a02-bc4e3d027204

        :bz: 1362372

        :steps:

            1. Create variable with valid value and type
            2. Create first matcher for attribute fqdn with valid details
            3. Create second matcher for other attribute with valid details
               Note - The fqdn/host should not have this attribute
            4. Create more matchers for some more attributes if any Note - The
               fqdn/host should not have this attributes
            5. Set 'merge overrides' to True
            6. Check ENC output of associated host

        :expectedresults:

            1. The ENC output shows variable values only for fqdn
            2. The variable doesn't have the values for attribute which are not
               associated to host
            3. The variable doesn't have the default value of variable
            4. Duplicate values if any are displayed

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    @upgrade
    def test_positive_update_variable_merge_default(self):
        """Merge the values of all the associated matchers + default value

        Note - This TC is only for array and hash key types

        :id: 9607c52c-f4c7-468b-a741-d179de144646

        :bz: 1362372

        :steps:

            1. Create variable with valid value and type
            2. Create first matcher for attribute fqdn with valid details
            3. Create second matcher for other attribute with valid details
               Note - The fqdn/host should have this attribute
            4. Create more matchers for some more attributes if any Note - The
               fqdn/host should have this attributes
            5. Set 'merge overrides' to True
            6. Set 'merge default' to True
            7. Check ENC output of associated host

        :expectedresults:

            1. The ENC output shows the variable values merged from all the
               associated matchers
            2. The variable values has the default value of variable
            3. Duplicate values if any are displayed

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_variable_merge_default(self):
        """Empty default value is not shown in merged values

        Note - This TC is only for array and hash key types

        :id: 9033de15-f7e8-42be-b2be-c04c13aa039b

        :bz: 1362372

        :steps:

            1. Create variable with empty value and type
            2. Create first matcher for attribute fqdn with valid details
            3. Create second matcher for other attribute with valid details
               Note - The fqdn/host should have this attribute
            4. Create more matchers for some more attributes if any Note - The
               fqdn/host should have this attributes
            5. Set 'merge overrides' to True
            6. Set 'merge default' to True
            7. Check ENC output of associated host

        :expectedresults:

            1. The ENC output shows variable values merged from all the
               associated matchers
            2. The variable doesn't have the empty default value of variable
            3. Duplicate values if any are displayed

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    @upgrade
    def test_positive_update_variable_avoid_duplicate(self):
        """Merge the values of all the associated matchers, remove duplicates

        Note - This TC is only for array and hash key types

        :id: fcb2dfb9-64d6-4647-bbcc-3e5c900aca1b

        :bz: 1362372

        :steps:
            1. Create variable with valid value and type
            2. Create first matcher for attribute fqdn with some value
            3. Create second matcher for other attribute with same value as
               fqdn matcher.  Note - The fqdn/host should have this attribute
            4. Set 'merge overrides' to True
            5. Set 'merge default' to True
            6. Set 'avoid duplicate' to True
            7. Check ENC output of associated host

        :expectedresults:

            1. The ENC output shows the variable values merged from all the
               associated matchers
            2. The variable shows the default value of variable
            3. Duplicate values are removed / not displayed

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_variable_avoid_duplicate(self):
        """Duplicates are not removed as they were not really present

        Note - This TC is only for array and hash key types

        :id: 1f8a06de-0c53-424e-b2c9-b48a580d6298

        :bz: 1362372

        :steps:

            1. Create variable with valid value and type
            2. Create first matcher for attribute fqdn with some value
            3. Create second matcher for other attribute with other value than
               fqdn matcher and default value.  Note - The fqdn/host should
               have this attribute
            4. Set 'merge overrides' to True
            5. Set 'merge default' to True
            6. Set 'avoid duplicates' to True
            7. Check ENC output of associated host

        :expectedresults:

            1. The ENC output shows the variable values merged from all
               matchers
            2. The variable shows default value of variable
            3. No value removed as duplicate value

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @tier1
    def test_positive_enable_merge_overrides_and_default_flags(self):
        """Enable Merge Overrides, Merge Default flags for supported types

        :id: af2c16e1-9a78-4615-9bc3-34fadca6a179

        :steps: Set variable type to array/hash

        :expectedresults: The Merge Overrides, Merge Default flags are enabled
            to set

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=[gen_integer()],
            variable_type='array',
        ).create()
        smart_variable.merge_overrides = True
        smart_variable.merge_default = True
        smart_variable.update(['merge_overrides', 'merge_default'])
        smart_variable.read()
        self.assertEqual(smart_variable.merge_overrides, True)
        self.assertEqual(smart_variable.merge_default, True)

    @run_only_on('sat')
    @tier1
    def test_negative_enable_merge_overrides_default_flags(self):
        """Disable Merge Overrides, Merge Default flags for non supported types

        :id: f62a7e23-6fb4-469a-8589-4c987ff589ef

        :steps: Set variable type other than array/hash

        :expectedresults: The Merge Overrides, Merge Default flags are not
            enabled to set

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value='50',
            variable_type='string',
        ).create()
        with self.assertRaises(HTTPError) as context:
            smart_variable.merge_overrides = True
            smart_variable.update(['merge_overrides'])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Merge overrides can only be set for "
            "array or hash"
        )
        with self.assertRaises(HTTPError) as context:
            smart_variable.merge_default = True
            smart_variable.update(['merge_default'])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Merge default can only be set when merge "
            "overrides is set"
        )
        smart_variable = smart_variable.read()
        self.assertEqual(smart_variable.merge_overrides, False)
        self.assertEqual(smart_variable.merge_default, False)

    @run_only_on('sat')
    @tier1
    def test_positive_enable_avoid_duplicates_flag(self):
        """Enable Avoid duplicates flag for supported type

        :id: 98fb1884-ad2b-45a0-b376-66bbc5ef6f72

        :steps:

            1. Set variable type to array
            2. Set 'merge overrides' to True

        :expectedresults: The Avoid Duplicates is enabled to set to True

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=[gen_integer()],
            variable_type='array',
        ).create()
        smart_variable.merge_overrides = True
        smart_variable.avoid_duplicates = True
        smart_variable.update(['merge_overrides', 'avoid_duplicates'])
        self.assertEqual(smart_variable.merge_overrides, True)
        self.assertEqual(smart_variable.avoid_duplicates, True)

    @run_only_on('sat')
    @tier1
    def test_negative_enable_avoid_duplicates_flag(self):
        """Disable Avoid duplicates flag for non supported types

        :id: c7a2f718-6346-4851-b5f1-ab36c2fa8c6a

        :steps: Set variable type other than array

        :expectedresults:

            1. The Merge Overrides flag is only enabled to set for type hash
               other than array
            2. The Avoid duplicates flag not enabled to set for any type than
               array

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=True,
            variable_type='boolean',
        ).create()
        with self.assertRaises(HTTPError) as context:
            smart_variable.merge_overrides = True
            smart_variable.update(['merge_overrides'])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Merge overrides can only be set for "
            "array or hash"
        )
        with self.assertRaises(HTTPError) as context:
            smart_variable.avoid_duplicates = True
            smart_variable.update(['avoid_duplicates'])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Avoid duplicates can only be set for arrays "
            "that have merge_overrides set to true"
        )
        smart_variable = smart_variable.read()
        self.assertEqual(smart_variable.merge_overrides, False)
        self.assertEqual(smart_variable.avoid_duplicates, False)

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_remove_matcher(self):
        """Removal of matcher from variable

        :id: 7a932a99-2bd9-43ee-bcda-2b01a389787c

        :steps:

            1. Create the variable and create a matcher for some attribute
            2. Remove the matcher created in step 1

        :expectedresults: The matcher removed from variable

        :CaseImportance: Critical
        """
        value = gen_string('alpha')
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            override_value_order='is_virtual',
        ).create()
        matcher = entities.OverrideValue(
            smart_variable=smart_variable,
            match='is_virtual=true',
            value=value,
        ).create()
        smart_variable = smart_variable.read()
        self.assertEqual(
            smart_variable.override_values[0]['match'], 'is_virtual=true')
        self.assertEqual(
            smart_variable.override_values[0]['value'], value)
        matcher.delete()
        self.assertEqual(len(smart_variable.read().override_values), 0)

    @run_only_on('sat')
    @tier2
    def test_positive_impact_variable_delete_attribute(self):
        """Impact on variable after deleting associated attribute

        :id: d4faec04-be29-48e6-8585-10ff1c361a9e

        :steps:

            1. Create a variable and matcher for some attribute
            2. Delete the attribute
            3. Recreate the attribute with same name as earlier

        :expectedresults:

            1. The matcher for deleted attribute removed from variable
            2. On recreating attribute, the matcher should not reappear in
               variable

        :CaseLevel: Integration
        """
        hostgroup_name = gen_string('alpha')
        matcher_value = gen_string('alpha')
        # Create variable
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
        ).create()
        # Create hostgroup and add puppet class to it
        hostgroup = entities.HostGroup(
            name=hostgroup_name,
            environment=self.env,
        ).create()
        hostgroup.add_puppetclass(
            data={'puppetclass_id': self.puppet_class.id})
        # Create matcher
        entities.OverrideValue(
            smart_variable=smart_variable,
            match='hostgroup={0}'.format(hostgroup_name),
            value=matcher_value,
        ).create()
        smart_variable = smart_variable.read()
        self.assertEqual(
            smart_variable.override_values[0]['match'],
            'hostgroup={0}'.format(hostgroup_name)
        )
        self.assertEqual(
            smart_variable.override_values[0]['value'], matcher_value)
        # Delete hostgroup
        hostgroup.delete()
        self.assertEqual(len(smart_variable.read().override_values), 0)
        # Recreate hostgroup
        hostgroup = entities.HostGroup(
            name=hostgroup_name,
            environment=self.env,
        ).create()
        hostgroup.add_puppetclass(
            data={'puppetclass_id': self.puppet_class.id})
        self.assertEqual(len(smart_variable.read().override_values), 0)

    @run_only_on('sat')
    @tier1
    def test_positive_hide_variable_default_value(self):
        """Hide the default value of variable

        :id: 04bed7fa8-a5be-4fc0-8e9b-d68da00f8de0

        :steps:
            1. Create variable with valid type and value
            2. Set 'Hidden Value' flag to true

        :expectedresults: The 'hidden value' flag is set

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            hidden_value=True,
        ).create()
        self.assertEqual(getattr(smart_variable, 'hidden_value?'), True)
        self.assertEqual(smart_variable.default_value, u'*****')

    @run_only_on('sat')
    @tier1
    def test_positive_unhide_variable_default_value(self):
        """Unhide the default value of variable

        :id: e8b3ec03-1abb-48d8-9409-17178bb887cb

        :steps:
            1. Create variable with valid type and value
            2. Set 'Hidden Value' flag to True
            3. After hiding, set the 'Hidden Value' flag to False

        :expectedresults: The 'hidden value' flag set to false

        :CaseImportance: Critical
        """
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            hidden_value=True,
        ).create()
        self.assertEqual(getattr(smart_variable, 'hidden_value?'), True)
        smart_variable.hidden_value = False
        smart_variable.update(['hidden_value'])
        smart_variable = smart_variable.read()
        self.assertEqual(getattr(smart_variable, 'hidden_value?'), False)

    @run_only_on('sat')
    @tier1
    def test_positive_update_hidden_value_in_variable(self):
        """Update the hidden default value of variable

        :id: 21b5586e-9434-45ea-ae85-12e24c549412

        :steps:
            1. Create variable with valid type and value
            2. Set 'Hidden Value' flag to true
            3. Now in hidden state, update the default value

        :expectedresults: 1. The variable default value is updated 2. The
            'hidden value' flag set to True

        :CaseImportance: Critical
        """
        value = gen_string('alpha')
        smart_variable = entities.SmartVariable(
            puppetclass=self.puppet_class,
            default_value=gen_string('alpha'),
            hidden_value=True,
        ).create()
        self.assertEqual(getattr(smart_variable, 'hidden_value?'), True)
        self.assertEqual(smart_variable.default_value, u'*****')
        smart_variable.default_value = value
        smart_variable.update(['default_value'])
        smart_variable = smart_variable.read(params={'show_hidden': 'true'})
        self.assertEqual(smart_variable.default_value, value)
        self.assertEqual(getattr(smart_variable, 'hidden_value?'), True)
