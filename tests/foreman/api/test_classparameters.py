"""Test class for Smart/Puppet Class Parameter

:Requirement: Classparameters

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Puppet

:TestType: Functional

:Upstream: No
"""
import json
from random import choice

from fauxfactory import gen_boolean
from fauxfactory import gen_integer
from fauxfactory import gen_string
from nailgun import entities
from requests import HTTPError

from robottelo.api.utils import delete_puppet_class
from robottelo.api.utils import publish_puppet_module
from robottelo.config import settings
from robottelo.constants.repos import CUSTOM_PUPPET_REPO
from robottelo.datafactory import filtered_datapoint
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import skip_if
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import APITestCase


@filtered_datapoint
def valid_sc_parameters_data():
    """Returns a list of valid smart class parameter types and values"""
    return [
        {'sc_type': 'string', 'value': gen_string('utf8')},
        {'sc_type': 'boolean', 'value': choice(['0', '1'])},
        {'sc_type': 'integer', 'value': gen_integer(min_value=1000)},
        {'sc_type': 'real', 'value': -123.0},
        {
            'sc_type': 'array',
            'value': "['{}', '{}', '{}']".format(
                gen_string('alpha'), gen_integer(), gen_boolean()
            ),
        },
        {
            'sc_type': 'hash',
            'value': '{{"{0}": "{1}"}}'.format(gen_string('alpha'), gen_string('alpha')),
        },
        {'sc_type': 'yaml', 'value': 'name=>XYZ'},
        {'sc_type': 'json', 'value': '{"name": "XYZ"}'},
    ]


@filtered_datapoint
def invalid_sc_parameters_data():
    """Returns a list of invalid smart class parameter types and values"""
    return [
        {'sc_type': 'boolean', 'value': gen_string('alphanumeric')},
        {'sc_type': 'integer', 'value': gen_string('utf8')},
        {'sc_type': 'real', 'value': gen_string('alpha')},
        {'sc_type': 'array', 'value': '0'},
        {'sc_type': 'hash', 'value': 'a:test'},
        {'sc_type': 'yaml', 'value': '{a:test}'},
        {'sc_type': 'json', 'value': gen_string('alpha')},
    ]


@run_in_one_thread
class SmartClassParametersTestCase(APITestCase):
    """Implements Smart Class Parameter tests in API"""

    @classmethod
    @skip_if(not settings.repos_hosting_url)
    def setUpClass(cls):
        """Import some parametrized puppet classes. This is required to make
        sure that we have smart class variable available.
        Read all available smart class parameters for imported puppet class to
        be able to work with unique entity for each specific test.
        """
        super().setUpClass()
        cls.puppet_modules = [{'author': 'robottelo', 'name': 'api_test_classparameters'}]
        cls.org = entities.Organization().create()
        cv = publish_puppet_module(cls.puppet_modules, CUSTOM_PUPPET_REPO, cls.org)
        cls.env = (
            entities.Environment().search(query={'search': f'content_view="{cv.name}"'})[0].read()
        )
        cls.puppet_class = entities.PuppetClass().search(
            query={
                'search': 'name = "{}" and environment = "{}"'.format(
                    cls.puppet_modules[0]['name'], cls.env.name
                )
            }
        )[0]
        cls.sc_params_list = entities.SmartClassParameters().search(
            query={'search': f'puppetclass="{cls.puppet_class.name}"', 'per_page': 1000}
        )

    @classmethod
    def tearDownClass(cls):
        """Removes puppet class."""
        super().tearDownClass()
        delete_puppet_class(cls.puppet_class.name)

    def setUp(self):
        """Checks that there is at least one not overridden
        smart class parameter before executing test.
        """
        super().setUp()
        if len(self.sc_params_list) == 0:
            raise Exception("Not enough smart class parameters. Please update puppet module.")

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

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        for data in valid_sc_parameters_data():
            with self.subTest(data):
                sc_param.override = True
                sc_param.parameter_type = data['sc_type']
                sc_param.default_value = data['value']
                sc_param.update(['override', 'parameter_type', 'default_value'])
                sc_param = sc_param.read()
                if data['sc_type'] == 'boolean':
                    self.assertEqual(
                        sc_param.default_value, True if data['value'] == '1' else False
                    )
                elif data['sc_type'] == 'array':
                    string_list = [str(element) for element in sc_param.default_value]
                    self.assertEqual(str(string_list), data['value'])
                elif data['sc_type'] in ('json', 'hash'):
                    self.assertEqual(
                        sc_param.default_value,
                        # convert string to dict
                        json.loads(data['value']),
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

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        for test_data in invalid_sc_parameters_data():
            with self.subTest(test_data):
                with self.assertRaises(HTTPError) as context:
                    sc_param.override = True
                    sc_param.parameter_type = test_data['sc_type']
                    sc_param.default_value = test_data['value']
                    sc_param.update(['override', 'parameter_type', 'default_value'])
                self.assertNotEqual(sc_param.read().default_value, test_data['value'])
                self.assertRegexpMatches(
                    context.exception.response.text, "Validation failed: Default value is invalid"
                )

    @tier1
    def test_positive_validate_default_value_required_check(self):
        """No error raised for non-empty default Value - Required check.

        :id: 92977eb0-92c2-4734-84d9-6fda8ff9d2d8

        :steps:

            1. Set override to True.
            2. Set some default value, Not empty.
            3. Set 'required' to true.
            4. Create a matcher for Parameter for some attribute.
            5. Set some Value for matcher.

        :expectedresults: No error raised for non-empty default value

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        sc_param.parameter_type = 'boolean'
        sc_param.default_value = True
        sc_param.override = True
        sc_param.required = True
        sc_param.update(['parameter_type', 'default_value', 'override', 'required'])
        sc_param = sc_param.read()
        self.assertEqual(sc_param.required, True)
        self.assertEqual(sc_param.default_value, True)
        entities.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value=False
        ).create()
        sc_param.update(['override', 'required'])
        sc_param = sc_param.read()
        self.assertEqual(sc_param.required, True)
        self.assertEqual(sc_param.override_values[0]['value'], False)

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

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.required = True
        sc_param.update(['override', 'required'])
        with self.assertRaises(HTTPError) as context:
            entities.OverrideValue(
                smart_class_parameter=sc_param, match='domain=example.com', value=''
            ).create()
        self.assertRegexpMatches(
            context.exception.response.text, "Validation failed: Value can't be blank"
        )

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

        :CaseImportance: Low
        """
        value = gen_string('alpha')
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.default_value = value
        sc_param.validator_type = 'regexp'
        sc_param.validator_rule = '[0-9]'
        with self.assertRaises(HTTPError) as context:
            sc_param.update(['override', 'default_value', 'validator_type', 'validator_rule'])
        self.assertRegexpMatches(
            context.exception.response.text, "Validation failed: Default value is invalid"
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
            4. Create a matcher with value that matches the regex of step 3.
            5. Validate this value with regex validator type and rule.

        :expectedresults: Error not raised for default value matching with
            regex.

        :CaseImportance: Low
        """
        # validate default value
        value = gen_string('numeric')
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.default_value = value
        sc_param.validator_type = 'regexp'
        sc_param.validator_rule = '[0-9]'
        sc_param.update(['override', 'default_value', 'validator_type', 'validator_rule'])
        sc_param = sc_param.read()
        self.assertEqual(sc_param.default_value, value)
        self.assertEqual(sc_param.validator_type, 'regexp')
        self.assertEqual(sc_param.validator_rule, '[0-9]')

        # validate matcher value
        entities.OverrideValue(
            smart_class_parameter=sc_param, match='domain=test.com', value=gen_string('numeric')
        ).create()
        sc_param.update(['override', 'default_value', 'validator_type', 'validator_rule'])
        self.assertEqual(sc_param.read().default_value, value)

    @tier1
    def test_negative_validate_matcher_value_with_list(self):
        """Error is raised for matcher value not in list.

        :id: a5e89e86-253f-4254-9ebb-eefb3dc2c2ab

        :steps:

            1. Set override to True.
            2. Create a matcher with value that doesn't match the list of step
            3. Validate this value with list validator type and rule.

        :expectedresults: Error raised for matcher value not in list.

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        entities.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value='myexample'
        ).create()
        sc_param.override = True
        sc_param.default_value = 50
        sc_param.validator_type = 'list'
        sc_param.validator_rule = '25, example, 50'
        with self.assertRaises(HTTPError) as context:
            sc_param.update(['override', 'default_value', 'validator_type', 'validator_rule'])
        self.assertRegexpMatches(
            context.exception.response.text, "Validation failed: Lookup values is invalid"
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

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        entities.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value=30
        ).create()
        sc_param.override = True
        sc_param.default_value = 'example'
        sc_param.validator_type = 'list'
        sc_param.validator_rule = 'test, example, 30'
        sc_param.update(['override', 'default_value', 'validator_type', 'validator_rule'])
        self.assertEqual(sc_param.read().default_value, 'example')

    @tier1
    def test_positive_validate_matcher_value_with_default_type(self):
        """No error for matcher value of default type.

        :id: 77b6e90d-e38a-4973-98e3-c698eae5c534

        :steps:

            1. Set override to True.
            2. Update parameter default type with valid value.
            3. Create a matcher with value that matches the default type.

        :expectedresults: Error not raised for matcher value of default type.

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.parameter_type = 'boolean'
        sc_param.default_value = True
        sc_param.update(['override', 'parameter_type', 'default_value'])
        entities.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value=False
        ).create()
        sc_param = sc_param.read()
        self.assertEqual(sc_param.override_values[0]['value'], False)
        self.assertEqual(sc_param.override_values[0]['match'], 'domain=example.com')

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

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        entities.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value=gen_string('alpha')
        ).create()
        with self.assertRaises(HTTPError) as context:
            sc_param.parameter_type = 'boolean'
            sc_param.default_value = gen_string('alpha')
            sc_param.update(['parameter_type', 'default_value'])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Default value is invalid, Lookup values is invalid",
        )

    @tier1
    def test_positive_create_and_remove_matcher_puppet_default_value(self):
        """Create matcher for attribute in parameter where
        value is puppet default value.

        :id: 2b205e9c-e50c-48cd-8ebb-3b6bea09be77

        :steps:

            1. Set override to True.
            2. Set some default Value.
            3. Create matcher with valid attribute type, name and puppet
               default value.
            4. Remove matcher afterwards

        :expectedresults: The matcher has been created and removed successfully.

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        value = gen_string('alpha')
        sc_param.override = True
        sc_param.default_value = gen_string('alpha')
        override = entities.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value=value, omit=True
        ).create()
        sc_param = sc_param.read()
        self.assertEqual(sc_param.override_values[0]['omit'], True)
        self.assertEqual(sc_param.override_values[0]['match'], 'domain=example.com')
        self.assertEqual(sc_param.override_values[0]['value'], value)
        override.delete()
        self.assertEqual(len(sc_param.read().override_values), 0)

    @tier1
    def test_positive_enable_merge_overrides_default_checkboxes(self):
        """Enable Merge Overrides, Merge Default checkbox for supported types.

        :id: ae1c8e2d-c15d-4325-9aa6-cc6b091fb95a

        :steps: Set parameter type to array/hash.

        :expectedresults: The Merge Overrides, Merge Default checks are enabled
            to check.

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.parameter_type = 'array'
        sc_param.default_value = "[{}, {}]".format(gen_string('alpha'), gen_string('alpha'))
        sc_param.merge_overrides = True
        sc_param.merge_default = True
        sc_param.update(
            ['override', 'parameter_type', 'default_value', 'merge_overrides', 'merge_default']
        )
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

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.parameter_type = 'string'
        sc_param.default_value = gen_string('alpha')
        sc_param.merge_overrides = True
        sc_param.merge_default = True
        with self.assertRaises(HTTPError) as context:
            sc_param.update(['override', 'parameter_type', 'default_value', 'merge_overrides'])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Merge overrides can only be set for array or hash",
        )
        with self.assertRaises(HTTPError) as context:
            sc_param.update(['override', 'parameter_type', 'default_value', 'merge_default'])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Merge default can only be set when merge overrides is set",
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

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.parameter_type = 'array'
        sc_param.default_value = "[{}, {}]".format(gen_string('alpha'), gen_string('alpha'))
        sc_param.merge_overrides = True
        sc_param.avoid_duplicates = True
        sc_param.update(
            ['override', 'parameter_type', 'default_value', 'merge_overrides', 'avoid_duplicates']
        )
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

        :CaseImportance: Medium
        """
        sc_param = self.sc_params_list.pop()
        sc_param.override = True
        sc_param.parameter_type = 'string'
        sc_param.default_value = gen_string('alpha')
        sc_param.avoid_duplicates = True
        with self.assertRaises(HTTPError) as context:
            sc_param.update(['override', 'parameter_type', 'default_value', 'avoid_duplicates'])
        self.assertRegexpMatches(
            context.exception.response.text,
            "Validation failed: Avoid duplicates can only be set for arrays "
            "that have merge_overrides set to true",
        )
        self.assertEqual(sc_param.read().avoid_duplicates, False)

    @tier2
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

        :CaseImportance: Medium

        :BZ: 1374253

        """
        sc_param = self.sc_params_list.pop()
        hostgroup_name = gen_string('alpha')
        match = f'hostgroup={hostgroup_name}'
        match_value = gen_string('alpha')
        hostgroup = entities.HostGroup(name=hostgroup_name, environment=self.env).create()
        hostgroup.add_puppetclass(data={'puppetclass_id': self.puppet_class.id})
        entities.OverrideValue(
            smart_class_parameter=sc_param, match=match, value=match_value
        ).create()
        sc_param = sc_param.read()
        self.assertEqual(sc_param.override_values[0]['match'], match)
        self.assertEqual(sc_param.override_values[0]['value'], match_value)
        hostgroup.delete()
        self.assertEqual(len(sc_param.read().override_values), 0)
        hostgroup = entities.HostGroup(name=hostgroup_name, environment=self.env).create()
        hostgroup.add_puppetclass(data={'puppetclass_id': self.puppet_class.id})
        self.assertEqual(len(sc_param.read().override_values), 0)
