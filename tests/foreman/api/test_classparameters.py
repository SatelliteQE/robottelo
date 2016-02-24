# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Class Parameter"""

from robottelo.decorators import run_only_on, stubbed, tier1, tier2, tier3
from robottelo.test import APITestCase


class SmartClassParametersTestCase(APITestCase):
    """Implements Smart Class Parameter tests in API"""

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_parameters_by_host_id(self):
        """List all the parameters included in specific Host by its id.

        @feature: Class Parameters - List

        @assert: Parameters listed for specific Host.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_parameters_by_hostgroup_id(self):
        """List all the parameters included in specific HostGroup by id.

        @feature: Class Parameters - List

        @assert: Parameters listed for specific HostGroup.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_parameters_by_puppetclass_id(self):
        """List all the parameters for specific puppet class by id.

        @feature: Class Parameters - List

        @assert: Parameters listed for specific Puppet class.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_parameters_by_environment_id(self):
        """List all the parameters for specific environment by id.

        @feature: Class Parameters - List

        @assert: Parameters listed for specific environment.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_override_checkbox(self):
        """Override the Default Parameter value.

        @feature: Class Parameters - Override

        @steps:

        1. Set override to True.
        2. Set the new valid Default Value.

        @assert: Parameter Value overridden with new value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_override_checkbox(self):
        """Override the Default Parameter value - override Unchecked.

        @feature: Class Parameters - Override

        @steps:

        1. Set override to False.
        2. Set the new valid Default Value.

        @assert: Parameter value not allowed/disabled to override.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_puppet_default(self):
        """On Override, Set Puppet Default Value.

        @feature: Class Parameters - Puppet Default

        @steps:

        1. Set override to True.
        2. Set 'Use Puppet Default' to True.

        @assert: Puppet Default Value applied on parameter.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_parameter_type(self):
        """Positive Parameter Update for parameter types - Valid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        @feature: Class Parameters - Parameter Type

        @steps:

        1. Set override to True.
        2. Update the Key Type to any of available.
        3. Set a 'valid' default Value.

        @assert: Parameter Updated with a new type successfully.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_parameter_type(self):
        """Negative Parameter Update for parameter types - Invalid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        @feature: Class Parameters - Parameter Type

        @steps:

        1. Set override to True.
        2. Update the Key Type.
        3. Attempt to set an 'Invalid' default Value.

        @assert:

        1. Parameter not updated with string type for invalid value.
        2. Error raised for invalid default value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_puppet_default_value(self):
        """Validation doesn't work on puppet default value.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Set puppet default value to 'Use Puppet Default'.
        3. Set Validator Type and Rule to validate this value.

        @assert: Validation shouldn't work with puppet default value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_required_checkbox(self):
        """Error raised for blank default Value - Required check.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Set empty default value.
        3. Set 'required' to True.

        @assert: Error raised for blank default value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_required_checkbox(self):
        """No error raised for non-empty default Value - Required check.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Set some default value, Not empty.
        3. Set 'required' to true.

        @assert: No error raised for non-empty default value

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_required_checkbox(self):
        """Error is raised for blank matcher Value - Required check.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Create a matcher for Parameter for some attribute.
        3. Set no value for matcher. Keep blank.
        4. Set 'required' to true.

        @assert: Error raised for blank matcher value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_required_checkbox(self):
        """Error is not raised for matcher Value - Required checkbox.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Create a matcher for Parameter for some attribute.
        3. Set some Value for matcher.
        4. Set 'required' to true.

        @assert: Error not raised for matcher value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_with_regex(self):
        """Error is raised for default value not matching with regex.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Set default value that doesn't matches the regex of step 3.
        3. Validate this value with regex validator type and rule.

        @assert: Error raised for default value not matching with regex.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_with_regex(self):
        """Error is not raised for default value matching with regex.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Set default value that matches the regex of step 3.
        3. Validate this value with regex validator type and rule.

        @assert: Error not raised for default value matching with regex.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_regex(self):
        """Error is raised for matcher value not matching with regex.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Create a matcher with value that doesn't match
        the regex of step 3.
        3. Validate this value with regex validator type and rule.

        @assert: Error raised for matcher value not matching with regex.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_regex(self):
        """Error is not raised for matcher value matching with regex.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Create a matcher with value that matches the regex of step 3.
        3. Validate this value with regex validator type and rule.

        @assert: Error not raised for matcher value matching with regex.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_with_list(self):
        """Error is raised for default value not in list.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Set default value that doesn't matches the list of step 3.
        3. Validate this value with list validator type and rule.

        @assert: Error is raised for default value that is not in list.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_with_list(self):
        """Error is not raised for default value in list.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Set default value that matches the list of step 3.
        3. Validate this value with list validator type and rule.

        @assert: Error not raised for default value in list.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_list(self):
        """Error is raised for matcher value not in list.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Create a matcher with value that doesn't match
        the list of step 3.
        3. Validate this value with list validator type and rule.

        @assert: Error raised for matcher value not in list.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_list(self):
        """Error is not raised for matcher value in list.

        @feature: Class Parameters - Optional Validation

        @steps:

        1. Set override to True.
        2. Create a matcher with value that matches the list of step 3.
        3. Validate this value with list validator type and rule.

        @assert: Error not raised for matcher value in list.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_default_type(self):
        """Error is raised for matcher value not of default type.

        @feature: Class Parameters - Validation

        @steps:

        1. Set override to True.
        2. Update parameter default type with valid value.
        3. Create a matcher with value that doesn't matches the default type.

        @assert: Error raised for matcher value not of default type.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_default_type(self):
        """No error for matcher value of default type.

        @feature: Class Parameters - Validation

        @steps:

        1. Set override to True.
        2. Update parameter default type with valid value.
        3. Create a matcher with value that matches the default type.

        @assert: Error not raised for matcher value of default type.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_and_default_value(self):
        """Error for invalid default and matcher value is raised both at a time.

        @feature: Class Parameters - Validation

        @steps:

        1. Set override to True.
        2. Update parameter default type with Invalid value.
        3. Create a matcher with value that doesn't matches the default type.

        @assert: Error raised for invalid default and matcher value both.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Error while creating matcher for Non Existing Attribute.

        @feature: Class Parameters - Validation

        @steps:

        1. Set override to True.
        2. Create a matcher with non existing attribute in org.

        @assert: Error raised for non existing attribute.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher(self):
        """Create matcher for attribute in parameter.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set some default Value.
        3. Create a matcher with all valid values.

        @assert: The matcher has been created successfully.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_puppet_default_value(self):
        """Create matcher for attribute in parameter where
        value is puppet default value.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set some default Value.
        3. Create matcher with valid attribute type, name and
        puppet default value.

        @assert: The matcher has been created successfully.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set some default Value.
        3. Set fqdn as top priority attribute.
        4. Create first matcher for fqdn with valid details.
        5. Create second matcher for some attribute with valid details.
        Note - The fqdn/host should have this attribute.
        6. Update the parameter with above steps.
        7. Go to YAML output of associated host.

        @assert: The YAML output has the value only for fqdn matcher.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host - alternate priority.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set some default Value.
        3. Set some attribute(other than fqdn) as top priority attribute.
        Note - The fqdn/host should have this attribute.
        4. Create first matcher for fqdn with valid details.
        5. Create second matcher for attribute of step 3 with valid details.
        6. Update the parameter with above steps.
        7. Go to YAML output of associated host.

        @assert:

        1. The YAML output has the value only for step 5 matcher.
        2. The YAML output doesn't have value for fqdn/host matcher.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_override(self):
        """Merge the values of all the associated matchers.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set some default Value.
        3. Create first matcher for attribute fqdn with valid details.
        4. Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5. Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6. Set 'merge overrides' to True.
        7. Update the parameter with above steps.
        8. Go to YAML output of associated host.

        @assert:

        1. The YAML output has the values merged from all the associated
        matchers.
        2. The YAML output doesn't have the default value of parameter.
        3. Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_override(self):
        """Attempt to merge the values from non associated matchers.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set some default Value.
        3. Create first matcher for attribute fqdn with valid details.
        4. Create second matcher for other attribute with valid details.
        Note - The fqdn/host should not have this attribute.
        5. Create more matchers for some more attributes if any.
        Note - The fqdn/host should not have this attributes.
        6. Set 'merge overrides' to True.
        7. Update the parameter with above steps.
        8. Go to YAML output of associated host.

        @assert:

        1. The YAML output has the values only for fqdn.
        2. The YAML output doesn't have the values for attribute
        which are not associated to host.
        3. The YAML output doesn't have the default value of parameter.
        4. Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_override_puppet_value(self):
        """Merge the values of all the associated matchers + puppet default value.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set some default Value.
        3. Create first matcher for attribute fqdn with valid details.
        4. Create second matcher for other attribute with value
        as puppet default.
        Note - The fqdn/host should have this attribute.
        5. Create more matchers for some more attributes with value
        as puppet default.
        Note - The fqdn/host should have this attributes.
        6. Set 'merge overrides' to True.
        7. Set 'merge default' to True.
        8. Update the parameter with above steps.
        9. Go to YAML output of associated host.

        @assert:

        1. The YAML output has the value only for fqdn.
        2. The YAML output doesn't have the puppet default values of matchers.
        3. Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_default(self):
        """Merge the values of all the associated matchers + default value.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set some default Value.
        3. Create first matcher for attribute fqdn with valid details.
        4. Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5. Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6. Set 'merge overrides' to True.
        7. Set 'merge default' to True.
        8. Update the parameter with above steps.
        9. Go to YAML output of associated host.

        @assert:

        1. The YAML output has the values merged from all
        the associated matchers.
        2. The YAML output has the default value of parameter.
        3. Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_default(self):
        """Empty default value is not shown in merged values.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set empty default Value.
        3. Create first matcher for attribute fqdn with valid details.
        4. Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5. Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6. Set 'merge overrides' to True.
        7. Set 'merge default' to True.
        8. Update the parameter with above steps.
        9. Go to YAML output of associated host.

        @assert:

        1. The YAML output has the values merged from all
        the associated matchers.
        2. The YAML output doesn't have the empty default value of parameter.
        3. Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_puppet_default(self):
        """Merge the values of all the associated matchers + puppet default value.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set default Value as puppet default value.
        3. Create first matcher for attribute fqdn with valid details.
        4. Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5. Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6. Set 'merge overrides' to True.
        7. Set 'merge default' to True.
        8. Update the parameter with above steps.
        9. Go to YAML output of associated host.

        @assert:

        1. The YAML output has the values merged from all
        the associated matchers.
        2. The YAML output doesn't have the puppet default value.
        3. Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_avoid_duplicate(self):
        """Merge the values of all the associated matchers, remove duplicates.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set some default Value of array type.
        3. Create first matcher for attribute fqdn with some value.
        4. Create second matcher for other attribute with
        same value as fqdn matcher.
        Note - The fqdn/host should have this attribute.
        5. Set 'merge overrides' to True.
        6. Set 'merge default' to True.
        7. Set 'avoid duplicate' to True.
        8. Update the parameter with above steps.
        9. Go to YAML output of associated host.

        @assert:

        1. The YAML output has the values merged from all
        the associated matchers.
        2. The YAML output has the default value of parameter.
        3. Duplicate values in YAML output are removed / not displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_avoid_duplicate(self):
        """Duplicates are not removed as they were not really present.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set override to True.
        2. Set some default Value of array type.
        3. Create first matcher for attribute fqdn with some value.
        4. Create second matcher for other attribute with other value
        than fqdn matcher and default value.
        Note - The fqdn/host should have this attribute.
        5. Set 'merge overrides' to True.
        6. Set 'merge default' to True.
        7. Set 'merge avoid duplicates' to True.
        8. Update the parameter with above steps.
        9. Go to YAML output of associated host.

        @assert:

        1. The YAML output has the values merged from all matchers.
        2. The YAML output has the default value of parameter.
        3. No value removed as duplicate value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_enable_merge_overrides_default_checkboxes(self):
        """Enable Merge Overrides, Merge Default checkbox for supported types.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set parameter type to array/hash.

        @assert: The Merge Overrides, Merge Default checks are enabled to
        check.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_merge_overrides_default_checkboxes(self):
        """Disable Merge Overrides, Merge Default checkboxes for non supported types.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set parameter type other than array/hash.

        @assert: The Merge Overrides, Merge Default checks are not enabled to
        check.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_enable_avaoid_duplicates_checkbox(self):
        """Enable Avoid duplicates checkbox for supported type- array.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set parameter type to array.
        2. Set 'merge overrides' to True.

        @assert: The Avoid Duplicates is enabled to set to True.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_avoid_duplicates_checkbox(self):
        """Disable Avoid duplicates checkbox for non supported types.

        @feature: Class Parameters - Matcher

        @steps:

        1. Set parameter type other than array.

        @assert:

        1. The Merge Overrides checkbox is only enabled to check
        for type hash other than array.
        2. The Avoid duplicates checkbox not enabled to check
        for any type than array.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_matcher(self):
        """Removal of matcher from parameter.

        @feature: Class Parameters - Matcher

        @steps:

        1. Override the parameter and create a matcher for some attribute.
        2. Remove the matcher created in step 1.

        @assert: The matcher removed from parameter.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_impact_parameter_delete_attribute(self):
        """Impact on parameter after deleting associated attribute.

        @feature: Class Parameters - Outside Impact

        @steps:

        1. Set the parameter to True and create a matcher
        for some attribute.
        2. Delete the attribute.
        3. Recreate the attribute with same name as earlier.

        @assert:

        1. The matcher for deleted attribute removed from parameter.
        2. On recreating attribute, the matcher should not
        reappear in parameter.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_parameter_default_value(self):
        """Hide the default value of parameter.

        @feature: Class Parameters - Value Hiding

        @steps:

        1. Set the override flag to True.
        2. Set some valid default value.
        3. Set 'Hidden Value' to true.

        @assert: The 'hidden value' set to True for that parameter.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_unhide_parameter_default_value(self):
        """Unhide the default value of parameter.

        @feature: Class Parameters - Value Hiding

        @steps:

        1. Set the override flag to True.
        2. Set some valid default value.
        3. Set 'Hidden Value' to True and update parameter.
        4. After hiding, set the 'Hidden Value' to False.

        @assert: The 'hidden value' set to false for that parameter.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_hidden_value_in_parameter(self):
        """Update the hidden default value of parameter.

        @feature: Class Parameters - Value Hiding

        @steps:

        1. Set the override flag for the parameter.
        2. Set some valid default value.
        3. Set 'Hidden Value' to true and update the parameter.
        4. Now in hidden state, update the default value.

        @assert:

        1. The parameter default value is updated.
        2. The 'hidden value' set/displayed as True for that parameter.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value.

        @feature: Class Parameters - Value Hiding

        @steps:

        1. Set the override flag to True.
        2. Don't set any default value/Set empty value.
        3. Set 'Hidden Value' to true and update the parameter.

        @assert:

        1. The 'hidden value' set to True for that parameter.
        2. The default value is empty even after hide.

        @status: Manual
        """
