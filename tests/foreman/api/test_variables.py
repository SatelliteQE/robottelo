# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Variables

:Requirement: Smart_Variables

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SmartVariables

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

    @tier1
    def test_positive_update_variable_puppet_class(self):
        """Update Smart Variable's puppet class.

        :id: 2312cb28-c3b0-4fbc-84cf-b66f0c0c64f0

        :steps:
            1. Create a smart variable with valid name.
            2. Update the puppet class associated to the smart variable created
               in step1.

        :expectedresults: The variable is updated with new puppet class.

        :bz: 1375857

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

    @tier1
    def test_negative_create_variable_type(self):
        """Negative variable Update for variable types - Invalid Value

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: 9709d67c-682f-4e6c-8b8b-f02f6c2d3b71

        :steps: Create a variable with all valid key types and invalid default
            values

        :expectedresults: Variable is not created for invalid value

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

    @tier2
    def test_positive_create_default_value_with_list(self):
        """Create variable with matching list validator

        :id: 6bc2caa0-1300-4751-8239-34b96517465b

        :steps:

            1. Create variable with default value that matches the list
               validator of step 2
            2. Validate this value with list validator type and rule

        :expectedresults: Variable is created for matching value with list

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
