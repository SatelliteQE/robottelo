# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Class Parameter"""

from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier3
)
from robottelo.test import UITestCase


class SmartClassParametersTestCase(UITestCase):
    """Implements Smart Class Parameter tests in UI"""

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_override_checkbox(self):
        """Override the Default Parameter value.

        @feature: Class Parameters - Override

        @steps:

        1.  Check the Override checkbox.
        2.  Set the new valid Default Value.
        3.  Submit the changes.

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

        1.  Don't check the Override checkbox.
        2.  Set the new valid Default Value.
        3.  Attempt to submit the changes.

        @assert: Parameter value not allowed/disabled to override.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_edit_parameter_dialog(self):
        """Enable Validation, merging and matcher sections.

        @feature: Class Parameters - Edit Dialog

        @steps:

        1.  Check the Override checkbox.

        @assert: Puppet Default, Hiding, Validation, Merging and
        Matcher section enabled.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_edit_parameter_dialog(self):
        """Disable Validation, merging and matcher sections.

        @feature: Class Parameters - Edit Dialog

        @steps:

        1.  Dont't Check the Override checkbox.

        @assert: Puppet Default, Hiding, Validation, Merging and
        Matcher section is disabled.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_puppet_default(self):
        """On Override, Set Puppet Default Value.

        @feature: Class Parameters - Puppet Default

        @steps:

        1.  Check the Override checkbox.
        2.  Check 'Use Puppet Default' checkbox.
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

        1.  Check the Override checkbox.
        2.  Update the Key Type.
        3.  Enter a 'valid' default Value.
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

        1.  Check the Override checkbox.
        2.  Update the Key Type.
        3.  Enter an 'Invalid' default Value.
        3.  Submit the changes.

        @assert: Parameter not updated with string type for invalid value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_puppet_default_value(self):
        """Validation doesn't works on puppet default value.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Check the Override checkbox.
        2.  Check 'Use Puppet Default' value.
        3.  Validate this value under section 'Optional Input Validator'.

        @assert: Validation shouldn't work with puppet default value.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_required_checkbox(self):
        """Error raised for blank default Value - Required checkbox.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Check the Override checkbox.
        2.  Don't provide any default value, keep blank.
        3.  Check Required checkbox in 'Optional Input Validator'.
        4.  Submit the change.

        @assert: Error raised for blank default value by 'Required' checkbox.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_required_checkbox(self):
        """Error not raised for default Value - Required checkbox.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Check the Override checkbox.
        2.  Provide some default value.
        3.  Check Required checkbox in 'Optional Input Validator'.
        4.  Submit the change.

        @assert: Error not raised default value by 'Required' checkbox.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_required_checkbox(self):
        """Error raised for blank matcher Value - Required checkbox.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Check the Override checkbox.
        2.  Create a matcher for Parameter for some attribute.
        3.  Dont provide Value for matcher. Keep blank.
        4.  Check Required checkbox in 'Optional Input Validator'.
        5.  Submit the change.

        @assert: Error raised for blank matcher value by 'Required' checkbox.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_required_checkbox(self):
        """Error not raised for matcher Value - Required checkbox.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Check the Override checkbox.
        2.  Create a matcher for Parameter for some attribute.
        3.  Provide some Value for matcher.
        4.  Check Required checkbox in 'Optional Input Validator'.
        5.  Submit the change.

        @assert: Error not raised for matcher value by 'Required' checkbox.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_with_regex(self):
        """Error raised for default value not matching with regex.

        @feature: Class Parameters - Optional Validation

        @steps:

        1.  Check the Override checkbox.
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

        1.  Check the Override checkbox.
        2.  Provide default value that matches the regex of step 3..
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

        1.  Check the Override checkbox.
        2.  Create a matcher with value that doesn't matches
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

        1.  Check the Override checkbox.
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

        1.  Check the Override checkbox.
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

        1.  Check the Override checkbox.
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

        1.  Check the Override checkbox.
        2.  Create a matcher with value that doesn't matches
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

        1.  Check the Override checkbox.
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

        1.  Check the Override checkbox.
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

        1.  Check the Override checkbox.
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

        1.  Check the Override checkbox.
        2.  Update parameter default type with Invalid value.
        3.  Create a matcher with value that doesn't matches the default type.
        4.  Submit the change.

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

        1.  Check the Override checkbox.
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

        1.  Check the Override checkbox.
        2.  Set some default Value.
        3.  Click on 'Add Matcher' button to add matcher.
        4.  Choose valid attribute type, name and value.
        5.  Submit the change.

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

        1.  Check the Override checkbox.
        2.  Set some default Value.
        3.  Click on 'Add Matcher' button to add matcher.
        4.  Choose valid attribute type, name and puppet default value.
        5.  Submit the change.

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

        1.  Check the Override checkbox.
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

        1.  Check the Override checkbox.
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

        1.  Check the Override checkbox.
        2.  Set some default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6.  Select 'Merge overrides' checkbox.
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

        1.  Check the Override checkbox.
        2.  Set some default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should not have this attribute.
        5.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should not have this attributes.
        6.  Select 'Merge overrides' checkbox.
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
    def test_positive_create_matcher_merge_oveeride_puppet_value(self):
        """Merge the values of all the associated matchers + puppet default value.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Check the Override checkbox.
        2.  Set some default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with value
        as puppet default.
        Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes with value
        as puppet default.
        Note - The fqdn/host should have this attributes.
        6.  Select 'Merge overrides' checkbox.
        7.  Select 'Merge default' checkbox.
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

        1.  Check the Override checkbox.
        2.  Set some default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6.  Select 'Merge overrides' checkbox.
        7.  Select 'Merge default' checkbox.
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

        1.  Check the Override checkbox.
        2.  Set empty default Value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6.  Select 'Merge overrides' checkbox.
        7.  Select 'Merge default' checkbox.
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

        1.  Check the Override checkbox.
        2.  Set default Value as puppet default value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        6.  Select 'Merge overrides' checkbox.
        7.  Select 'Merge default' checkbox.
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

        1.  Check the Override checkbox.
        2.  Set some default Value of array type.
        3.  Create first matcher for attribute fqdn with some value.
        4.  Create second matcher for other attribute with
        same value as fqdn matcher.
        Note - The fqdn/host should have this attribute.
        5.  Select 'Merge overrides' checkbox.
        6.  Select 'Merge default' checkbox.
        7.  Select 'Avoid Duplicates' checkbox.
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

        1.  Check the Override checkbox.
        2.  Set some default Value of array type.
        3.  Create first matcher for attribute fqdn with some value.
        4.  Create second matcher for other attribute with other value
        than fqdn matcher and default value.
        Note - The fqdn/host should have this attribute.
        5.  Select 'Merge overrides' checkbox.
        6.  Select 'Merge default' checkbox.
        7.  Select 'Avoid Duplicates' checkbox.
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
    def test_positive_enable_merge_overrides_default_checkboxes(self):
        """Enable Merge Overrides, Merge Default checkbox for supported types.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Check the Override checkbox.
        2.  Set parameter type to array/hash.

        @assert: The Merge Overrides, Merge Default checkbox
        are enabled to check.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_merge_overrides_default_checkboxes(self):
        """Disable Merge Overrides, Merge Default checkboxes for non supported types.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Check the Override checkbox.
        2.  Set parameter type other than array/hash.

        @assert: The Merge Overrides, Merge Default checkboxes
        are not enabled to check.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_enable_avaoid_duplicates_checkbox(self):
        """Enable Avoid duplicates checkbox for supported type- array.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Check the Override checkbox.
        2.  Set parameter type to array.
        3.  Check Merge Overrides checkbox.

        @assert: The Avoid Duplicates checkbox is enabled to check.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_avaoid_duplicates_checkbox(self):
        """Disable Avoid duplicates checkbox for non supported types.

        @feature: Class Parameters - Matcher

        @steps:

        1.  Check the Override checkbox.
        2.  Set parameter type other than array.

        @assert:

        1.  The Merge Overrides checkbox is only enabled to check
        for type hash.
        2.  The Avoid duplicates checkbox not enabled to check
        for any type than array.

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

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_override_from_attribute(self):
        """Impact on parameter on overriding the parameter value from attribute.

        @feature: Class Parameters - Outside Impact

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Associate parameter with fqdn/hostgroup.
        3.  From host/hostgroup, override the parameter value.
        4.  Submit the changes.

        @assert:

        1.  The host/hostgroup is saved with changes.
        2.  New matcher for fqdn/hostgroup created inside parameter.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_override_from_attribute(self):
        """No impact on parameter on overriding the parameter
        with invalid value from attribute.

        @feature: Class Parameters - Outside Impact

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Associate parameter with fqdn/hostgroup.
        3.  From host/hostgroup, Attempt to override the parameter with
        some other key type of value.

        @assert:

        1.  Error thrown for invalid type value.
        2.  No matcher for fqdn/hostgroup is created inside parameter.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_override_from_attribute_puppet_default(self):
        """Impact on parameter on overriding the parameter value
        from attribute - puppet default.

        @feature: Class Parameters - Outside Impact

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Associate parameter with fqdn/hostgroup.
        3.  From host/hostgroup, override the parameter value as
        puppet default value.
        4.  Submit the changes.

        @assert:

        1.  The host/hostgroup is saved with changes.
        2.  New matcher for fqdn/hostgroup created inside parameter.
        3.  In matcher, 'Use Puppet Default' checkbox is checked.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_override_from_attribute_required_checked(self):
        """Error for empty value on overriding the parameter value
        from attribute - Required checked.

        @feature: Class Parameters - Outside Impact

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Check 'Required' checkbox in parameter.
        3.  Associate parameter with fqdn/hostgroup.
        4.  From host/hostgroup, Attempt to override the parameter
        with empty value.

        @assert:

        1.  Error thrown for empty value as the value is required to pass.
        2.  The info icon changed to warning icon for that parameter.
        3.  No matcher for fqdn/hostgroup created inside parameter.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_matcher_from_attribute(self):
        """Impact on parameter on editing the parameter value from attribute.

        @feature: Class Parameters - Outside Impact

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Associate parameter with fqdn/hostgroup.
        3.  Create a matcher for fqdn/hostgroup with valid details.
        4.  From host/hostgroup, edit the parameter value.
        5.  Submit the changes.

        @assert:

        1.  The host/hostgroup is saved with changes.
        2.  Matcher value in parameter is updated from fqdn/hostgroup.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_matcher_from_attribute(self):
        """No Impact on parameter on editing the parameter with
        invalid value from attribute.

        @feature: Class Parameters - Outside Impact

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Associate parameter with fqdn/hostgroup.
        3.  Create a matcher for fqdn/hostgroup with valid details.
        4.  From host/hostgroup, attempt to edit the parameter
        with invalid value.

        @assert:

        1.  Error thrown for invalid value.
        2.  Matcher value in parameter is not updated from fqdn/hostgroup.

        @status: Manual
        """

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1295179)
    @stubbed()
    @tier1
    def test_positive_update_parameter_in_nested_hostgroup(self):
        """Update parameter value in nested hostgroup.

        @feature: Class Parameters - Outside Impact

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Associate parameter with one hostgroup.
        3.  Create a nested hostgroup from above parent hostgroup.
        4.  And Update the value of parameter from nested hostgroup.
        5.  Submit the changes.

        @assert:

        1.  The parameter value updated in nested hostgroup.
        2.  Changes submitted successfully.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_parameter_default_value(self):
        """Hide the default value of parameter.

        @feature: Class Parameters - Value Hiding

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Enter some valid default value.
        3.  Check 'Hidden Value' checkbox.

        @assert:

        1.  The default value shown in hidden state.
        2.  Changes submitted successfully.
        3.  Matcher values shown hidden if any.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_unhide_parameter_default_value(self):
        """Unhide the default value of parameter.

        @feature: Class Parameters - Value Hiding

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Enter some valid default value.
        3.  Hide the value of parameter.
        4.  After hiding, uncheck the 'Hidden Value' checkbox.

        @assert:

        1.  The default value shown in unhidden state.
        2.  Changes submitted successfully.
        3.  Matcher values shown unhidden if any.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_default_value_in_attribute(self):
        """Hide the default value of parameter in attribute.

        @feature: Class Parameters - Value Hiding

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate parameter on host/hostgroup.

        @assert:

        1.  In host/hostgroup, the parameter value shown in hidden state.
        2.  The button for unhiding the value is displayed and accessible.
        3.  The button for overriding the value is displayed and accessible.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_unhide_default_value_in_attribute(self):
        """Unhide the default value of parameter in attribute.

        @feature: Class Parameters - Value Hiding

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate parameter on host/hostgroup.
        6.  In host/hostgroup, Click Unhide button icon.

        @assert:

        1.  In host/hostgroup, the parameter value shown in unhidden state.
        2.  The button for hiding the value is displayed and accessible.
        3.  The button for overriding the value is displayed and accessible.
        4.  In parameter, the default value is still hidden.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_hidden_value_in_parameter(self):
        """Update the hidden default value of parameter.

        @feature: Class Parameters - Value Hiding

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Again update the default value.
        5.  Submit the changes.

        @assert:

        1.  The parameter default value is updated.
        2.  The parameter default value displayed as hidden.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_hidden_value_in_attribute(self):
        """Update the hidden default value of parameter in attribute.

        @feature: Class Parameters - Value Hiding

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate parameter on host/hostgroup.
        6.  In host/hostgroup, update the parameter value.

        @assert:

        1.  In host/hostgroup, the parameter value is updated.
        2.  The parameter Value displayed as hidden.
        3.  In parameter, new matcher created for fqdn/hostgroup.
        4.  And the value shown hidden.

        @status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value.

        @feature: Class Parameters - Value Hiding

        @steps:

        1.  Check the override checkbox for the parameter.
        2.  Don't enter any value, keep blank.
        3.  Check the 'Hidden Value' icon.
        4.  Create a matcher with some value.

        @assert:

        1.  The 'Hidden Value' checkbox is enabled to check.
        2.  The default value shows empty on hide.
        2.  Matcher Value shown as hidden.

        @status: Manual
        """
