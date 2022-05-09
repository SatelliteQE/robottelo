"""Test class for Smart/Puppet Class Parameter

:Requirement: Classparameters

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:Upstream: No
"""
import json
from random import choice

import pytest
from fauxfactory import gen_boolean
from fauxfactory import gen_integer
from fauxfactory import gen_string
from requests import HTTPError

from robottelo.config import settings
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import parametrized


@filtered_datapoint
def valid_sc_parameters_data():
    """Returns a list of valid smart class parameter types and values"""
    return [
        {'sc_type': 'string', 'value': gen_string('utf8')},
        {'sc_type': 'boolean', 'value': choice(['0', '1'])},
        {'sc_type': 'integer', 'value': gen_integer(min_value=1000)},
        {'sc_type': 'real', 'value': -123.0},
        {'sc_type': 'array', 'value': [gen_string('alpha'), gen_integer(), gen_boolean()]},
        {'sc_type': 'hash', 'value': f'{{"{gen_string("alpha")}": "{gen_string("alpha")}"}}'},
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


@pytest.fixture(scope='module')
def module_puppet(session_puppet_enabled_sat):
    puppet_class = 'api_test_classparameters'
    env_name = session_puppet_enabled_sat.create_custom_environment(repo=puppet_class)
    puppet_class = session_puppet_enabled_sat.api.PuppetClass().search(
        query={'search': f'name = "{puppet_class}" and environment = "{env_name}"'}
    )[0]
    sc_params_list = session_puppet_enabled_sat.api.SmartClassParameters().search(
        query={'search': f'puppetclass="{puppet_class.name}"', 'per_page': '1000'}
    )
    env = (
        session_puppet_enabled_sat.api.Environment()
        .search(query={'search': f'name="{env_name}"'})[0]
        .read()
    )
    yield {'env': env, 'class': puppet_class, 'sc_params': sc_params_list}
    session_puppet_enabled_sat.delete_puppet_class(puppet_class.name)
    session_puppet_enabled_sat.destroy_custom_environment(env_name)


@pytest.mark.run_in_one_thread
@pytest.mark.skipif(
    not settings.robottelo.repos_hosting_url, reason='repos_hosting_url is not defined'
)
class TestSmartClassParameters:
    """Implements Smart Class Parameter tests in API"""

    @pytest.mark.tier1
    @pytest.mark.upgrade
    @pytest.mark.parametrize('data', **parametrized(valid_sc_parameters_data()))
    def test_positive_update_parameter_type(self, data, module_puppet):
        """Positive Parameter Update for parameter types - Valid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: 1140c3bf-ab3b-4da6-99fb-9c508cefbbd1

        :parametrized: yes

        :steps:

            1. Set override to True.
            2. Update the Key Type to any of available.
            3. Set a 'valid' default Value.

        :expectedresults: Parameter Updated with a new type successfully.

        :CaseImportance: Medium
        """
        sc_param = module_puppet['sc_params'].pop()
        sc_param.override = True
        sc_param.parameter_type = data['sc_type']
        sc_param.default_value = data['value']
        sc_param.update(['override', 'parameter_type', 'default_value'])
        sc_param = sc_param.read()
        if data['sc_type'] == 'boolean':
            assert sc_param.default_value == (data['value'] == '1')
        elif data['sc_type'] == 'array':
            assert sc_param.default_value == data['value']
        elif data['sc_type'] in ('json', 'hash'):
            assert sc_param.default_value == json.loads(data['value'])  # convert string to dict
        else:
            assert sc_param.default_value == data['value']

    @pytest.mark.tier1
    @pytest.mark.parametrize('test_data', **parametrized(invalid_sc_parameters_data()))
    def test_negative_update_parameter_type(self, test_data, module_puppet):
        """Negative Parameter Update for parameter types - Invalid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: 7f0ab885-5520-4431-a916-f739c0498a5b

        :parametrized: yes

        :steps:

            1. Set override to True.
            2. Update the Key Type.
            3. Attempt to set an 'Invalid' default Value.

        :expectedresults:

            1. Parameter not updated with string type for invalid value.
            2. Error raised for invalid default value.

        :CaseImportance: Medium
        """
        sc_param = module_puppet['sc_params'].pop()
        with pytest.raises(HTTPError) as context:
            sc_param.override = True
            sc_param.parameter_type = test_data['sc_type']
            sc_param.default_value = test_data['value']
            sc_param.update(['override', 'parameter_type', 'default_value'])
        assert sc_param.read().default_value != test_data['value']
        assert 'Validation failed: Default value is invalid' in context.value.response.text

    @pytest.mark.tier1
    def test_positive_validate_default_value_required_check(
        self, session_puppet_enabled_sat, module_puppet
    ):
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
        sc_param = module_puppet['sc_params'].pop()
        sc_param.parameter_type = 'boolean'
        sc_param.default_value = True
        sc_param.override = True
        sc_param.required = True
        sc_param.update(['parameter_type', 'default_value', 'override', 'required'])
        sc_param = sc_param.read()
        assert sc_param.required is True
        assert sc_param.default_value is True
        session_puppet_enabled_sat.api.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value=False
        ).create()
        sc_param.update(['override', 'required'])
        sc_param = sc_param.read()
        assert sc_param.required is True
        assert sc_param.override_values[0]['value'] is False

    @pytest.mark.tier1
    def test_negative_validate_matcher_value_required_check(
        self, session_puppet_enabled_sat, module_puppet
    ):
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
        sc_param = module_puppet['sc_params'].pop()
        sc_param.override = True
        sc_param.required = True
        sc_param.update(['override', 'required'])
        with pytest.raises(HTTPError) as context:
            session_puppet_enabled_sat.api.OverrideValue(
                smart_class_parameter=sc_param, match='domain=example.com', value=''
            ).create()
        assert "Validation failed: Value can't be blank" in context.value.response.text

    @pytest.mark.tier1
    def test_negative_validate_default_value_with_regex(self, module_puppet):
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
        sc_param = module_puppet['sc_params'].pop()
        sc_param.override = True
        sc_param.default_value = value
        sc_param.validator_type = 'regexp'
        sc_param.validator_rule = '[0-9]'
        with pytest.raises(HTTPError) as context:
            sc_param.update(['override', 'default_value', 'validator_type', 'validator_rule'])
        assert 'Validation failed: Default value is invalid' in context.value.response.text
        assert sc_param.read().default_value != value

    @pytest.mark.tier1
    def test_positive_validate_default_value_with_regex(
        self, session_puppet_enabled_sat, module_puppet
    ):
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
        sc_param = module_puppet['sc_params'].pop()
        sc_param.override = True
        sc_param.default_value = value
        sc_param.validator_type = 'regexp'
        sc_param.validator_rule = '[0-9]'
        sc_param.update(['override', 'default_value', 'validator_type', 'validator_rule'])
        sc_param = sc_param.read()
        assert sc_param.default_value == value
        assert sc_param.validator_type == 'regexp'
        assert sc_param.validator_rule == '[0-9]'

        # validate matcher value
        session_puppet_enabled_sat.api.OverrideValue(
            smart_class_parameter=sc_param, match='domain=test.com', value=gen_string('numeric')
        ).create()
        sc_param.update(['override', 'default_value', 'validator_type', 'validator_rule'])
        assert sc_param.read().default_value == value

    @pytest.mark.tier1
    def test_negative_validate_matcher_value_with_list(
        self, session_puppet_enabled_sat, module_puppet
    ):
        """Error is raised for matcher value not in list.

        :id: a5e89e86-253f-4254-9ebb-eefb3dc2c2ab

        :steps:

            1. Set override to True.
            2. Create a matcher with value that doesn't match the list of step
            3. Validate this value with list validator type and rule.

        :expectedresults: Error raised for matcher value not in list.

        :CaseImportance: Medium
        """
        sc_param = module_puppet['sc_params'].pop()
        session_puppet_enabled_sat.api.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value='myexample'
        ).create()
        sc_param.override = True
        sc_param.default_value = 50
        sc_param.validator_type = 'list'
        sc_param.validator_rule = '25, example, 50'
        with pytest.raises(HTTPError) as context:
            sc_param.update(['override', 'default_value', 'validator_type', 'validator_rule'])
        assert 'Validation failed: Lookup values is invalid' in context.value.response.text
        assert sc_param.read().default_value != 50

    @pytest.mark.tier1
    def test_positive_validate_matcher_value_with_list(
        self, session_puppet_enabled_sat, module_puppet
    ):
        """Error is not raised for matcher value in list.

        :id: 05c1a0bb-ba27-4842-bb6a-8420114cffe7

        :steps:

            1. Set override to True.
            2. Create a matcher with value that matches the list of step 3.
            3. Validate this value with list validator type and rule.

        :expectedresults: Error not raised for matcher value in list.

        :CaseImportance: Medium
        """
        sc_param = module_puppet['sc_params'].pop()
        session_puppet_enabled_sat.api.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value=30
        ).create()
        sc_param.override = True
        sc_param.default_value = 'example'
        sc_param.validator_type = 'list'
        sc_param.validator_rule = 'test, example, 30'
        sc_param.update(['override', 'default_value', 'validator_type', 'validator_rule'])
        assert sc_param.read().default_value == 'example'

    @pytest.mark.tier1
    def test_positive_validate_matcher_value_with_default_type(
        self, session_puppet_enabled_sat, module_puppet
    ):
        """No error for matcher value of default type.

        :id: 77b6e90d-e38a-4973-98e3-c698eae5c534

        :steps:

            1. Set override to True.
            2. Update parameter default type with valid value.
            3. Create a matcher with value that matches the default type.

        :expectedresults: Error not raised for matcher value of default type.

        :CaseImportance: Medium
        """
        sc_param = module_puppet['sc_params'].pop()
        sc_param.override = True
        sc_param.parameter_type = 'boolean'
        sc_param.default_value = True
        sc_param.update(['override', 'parameter_type', 'default_value'])
        session_puppet_enabled_sat.api.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value=False
        ).create()
        sc_param = sc_param.read()
        assert sc_param.override_values[0]['value'] is False
        assert sc_param.override_values[0]['match'] == 'domain=example.com'

    @pytest.mark.tier1
    def test_negative_validate_matcher_and_default_value(
        self, session_puppet_enabled_sat, module_puppet
    ):
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
        sc_param = module_puppet['sc_params'].pop()
        session_puppet_enabled_sat.api.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value=gen_string('alpha')
        ).create()
        with pytest.raises(HTTPError) as context:
            sc_param.parameter_type = 'boolean'
            sc_param.default_value = gen_string('alpha')
            sc_param.update(['parameter_type', 'default_value'])
        assert (
            'Validation failed: Default value is invalid, Lookup values is invalid'
            in context.value.response.text
        )

    @pytest.mark.tier1
    def test_positive_create_and_remove_matcher_puppet_default_value(
        self, session_puppet_enabled_sat, module_puppet
    ):
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
        sc_param = module_puppet['sc_params'].pop()
        value = gen_string('alpha')
        sc_param.override = True
        sc_param.default_value = gen_string('alpha')
        override = session_puppet_enabled_sat.api.OverrideValue(
            smart_class_parameter=sc_param, match='domain=example.com', value=value, omit=True
        ).create()
        sc_param = sc_param.read()
        assert sc_param.override_values[0]['omit'] is True
        assert sc_param.override_values[0]['match'] == 'domain=example.com'
        assert sc_param.override_values[0]['value'] == value
        override.delete()
        assert len(sc_param.read().override_values) == 0

    @pytest.mark.tier1
    def test_positive_enable_merge_overrides_default_checkboxes(self, module_puppet):
        """Enable Merge Overrides, Merge Default checkbox for supported types.

        :id: ae1c8e2d-c15d-4325-9aa6-cc6b091fb95a

        :steps: Set parameter type to array/hash.

        :expectedresults: The Merge Overrides, Merge Default checks are enabled
            to check.

        :CaseImportance: Medium
        """
        sc_param = module_puppet['sc_params'].pop()
        sc_param.override = True
        sc_param.parameter_type = 'array'
        sc_param.default_value = f"[{gen_string('alpha')}, {gen_string('alpha')}]"
        sc_param.merge_overrides = True
        sc_param.merge_default = True
        sc_param.update(
            ['override', 'parameter_type', 'default_value', 'merge_overrides', 'merge_default']
        )
        sc_param = sc_param.read()
        assert sc_param.merge_overrides is True
        assert sc_param.merge_default is True

    @pytest.mark.tier1
    def test_negative_enable_merge_overrides_default_checkboxes(
        self, session_puppet_enabled_sat, module_puppet
    ):
        """Disable Merge Overrides, Merge Default checkboxes for non supported types.

        :id: d7b1c336-bd9f-40a3-a573-939f2a021cdc

        :steps: Set parameter type other than array/hash.

        :expectedresults: The Merge Overrides, Merge Default checks are not
            enabled to check.

        :CaseImportance: Medium
        """
        sc_param = module_puppet['sc_params'].pop()
        sc_param.override = True
        sc_param.parameter_type = 'string'
        sc_param.default_value = gen_string('alpha')
        sc_param.merge_overrides = True
        sc_param.merge_default = True
        with pytest.raises(HTTPError) as context:
            sc_param.update(['override', 'parameter_type', 'default_value', 'merge_overrides'])
        assert (
            'Validation failed: Merge overrides can only be set for array, hash, json or yaml'
            in context.value.response.text
        )
        with pytest.raises(HTTPError) as context:
            sc_param.update(['override', 'parameter_type', 'default_value', 'merge_default'])
        assert (
            'Validation failed: Merge default can only be set when merge overrides is set'
            in context.value.response.text
        )
        sc_param = sc_param.read()
        assert sc_param.merge_overrides is False
        assert sc_param.merge_default is False

    @pytest.mark.tier1
    def test_positive_enable_avoid_duplicates_checkbox(self, module_puppet):
        """Enable Avoid duplicates checkbox for supported type- array.

        :id: 80bf52df-e678-4384-a4d5-7a88928620ce

        :steps:

            1. Set parameter type to array.
            2. Set 'merge overrides' to True.

        :expectedresults: The Avoid Duplicates is enabled to set to True.

        :CaseImportance: Medium
        """
        sc_param = module_puppet['sc_params'].pop()
        sc_param.override = True
        sc_param.parameter_type = 'array'
        sc_param.default_value = f'[{gen_string("alpha")}, {gen_string("alpha")}]'
        sc_param.merge_overrides = True
        sc_param.avoid_duplicates = True
        sc_param.update(
            ['override', 'parameter_type', 'default_value', 'merge_overrides', 'avoid_duplicates']
        )
        assert sc_param.read().avoid_duplicates is True

    @pytest.mark.tier1
    def test_negative_enable_avoid_duplicates_checkbox(self, module_puppet):
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
        sc_param = module_puppet['sc_params'].pop()
        sc_param.override = True
        sc_param.parameter_type = 'string'
        sc_param.default_value = gen_string('alpha')
        sc_param.avoid_duplicates = True
        with pytest.raises(HTTPError) as context:
            sc_param.update(['override', 'parameter_type', 'default_value', 'avoid_duplicates'])
        assert (
            'Validation failed: Avoid duplicates can only be set for arrays '
            'that have merge_overrides set to true'
        ) in context.value.response.text
        assert sc_param.read().avoid_duplicates is False

    @pytest.mark.tier2
    def test_positive_impact_parameter_delete_attribute(
        self, session_puppet_enabled_sat, module_puppet
    ):
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
        sc_param = module_puppet['sc_params'].pop()
        hostgroup_name = gen_string('alpha')
        match = f'hostgroup={hostgroup_name}'
        match_value = gen_string('alpha')
        hostgroup = session_puppet_enabled_sat.api.HostGroup(
            name=hostgroup_name, environment=module_puppet['env']
        ).create()
        hostgroup.add_puppetclass(data={'puppetclass_id': module_puppet['class'].id})
        session_puppet_enabled_sat.api.OverrideValue(
            smart_class_parameter=sc_param, match=match, value=match_value
        ).create()
        sc_param = sc_param.read()
        assert sc_param.override_values[0]['match'] == match
        assert sc_param.override_values[0]['value'] == match_value
        hostgroup.delete()
        assert len(sc_param.read().override_values) == 0
        hostgroup = session_puppet_enabled_sat.api.HostGroup(
            name=hostgroup_name, environment=module_puppet['env']
        ).create()
        hostgroup.add_puppetclass(data={'puppetclass_id': module_puppet['class'].id})
        assert len(sc_param.read().override_values) == 0
        hostgroup.delete()
