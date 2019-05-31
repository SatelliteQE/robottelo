# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Class Parameter

:Requirement: Classparameters

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import json
from random import choice

from fauxfactory import gen_boolean, gen_integer, gen_string

from nailgun import entities
from requests import HTTPError

from robottelo.api.utils import delete_puppet_class, publish_puppet_module
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.datafactory import filtered_datapoint
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_bug_open,
    tier1,
    upgrade
)
from robottelo.test import APITestCase


@filtered_datapoint
def valid_sc_parameters_data():
    """Returns a list of valid smart class parameter types and values"""
    return [
        {
            u'sc_type': 'string',
            u'value': gen_string('utf8'),
        },
        {
            u'sc_type': 'boolean',
            u'value': choice(['0', '1']),
        },
        {
            u'sc_type': 'integer',
            u'value': gen_integer(min_value=1000),
        },
        {
            u'sc_type': 'real',
            u'value': -123.0,
        },
        {
            u'sc_type': 'array',
            u'value': "['{0}', '{1}', '{2}']".format(
                gen_string('alpha'), gen_integer(), gen_boolean()),
        },
        {
            u'sc_type': 'hash',
            u'value': '{{"{0}": "{1}"}}'.format(
                gen_string('alpha'), gen_string('alpha')),
        },
        {
            u'sc_type': 'yaml',
            u'value': 'name=>XYZ',
        },
        {
            u'sc_type': 'json',
            u'value': '{"name": "XYZ"}',
        },
    ]


@filtered_datapoint
def invalid_sc_parameters_data():
    """Returns a list of invalid smart class parameter types and values"""
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
            u'value': gen_string('alpha'),
        },
        {
            u'sc_type': 'array',
            u'value': '0',
        },
        {
            u'sc_type': 'hash',
            u'value': 'a:test',
        },
        {
            u'sc_type': 'yaml',
            u'value': '{a:test}',
        },
        {
            u'sc_type': 'json',
            u'value': gen_string('alpha'),
        },
    ]


@run_in_one_thread
class SmartClassParametersTestCase(APITestCase):
    """Implements Smart Class Parameter tests in API"""

    @classmethod
    def setUpClass(cls):
        """Import some parametrized puppet classes. This is required to make
        sure that we have smart class variable available.
        Read all available smart class parameters for imported puppet class to
        be able to work with unique entity for each specific test.
        """
        super(SmartClassParametersTestCase, cls).setUpClass()
        cls.puppet_modules = [
            {'author': 'robottelo', 'name': 'api_test_classparameters'},
        ]
        cls.org = entities.Organization().create()
        cv = publish_puppet_module(
            cls.puppet_modules, CUSTOM_PUPPET_REPO, cls.org)
        cls.env = entities.Environment().search(
            query={'search': u'content_view="{0}"'.format(cv.name)}
        )[0].read()
        cls.puppet_class = entities.PuppetClass().search(query={
            'search': u'name = "{0}" and environment = "{1}"'.format(
                cls.puppet_modules[0]['name'], cls.env.name)
        })[0]
        cls.sc_params_list = entities.SmartClassParameters().search(
            query={
                'search': 'puppetclass="{0}"'.format(cls.puppet_class.name),
                'per_page': 1000
            })

    @classmethod
    def tearDownClass(cls):
        """Removes puppet class."""
        super(SmartClassParametersTestCase, cls).tearDownClass()
        delete_puppet_class(cls.puppet_class.name)

    def setUp(self):
        """Checks that there is at least one not overridden
        smart class parameter before executing test.
        """
        super(SmartClassParametersTestCase, self).setUp()
        if len(self.sc_params_list) == 0:
            raise Exception("Not enough smart class parameters. Please "
                            "update puppet module.")

    @tier1
    @upgrade
    def test_positive_update_parameter_type(self):
        """Positive Parameter Update for parameter types - Valid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: 1140c3bf-ab3b-4da6-99fb-9c508cefbbd1

        :steps:

            1. Set override to True.
            2. Update the Key Type to any of available.
            3. Set a 'valid' default Value.

        :expectedresults: Parameter Updated with a new type successfully.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        for data in valid_sc_parameters_data():
            with self.subTest(data):
                sc_param.override = True
                sc_param.parameter_type = data['sc_type']
                sc_param.default_value = data['value']
                sc_param.update(
                    ['override', 'parameter_type', 'default_value']
                )
                sc_param = sc_param.read()
                if data['sc_type'] == 'boolean':
                    self.assertEqual(
                        sc_param.default_value,
                        True if data['value'] == '1' else False
                    )
                elif data['sc_type'] == 'array':
                    string_list = [
                        str(element) for element in sc_param.default_value]
                    self.assertEqual(str(string_list), data['value'])
                elif data['sc_type'] in ('json', 'hash'):
                    self.assertEqual(
                        sc_param.default_value,
                        # convert string to dict
                        json.loads(data['value'])
                    )
                else:
                    self.assertEqual(sc_param.default_value, data['value'])

    @tier1
    def test_negative_update_parameter_type(self):
        """Negative Parameter Update for parameter types - Invalid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: 7f0ab885-5520-4431-a916-f739c0498a5b

        :steps:

            1. Set override to True.
            2. Update the Key Type.
            3. Attempt to set an 'Invalid' default Value.

        :expectedresults:

            1. Parameter not updated with string type for invalid value.
            2. Error raised for invalid default value.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        for test_data in invalid_sc_parameters_data():
            with self.subTest(test_data):
                with self.assertRaises(HTTPError) as context:
                    sc_param.override = True
                    sc_param.parameter_type = test_data['sc_type']
                    sc_param.default_value = test_data['value']
                    sc_param.update(
                        ['override', 'parameter_type', 'default_value'])
                self.assertNotEqual(
                    sc_param.read().default_value, test_data['value'])
                self.assertRegexpMatches(
                    context.exception.response.text,
                    "Validation failed: Default value is invalid"
                )

    @tier1
    def test_positive_validate_default_value_required_check(self):
        """No error raised for non-empty default Value - Required check.

        :id: 92977eb0-92c2-4734-84d9-6fda8ff9d2d8

        :steps:

            1. Set override to True.
            2. Set some default value, Not empty.
            3. Set 'required' to true.

        :expectedresults: No error raised for non-empty default value

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.parameter_type = 'boolean'
        sc_param.default_value = True
        sc_param.override = True
        sc_param.required = True
        sc_param.update(
            ['parameter_type', 'default_value', 'override', 'required']
        )
        sc_param = sc_param.read()
        self.assertEqual(sc_param.required, True)
        self.assertEqual(sc_param.default_value, True)

    @tier1
    def test_negative_validate_matcher_value_required_check(self):
        """Error is raised for blank matcher Value - Required check.

        :id: 49de2c9b-40f1-4837-8ebb-dfa40d8fcb89

        :steps:
            1. Set override to True.
            2. Create a matcher for Parameter for some attribute.
            3. Set no value for matcher. Keep blank.
            4. Set 'required' to true.

        :expectedresults: Error raised for blank matcher value.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.required = True
        sc_param.update(['override', 'required'])
        with self.assertRaises(HTTPError) as context:
            entities.OverrideValue(
                smart_class_parameter=sc_param,
                match='domain=example.com',
                value='',
            ).create()
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Value can't be blank"
        )

    @tier1
    def test_positive_validate_matcher_value_required_check(self):
        """Error is not raised for matcher Value - Required checkbox.

        :id: bf620cef-c7ab-4a32-9050-bd06040dc8d1

        :steps:

            1. Set override to True.
            2. Create a matcher for Parameter for some attribute.
            3. Set some Value for matcher.
            4. Set 'required' to true.

        :expectedresults: Error not raised for matcher value.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        value = gen_string('alpha')
        entities.OverrideValue(
            smart_class_parameter=sc_param,
            match='domain=example.com',
            value=value,
        ).create()
        sc_param.override = True
        sc_param.required = True
        sc_param.update(['override', 'required'])
        sc_param = sc_param.read()
        self.assertEqual(sc_param.required, True)
        self.assertEqual(sc_param.override_values[0]['value'], value)

    @tier1
    def test_negative_validate_default_value_with_regex(self):
        """Error is raised for default value not matching with regex.

        :id: 99628b78-3037-4c20-95f0-7ce5455093ac

        :steps:

            1. Set override to True.
            2. Set default value that doesn't matches the regex of step 3.
            3. Validate this value with regex validator type and rule.

        :expectedresults: Error raised for default value not matching with
            regex.

        :CaseImportance: Critical
        """
        value = gen_string('alpha')
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.default_value = value
        sc_param.validator_type = 'regexp'
        sc_param.validator_rule = '[0-9]'
        with self.assertRaises(HTTPError) as context:
            sc_param.update([
                'override', 'default_value',
                'validator_type', 'validator_rule'
            ])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Default value is invalid"
        )
        self.assertNotEqual(sc_param.read().default_value, value)

    @tier1
    def test_positive_validate_default_value_with_regex(self):
        """Error is not raised for default value matching with regex.

        :id: d5df7804-9633-4ef8-a065-10807351d230

        :steps:

            1. Set override to True.
            2. Set default value that matches the regex of step 3.
            3. Validate this value with regex validator type and rule.

        :expectedresults: Error not raised for default value matching with
            regex.

        :CaseImportance: Critical
        """
        value = gen_string('numeric')
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.default_value = value
        sc_param.validator_type = 'regexp'
        sc_param.validator_rule = '[0-9]'
        sc_param.update(
            ['override', 'default_value', 'validator_type', 'validator_rule']
        )
        sc_param = sc_param.read()
        self.assertEqual(sc_param.default_value, value)
        self.assertEqual(sc_param.validator_type, 'regexp')
        self.assertEqual(sc_param.validator_rule, '[0-9]')

    @tier1
    def test_negative_validate_matcher_value_with_regex(self):
        """Error is raised for matcher value not matching with regex.

        :id: 08820c89-2b93-40f1-be17-0bd38c519e90

        :steps:

            1. Set override to True.
            2. Create a matcher with value that doesn't match the regex of step
               3.
            3. Validate this value with regex validator type and rule.

        :expectedresults: Error raised for matcher value not matching with
            regex.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        value = gen_string('numeric')
        entities.OverrideValue(
            smart_class_parameter=sc_param,
            match='domain=test.com',
            value=gen_string('alpha'),
        ).create()
        sc_param.override = True
        sc_param.default_value = value
        sc_param.validator_type = 'regexp'
        sc_param.validator_rule = '[0-9]'
        with self.assertRaises(HTTPError) as context:
            sc_param.update([
                'override',
                'default_value',
                'validator_type',
                'validator_rule'
            ])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Lookup values is invalid"
        )
        self.assertNotEqual(sc_param.read().default_value, value)

    @tier1
    def test_positive_validate_matcher_value_with_regex(self):
        """Error is not raised for matcher value matching with regex.

        :id: 74164406-885b-4f5b-8ea0-06738314310f

        :steps:

            1. Set override to True.
            2. Create a matcher with value that matches the regex of step 3.
            3. Validate this value with regex validator type and rule.

        :expectedresults: Error not raised for matcher value matching with
            regex.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        value = gen_string('numeric')
        entities.OverrideValue(
            smart_class_parameter=sc_param,
            match='domain=test.com',
            value=gen_string('numeric'),
        ).create()
        sc_param.override = True
        sc_param.default_value = value
        sc_param.validator_type = 'regexp'
        sc_param.validator_rule = '[0-9]'
        sc_param.update(
            ['override', 'default_value', 'validator_type', 'validator_rule']
        )
        self.assertEqual(sc_param.read().default_value, value)

    @tier1
    def test_negative_validate_default_value_with_list(self):
        """Error is raised for default value not in list.

        :id: 75b1dc0b-2287-4b99-b8dc-e50b83355819

        :steps:

            1. Set override to True.
            2. Set default value that doesn't matches the list of step 3.
            3. Validate this value with list validator type and rule.

        :expectedresults: Error is raised for default value that is not in
            list.

        :CaseImportance: Critical
        """
        value = gen_string('alphanumeric')
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.default_value = value
        sc_param.validator_type = 'list'
        sc_param.validator_rule = '5, test'
        with self.assertRaises(HTTPError) as context:
            sc_param.update([
                'override',
                'default_value',
                'validator_type',
                'validator_rule',
            ])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Default value \\w+ is not one of"
        )
        self.assertNotEqual(sc_param.read().default_value, value)

    @tier1
    def test_positive_validate_default_value_with_list(self):
        """Error is not raised for default value in list.

        :id: d5d5f084-fa62-4ec3-90ea-9fcabd7bda4f

        :steps:

            1. Set override to True.
            2. Set default value that matches the list of step 3.
            3. Validate this value with list validator type and rule.

        :expectedresults: Error not raised for default value in list.

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
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.default_value = value
        sc_param.validator_type = 'list'
        sc_param.validator_rule = values_list_str
        sc_param.update([
            'override',
            'default_value',
            'validator_type',
            'validator_rule',
        ])
        sc_param = sc_param.read()
        self.assertEqual(sc_param.default_value, str(value))
        self.assertEqual(sc_param.validator_type, 'list')
        self.assertEqual(sc_param.validator_rule, values_list_str)

    @tier1
    def test_negative_validate_matcher_value_with_list(self):
        """Error is raised for matcher value not in list.

        :id: a5e89e86-253f-4254-9ebb-eefb3dc2c2ab

        :steps:

            1. Set override to True.
            2. Create a matcher with value that doesn't match the list of step
               3.
            3. Validate this value with list validator type and rule.

        :expectedresults: Error raised for matcher value not in list.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        entities.OverrideValue(
            smart_class_parameter=sc_param,
            match='domain=example.com',
            value='myexample',
        ).create()
        sc_param.override = True
        sc_param.default_value = 50
        sc_param.validator_type = 'list'
        sc_param.validator_rule = '25, example, 50'
        with self.assertRaises(HTTPError) as context:
            sc_param.update([
                'override',
                'default_value',
                'validator_type',
                'validator_rule',
            ])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Lookup values is invalid"
        )
        self.assertNotEqual(sc_param.read().default_value, 50)

    @tier1
    def test_positive_validate_matcher_value_with_list(self):
        """Error is not raised for matcher value in list.

        :id: 05c1a0bb-ba27-4842-bb6a-8420114cffe7

        :steps:

            1. Set override to True.
            2. Create a matcher with value that matches the list of step 3.
            3. Validate this value with list validator type and rule.

        :expectedresults: Error not raised for matcher value in list.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        entities.OverrideValue(
            smart_class_parameter=sc_param,
            match='domain=example.com',
            value=30,
        ).create()
        sc_param.override = True
        sc_param.default_value = 'example'
        sc_param.validator_type = 'list'
        sc_param.validator_rule = 'test, example, 30'
        sc_param.update(
            ['override', 'default_value', 'validator_type', 'validator_rule']
        )
        self.assertEqual(sc_param.read().default_value, 'example')

    @tier1
    def test_negative_validate_matcher_value_with_default_type(self):
        """Error is raised for matcher value not of default type.

        :id: 21668ef4-1a7a-41cb-98e3-dc4c664db351

        :steps:

            1. Set override to True.
            2. Update parameter default type with valid value.
            3. Create a matcher with value that doesn't matches the default
               type.

        :expectedresults: Error raised for matcher value not of default type.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.parameter_type = 'boolean'
        sc_param.default_value = True
        sc_param.update(['override', 'parameter_type', 'default_value'])
        with self.assertRaises(HTTPError) as context:
            entities.OverrideValue(
                smart_class_parameter=sc_param,
                match='domain=example.com',
                value=gen_string('alpha'),
            ).create()
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Value is invalid"
        )

    @tier1
    def test_positive_validate_matcher_value_with_default_type(self):
        """No error for matcher value of default type.

        :id: 77b6e90d-e38a-4973-98e3-c698eae5c534

        :steps:

            1. Set override to True.
            2. Update parameter default type with valid value.
            3. Create a matcher with value that matches the default type.

        :expectedresults: Error not raised for matcher value of default type.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.parameter_type = 'boolean'
        sc_param.default_value = True
        sc_param.update(['override', 'parameter_type', 'default_value'])
        entities.OverrideValue(
            smart_class_parameter=sc_param,
            match='domain=example.com',
            value=False,
        ).create()
        sc_param = sc_param.read()
        self.assertEqual(sc_param.override_values[0]['value'], False)
        self.assertEqual(
            sc_param.override_values[0]['match'], 'domain=example.com')

    @tier1
    def test_negative_validate_matcher_and_default_value(self):
        """Error for invalid default and matcher value is raised both at a time.

        :id: e46a12cb-b3ea-42eb-b1bb-b750655b6a4a

        :steps:

            1. Set override to True.
            2. Update parameter default type with Invalid value.
            3. Create a matcher with value that doesn't matches the default
               type.

        :expectedresults: Error raised for invalid default and matcher value
            both.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        entities.OverrideValue(
            smart_class_parameter=sc_param,
            match='domain=example.com',
            value=gen_string('alpha'),
        ).create()
        with self.assertRaises(HTTPError) as context:
            sc_param.parameter_type = 'boolean'
            sc_param.default_value = gen_string('alpha')
            sc_param.update(['parameter_type', 'default_value'])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Default value is invalid, "
            "Lookup values is invalid"
        )

    @tier1
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Error while creating matcher for Non Existing Attribute.

        :id: bef0e457-16be-4ca6-bc56-fa32dff55a01

        :steps:

            1. Set override to True.
            2. Create a matcher with non existing attribute in org.

        :expectedresults: Error raised for non existing attribute.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        with self.assertRaises(HTTPError) as context:
            entities.OverrideValue(
                smart_class_parameter=sc_param,
                match='hostgroup=nonexistingHG',
                value=gen_string('alpha')
            ).create()
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Match hostgroup=nonexistingHG does not match "
            "an existing host group"
        )

    @tier1
    @upgrade
    def test_positive_create_matcher(self):
        """Create matcher for attribute in parameter.

        :id: 19d319e6-9b12-485e-a680-c84d18742c40

        :steps:

            1. Set override to True.
            2. Set some default Value.
            3. Create a matcher with all valid values.

        :expectedresults: The matcher has been created successfully.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.override_value_order = 'is_virtual'
        sc_param.update(['override', 'override_value_order'])
        value = gen_string('alpha')
        entities.OverrideValue(
            smart_class_parameter=sc_param,
            match='is_virtual=true',
            value=value,
        ).create()
        sc_param = sc_param.read()
        self.assertEqual(
            sc_param.override_values[0]['match'], 'is_virtual=true')
        self.assertEqual(sc_param.override_values[0]['value'], value)

    @tier1
    def test_positive_create_matcher_puppet_default_value(self):
        """Create matcher for attribute in parameter where
        value is puppet default value.

        :id: 2b205e9c-e50c-48cd-8ebb-3b6bea09be77

        :steps:

            1. Set override to True.
            2. Set some default Value.
            3. Create matcher with valid attribute type, name and puppet
               default value.

        :expectedresults: The matcher has been created successfully.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        value = gen_string('alpha')
        sc_param.override = True
        sc_param.default_value = gen_string('alpha')
        entities.OverrideValue(
            smart_class_parameter=sc_param,
            match='domain=example.com',
            value=value,
            use_puppet_default=True,
        ).create()
        sc_param = sc_param.read()
        self.assertEqual(
            sc_param.override_values[0]['use_puppet_default'], True)
        self.assertEqual(
            sc_param.override_values[0]['match'], 'domain=example.com')
        self.assertEqual(sc_param.override_values[0]['value'], value)

    @tier1
    def test_positive_enable_merge_overrides_default_checkboxes(self):
        """Enable Merge Overrides, Merge Default checkbox for supported types.

        :id: ae1c8e2d-c15d-4325-9aa6-cc6b091fb95a

        :steps: Set parameter type to array/hash.

        :expectedresults: The Merge Overrides, Merge Default checks are enabled
            to check.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.parameter_type = 'array'
        sc_param.default_value = "[{0}, {1}]".format(
            gen_string('alpha'), gen_string('alpha'))
        sc_param.merge_overrides = True
        sc_param.merge_default = True
        sc_param.update([
            'override',
            'parameter_type',
            'default_value',
            'merge_overrides',
            'merge_default',
        ])
        sc_param = sc_param.read()
        self.assertEqual(sc_param.merge_overrides, True)
        self.assertEqual(sc_param.merge_default, True)

    @tier1
    def test_negative_enable_merge_overrides_default_checkboxes(self):
        """Disable Merge Overrides, Merge Default checkboxes for non supported types.

        :id: d7b1c336-bd9f-40a3-a573-939f2a021cdc

        :steps: Set parameter type other than array/hash.

        :expectedresults: The Merge Overrides, Merge Default checks are not
            enabled to check.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.parameter_type = 'string'
        sc_param.default_value = gen_string('alpha')
        sc_param.merge_overrides = True
        sc_param.merge_default = True
        with self.assertRaises(HTTPError) as context:
            sc_param.update([
                'override',
                'parameter_type',
                'default_value',
                'merge_overrides',
            ])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Merge overrides can only be set for "
            "array or hash"
        )
        with self.assertRaises(HTTPError) as context:
            sc_param.update([
                'override',
                'parameter_type',
                'default_value',
                'merge_default',
            ])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Merge default can only be set when merge "
            "overrides is set"
        )
        sc_param = sc_param.read()
        self.assertEqual(sc_param.merge_overrides, False)
        self.assertEqual(sc_param.merge_default, False)

    @tier1
    def test_positive_enable_avoid_duplicates_checkbox(self):
        """Enable Avoid duplicates checkbox for supported type- array.

        :id: 80bf52df-e678-4384-a4d5-7a88928620ce

        :steps:

            1. Set parameter type to array.
            2. Set 'merge overrides' to True.

        :expectedresults: The Avoid Duplicates is enabled to set to True.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.parameter_type = 'array'
        sc_param.default_value = "[{0}, {1}]".format(
            gen_string('alpha'), gen_string('alpha'))
        sc_param.merge_overrides = True
        sc_param.avoid_duplicates = True
        sc_param.update([
            'override',
            'parameter_type',
            'default_value',
            'merge_overrides',
            'avoid_duplicates',
        ])
        self.assertEqual(sc_param.read().avoid_duplicates, True)

    @tier1
    def test_negative_enable_avoid_duplicates_checkbox(self):
        """Disable Avoid duplicates checkbox for non supported types.

        :id: 11d75f6d-7105-4ee8-b147-b8329cae4156

        :steps: Set parameter type other than array.

        :expectedresults:

            1. The Merge Overrides checkbox is only enabled to check for type
               hash other than array.
            2. The Avoid duplicates checkbox not enabled to check for any type
               than array.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.parameter_type = 'string'
        sc_param.default_value = gen_string('alpha')
        sc_param.avoid_duplicates = True
        with self.assertRaises(HTTPError) as context:
            sc_param.update([
                'override',
                'parameter_type',
                'default_value',
                'avoid_duplicates'
            ])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Avoid duplicates can only be set for arrays "
            "that have merge_overrides set to true"
        )
        self.assertEqual(sc_param.read().avoid_duplicates, False)

    @tier1
    def test_positive_remove_matcher(self):
        """Removal of matcher from parameter.

        :id: 9018d624-07f2-4fb2-b421-8888c7d324a7

        :steps:

            1. Override the parameter and create a matcher for some attribute.
            2. Remove the matcher created in step 1.

        :expectedresults: The matcher removed from parameter.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.override_value_order = 'is_virtual'
        sc_param.update(['override', 'override_value_order'])
        value = gen_string('alpha')
        override = entities.OverrideValue(
            smart_class_parameter=sc_param,
            match='is_virtual=true',
            value=value,
        ).create()
        self.assertEqual(len(sc_param.read().override_values), 1)
        override.delete()
        self.assertEqual(len(sc_param.read().override_values), 0)

    @skip_if_bug_open('bugzilla', 1374253)
    @tier1
    def test_positive_impact_parameter_delete_attribute(self):
        """Impact on parameter after deleting associated attribute.

        :id: 3ffbf403-dac9-4172-a586-82267765abd8

        :steps:

            1. Set the parameter to True and create a matcher for some
               attribute.
            2. Delete the attribute.
            3. Recreate the attribute with same name as earlier.

        :expectedresults:

            1. The matcher for deleted attribute removed from parameter.
            2. On recreating attribute, the matcher should not reappear in
               parameter.

        :CaseImportance: Critical

        :CaseAutomation: automated
        """
        sc_param = self.sc_params_list.pop()
        hostgroup_name = gen_string('alpha')
        match = 'hostgroup={0}'.format(hostgroup_name)
        match_value = gen_string('alpha')
        hostgroup = entities.HostGroup(
            name=hostgroup_name,
            environment=self.env,
        ).create()
        hostgroup.add_puppetclass(
            data={'puppetclass_id': self.puppet_class.id})
        entities.OverrideValue(
            smart_class_parameter=sc_param,
            match=match,
            value=match_value,
        ).create()
        sc_param = sc_param.read()
        self.assertEqual(sc_param.override_values[0]['match'], match)
        self.assertEqual(sc_param.override_values[0]['value'], match_value)
        hostgroup.delete()
        self.assertEqual(len(sc_param.read().override_values), 0)
        hostgroup = entities.HostGroup(
            name=hostgroup_name,
            environment=self.env,
        ).create()
        hostgroup.add_puppetclass(
            data={'puppetclass_id': self.puppet_class.id})
        self.assertEqual(len(sc_param.read().override_values), 0)

    @tier1
    def test_positive_hide_parameter_default_value(self):
        """Hide the default value of parameter.

        :id: 0cb8ab59-7910-4573-9dea-2e489d1578d4

        :steps:

            1. Set the override flag to True.
            2. Set some valid default value.
            3. Set 'Hidden Value' to true.

        :expectedresults: The 'hidden value' set to True for that parameter.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.default_value = gen_string('alpha')
        sc_param.hidden_value = True
        sc_param.update(['override', 'default_value', 'hidden_value'])
        sc_param = sc_param.read()
        self.assertEqual(getattr(sc_param, 'hidden_value?'), True)
        self.assertEqual(sc_param.default_value, u'*****')

    @tier1
    def test_positive_unhide_parameter_default_value(self):
        """Unhide the default value of parameter.

        :id: 73151830-e902-4b9e-888e-149570869530

        :steps:

            1. Set the override flag to True.
            2. Set some valid default value.
            3. Set 'Hidden Value' to True and update parameter.
            4. After hiding, set the 'Hidden Value' to False.

        :expectedresults: The 'hidden value' set to false for that parameter.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.default_value = gen_string('alpha')
        sc_param.hidden_value = True
        sc_param.update(['override', 'default_value', 'hidden_value'])
        sc_param = sc_param.read()
        self.assertEqual(getattr(sc_param, 'hidden_value?'), True)
        sc_param.hidden_value = False
        sc_param.update(['hidden_value'])
        sc_param = sc_param.read()
        self.assertEqual(getattr(sc_param, 'hidden_value?'), False)

    @tier1
    def test_positive_update_hidden_value_in_parameter(self):
        """Update the hidden default value of parameter.

        :id: 6f7ad3c4-7745-45bf-a9f9-697f049556da

        :steps:

            1. Set the override flag for the parameter.
            2. Set some valid default value.
            3. Set 'Hidden Value' to true and update the parameter.
            4. Now in hidden state, update the default value.

        :expectedresults:

            1. The parameter default value is updated.
            2. The 'hidden value' set/displayed as True for that parameter.

        :CaseImportance: Critical
        """
        old_value = gen_string('alpha')
        new_value = gen_string('alpha')
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.default_value = old_value
        sc_param.hidden_value = True
        sc_param.update(['override', 'default_value', 'hidden_value'])
        sc_param = sc_param.read(params={'show_hidden': 'true'})
        self.assertEqual(getattr(sc_param, 'hidden_value?'), True)
        self.assertEqual(sc_param.default_value, old_value)
        sc_param.default_value = new_value
        sc_param.update(['default_value'])
        sc_param = sc_param.read(params={'show_hidden': 'true'})
        self.assertEqual(getattr(sc_param, 'hidden_value?'), True)
        self.assertEqual(sc_param.default_value, new_value)

    @tier1
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value.

        :id: b6882658-9201-4e87-978a-0195a99ec07d

        :steps:

            1. Set the override flag to True.
            2. Don't set any default value/Set empty value.
            3. Set 'Hidden Value' to true and update the parameter.

        :expectedresults:

            1. The 'hidden value' set to True for that parameter.
            2. The default value is empty even after hide.

        :CaseImportance: Critical

        :CaseAutomation: automated
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.default_value = ''
        sc_param.hidden_value = True
        sc_param.update(['override', 'default_value', 'hidden_value'])
        sc_param = sc_param.read()
        self.assertEqual(getattr(sc_param, 'hidden_value?'), True)
        self.assertEqual(sc_param.default_value, u'*****')
        sc_param = sc_param.read(params={'show_hidden': 'true'})
        self.assertEqual(sc_param.default_value, u'')
