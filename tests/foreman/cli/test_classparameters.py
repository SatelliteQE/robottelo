# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Class Parameter"""

from robottelo.decorators import run_only_on, stubbed, tier1, tier3
from robottelo.test import CLITestCase


class SmartClassParametersTestCase(CLITestCase):
    """Implements Smart Class Parameter tests in CLI"""

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_override_check(self):
        """Override the Default Parameter value.

        @feature: Class Parameters - Override

        @steps:

        1.  Override the parameter.
        2.  Set the new valid Default Value.
        3.  Submit the changes.

        @assert: Parameter Value overridden with new value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_override_uncheck(self):
        """Override the Default Parameter value - override Unchecked.

        @feature: Class Parameters - Override

        @steps:

        1.  Don't override the parameter.
        2.  Set the new valid Default Value.
        3.  Attempt to submit the changes.

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

        1.  Override the parameter.
        2.  Set puppet default value to 'Use Puppet Default'.
        3.  Submit the changes.

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

        1.  Override the parameter.
        2.  Update the Key Type.
        3.  Provide a 'valid' default Value.
        3.  Submit the changes.

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

        1.  Override the parameter.
        2.  Update the Key Type.
        3.  Enter an 'Invalid' default Value.
        3.  Submit the changes.

        @assert:

        1.  Parameter not updated with string type for invalid value.
        2.  Error raised for invalid default value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_puppet_default_value(self):
        """Validation doesn't works on puppet default value.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Set puppet default value to 'Use Puppet Default'.
        3.  Validate this value under section 'Optional Input Validator'.

        @assert: Validation shouldn't work with puppet default value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_required_check(self):
        """Error raised for blank default Value - Required check.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Set empty default value.
        3.  Set '--required' check.
        4.  Submit the change.

        @assert: Error raised for blank default value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_required_check(self):
        """No error raised for non-empty default Value - Required check.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Provide some default value, Not empty.
        3.  Set '--required' check.
        4.  Submit the change.

        @assert: No error raised for non-empty default value

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_required_check(self):
        """Error raised for blank matcher Value - Required check.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Create a matcher for Parameter for some attribute.
        3.  Dont provide Value for matcher. Keep blank.
        4.  Set '--required' check.
        5.  Submit the change.

        @assert: Error raised for blank matcher value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_required_check(self):
        """Error not raised for matcher Value - Required check.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Create a matcher for Parameter for some attribute.
        3.  Provide some Value for matcher.
        4.  Set '--required' check.
        5.  Submit the change.

        @assert: Error not raised for matcher value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_with_regex(self):
        """Error raised for default value not matching with regex.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Provide default value that doesn't matches the regex of step 3.
        3.  Validate this value with regex validator type and rule.
        4.  Submit the change.

        @assert: Error raised for default value not matching with regex.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_with_regex(self):
        """Error not raised for default value matching with regex.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Provide default value that matches the regex of step 3.
        3.  Validate this value with regex validator type and rule.
        4.  Submit the change.

        @assert: Error not raised for default value matching with regex.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_regex(self):
        """Error raised for matcher value not matching with regex.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Create a matcher with value that doesn't match
        the regex of step 3.
        3.  Validate this value with regex validator type and rule.
        4.  Submit the change.

        @assert: Error raised for matcher value not matching with regex.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_regex(self):
        """Error not raised for matcher value matching with regex.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Create a matcher with value that matches the regex of step 3.
        3.  Validate this value with regex validator type and rule.
        4.  Submit the change.

        @assert: Error not raised for matcher value matching with regex.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_with_list(self):
        """Error raised for default value not in list.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Provide default value that doesn't matches the list of step 3.
        3.  Validate this value with list validator type and rule.
        4.  Submit the change.

        @assert: Error raised for default value not in list.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_with_list(self):
        """Error not raised for default value in list.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Provide default value that matches the list of step 3.
        3.  Validate this value with list validator type and rule.
        4.  Submit the change.

        @assert: Error not raised for default value in list.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_list(self):
        """Error raised for matcher value not in list.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Create a matcher with value that doesn't match
        the list of step 3.
        3.  Validate this value with list validator type and rule.
        4.  Submit the change.

        @assert: Error raised for matcher value not in list.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_list(self):
        """Error not raised for matcher value in list.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Override the parameter.
        2.  Create a matcher with value that matches the list of step 3.
        3.  Validate this value with list validator type and rule.
        4.  Submit the change.

        @assert: Error not raised for matcher value in list.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_default_type(self):
        """Error raised for matcher value not of default type.

        @feature: Class Parameters - Validation

        @steps:

        1.  Override the parameter.
        2.  Update parameter default type with valid value.
        3.  Create a matcher with value that doesn't matches the default type.
        4.  Submit the change.

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

        1.  Override the parameter.
        2.  Update parameter default type with valid value.
        3.  Create a matcher with value that matches the default type.
        4.  Submit the change.

        @assert: Error not raised for matcher value of default type.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_and_default_value(self):
        """Error for invalid default and matcher value both at a time.

        @feature: Class Parameters - Validation

        @steps:

        1.  Override the parameter.
        2.  Update parameter default type with Invalid value.
        3.  Create a matcher with value that doesn't matches the default type.
        4.  Attempt to submit the change.

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

        1.  Override the parameter.
        2.  Create a matcher with non existing attribute in org.
        4.  Attempt to submit the change.

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

        1.  Override the parameter.
        2.  Set some default Value.
        3.  Create a matcher with all valid values.
        4.  Submit the change.

        @assert: The matcher has been created successfully.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_puppet_default_value(self):
        """Create matcher for attribute in parameter,
        Where Value is puppet default value.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Override the parameter.
        2.  Set some default Value.
        3.  Create matcher with valid attribute type, name and
        puppet default value.
        4.  Submit the change.

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

        1.  Override the parameter.
        2.  Set some default Value.
        3.  Set fqdn as top priority attribute.
        4.  Create first matcher for fqdn with valid details.
        5.  Create second matcher for some attribute with valid details.
        Note - The fqdn/host should have this attribute.
        6.  Submit the change.
        7.  Go to YAML output of associated host.

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

        1.  Override the parameter.
        2.  Set some default Value.
        3.  Set some attribute(other than fqdn) as top priority attribute.
        Note - The fqdn/host should have this attribute.
        4.  Create first matcher for fqdn with valid details.
        5.  Create second matcher for attribute of step 3 with valid details.
        6.  Submit the change.
        7.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the value only for step 5 matcher.
        2.  The YAML output doesn't have value for fqdn/host matcher.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_override(self):
        """Merge the values of all the associated matchers.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Override the parameter.
        2.  Set some default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6.  Set '--merge overrides' check.
        7.  Submit the change.
        8.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all the associated
        matchers.
        2.  The YAML output doesn't have the default value of parameter.
        3.  Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_override(self):
        """Attempt to merge the values from non associated matchers.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Override the parameter.
        2.  Set some default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should not have this attribute.
        5.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should not have this attributes.
        6.  Set '--merge overrides' check.
        7.  Submit the change.
        8.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values only for fqdn.
        2.  The YAML output doesn't have the values for attribute
        which are not associated to host.
        3.  The YAML output doesn't have the default value of parameter.
        4.  Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_override_puppet_value(self):
        """Merge the values of all the associated matchers + puppet default value.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Override the parameter.
        2.  Set some default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with value
        as puppet default.
        Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes with value
        as puppet default.
        Note - The fqdn/host should have this attributes.
        6.  Set '--merge overrides' check.
        7.  Set '--merge default' check.
        8.  Submit the change.
        9.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the value only for fqdn.
        2.  The YAML output doesn't have the puppet default values of matchers.
        3.  Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_default(self):
        """Merge the values of all the associated matchers + default value.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Override the parameter.
        2.  Set some default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6.  Set '--merge overrides' check.
        7.  Set '--merge default' check.
        8.  Submit the change.
        9.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all
        the associated matchers.
        2.  The YAML output has the default value of parameter.
        3.  Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_default(self):
        """Empty default value is not shown in merged values.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Override the parameter.
        2.  Set empty default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6.  Set '--merge overrides' check.
        7.  Set '--merge default' check.
        8.  Submit the change.
        9.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all
        the associated matchers.
        2.  The YAML output doesn't have the empty default value of parameter.
        3.  Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_puppet_default(self):
        """Merge the values of all the associated matchers + puppet default value.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Override the parameter.
        2.  Set default Value as puppet default value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6.  Set '--merge overrides' check.
        7.  Set '--merge default' check.
        8.  Submit the change.
        9.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all
        the associated matchers.
        2.  The YAML output doesn't have the puppet default value.
        3.  Duplicate values in YAML output if any are displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_avoid_duplicate(self):
        """Merge the values of all the associated matchers, remove duplicates.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Override the parameter.
        2.  Set some default Value of array type.
        3.  Create first matcher for attribute fqdn with some value.
        4.  Create second matcher for other attribute with
        same value as fqdn matcher.
        Note - The fqdn/host should have this attribute.
        5.  Set '--merge overrides' check.
        6.  Set '--merge default' check.
        7.  Set '--avoid duplicate' check.
        8.  Submit the change.
        9.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all
        the associated matchers.
        2.  The YAML output has the default value of parameter.
        3.  Duplicate values in YAML output are removed / not displayed.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_avoid_duplicate(self):
        """Duplicates not removed as they were not really present.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Override the parameter.
        2.  Set some default Value of array type.
        3.  Create first matcher for attribute fqdn with some value.
        4.  Create second matcher for other attribute with other value
        than fqdn matcher and default value.
        Note - The fqdn/host should have this attribute.
        5.  Set '--merge overrides' check.
        6.  Set '--merge default' check.
        7.  Set '--merge avoid duplicates' check.
        8.  Submit the change.
        9.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all matchers.
        2.  The YAML output has the default value of parameter.
        3.  No value removed as duplicate value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_impact_parameter_delete_attribute(self):
        """Impact on parameter after deleting associated attribute.

        @feature: Class Parameters - Outside Impact

        @steps:

        1.  Override the parameter and create a matcher
        for some attribute.
        2.  Delete the attribute.
        3.  Recreate the attribute with same name as earlier.

        @assert:

        1.  The matcher for deleted attribute removed from parameter.
        2.  On recreating attribute, the matcher should not
        reappear in parameter.

        @status: Manual
        """
