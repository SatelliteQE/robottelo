# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Class Parameter"""

from robottelo.decorators import run_only_on, stubbed, tier1, tier3
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
