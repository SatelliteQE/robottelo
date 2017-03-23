# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Class Parameter

:Requirement: Classparameters

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

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

        :id: e798b1be-b176-48e2-887f-3f3370efef90

        :steps:
            1.  Check the Override checkbox.
            2.  Set the new valid Default Value.
            3.  Submit the changes.

        :expectedresults: Parameter Value overridden with new value.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_override_checkbox(self):
        """Override the Default Parameter value - override Unchecked.

        :id: 3002d976-7c34-4da0-9b43-db28441d94de

        :steps:
            1.  Don't check the Override checkbox.
            2.  Set the new valid Default Value.
            3.  Attempt to submit the changes.

        :expectedresults: Parameter value not allowed/disabled to override.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_edit_parameter_dialog(self):
        """Enable Validation, merging and matcher sections.

        :id: a6639110-1a58-4f68-8265-369b515f9c4a

        :steps: Check the Override checkbox.

        :expectedresults: Puppet Default, Hiding, Validation, Merging and
            Matcher section enabled.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_edit_parameter_dialog(self):
        """Disable Validation, merging and matcher sections.

        :id: 30da3a17-05a5-4c19-8210-80c3a8dcf32b

        :steps: Dont't Check the Override checkbox.

        :expectedresults: Puppet Default, Hiding, Validation, Merging and
            Matcher section is disabled.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_puppet_default(self):
        """On Override, Set Puppet Default Value.

        :id: 49b68cd4-8a4b-4980-b3f0-40678f687fd7

        :steps:
            1.  Check the Override checkbox.
            2.  Check 'Use Puppet Default' checkbox.
            3.  Submit the changes.

        :expectedresults: Puppet Default Value applied on parameter.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_parameter_type(self):
        """Positive Parameter Update for parameter types - Valid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: 5157c174-54f2-422f-8028-89604267c8e8

        :steps:
            1.  Check the Override checkbox.
            2.  Update the Key Type.
            3.  Enter a 'valid' default Value.
            4.  Submit the changes.

        :expectedresults: Parameter Updated with a new type successfully.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_parameter_type(self):
        """Negative Parameter Update for parameter types - Invalid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: 4285b397-0426-4523-8cc2-8e5d79f49aae

        :steps:
            1.  Check the Override checkbox.
            2.  Update the Key Type.
            3.  Enter an 'Invalid' default Value.
            4.  Submit the changes.

        :expectedresults: Parameter not updated with string type for invalid
            value.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_puppet_default_value(self):
        """Validation doesn't works on puppet default value.

        :id: 8671338d-5547-4259-9119-a8952b4d982d

        :steps:
            1.  Check the Override checkbox.
            2.  Check 'Use Puppet Default' value.
            3.  Validate this value under section 'Optional Input Validator'.

        :expectedresults: Validation shouldn't work with puppet default value.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_required_checkbox(self):
        """Error raised for blank default Value - Required checkbox.

        :id: b665891a-15c2-4e7b-a118-f239ff45d37a

        :steps:
            1.  Check the Override checkbox.
            2.  Don't provide any default value, keep blank.
            3.  Check Required checkbox in 'Optional Input Validator'.
            4.  Submit the change.

        :expectedresults: Error raised for blank default value by 'Required'
            checkbox.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_required_checkbox(self):
        """Error not raised for default Value - Required checkbox.

        :id: a4c82c28-8bdf-4c6a-93d6-5d57145f095f

        :steps:
            1.  Check the Override checkbox.
            2.  Provide some default value.
            3.  Check Required checkbox in 'Optional Input Validator'.
            4.  Submit the change.

        :expectedresults: Error not raised default value by 'Required'
            checkbox.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_required_checkbox(self):
        """Error raised for blank matcher Value - Required checkbox.

        :id: e88b1bc7-529a-4dbd-9e43-4738580e12ab

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher for Parameter for some attribute.
            3.  Dont provide Value for matcher. Keep blank.
            4.  Check Required checkbox in 'Optional Input Validator'.
            5.  Submit the change.

        :expectedresults: Error raised for blank matcher value by 'Required'
            checkbox.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_required_checkbox(self):
        """Error not raised for matcher Value - Required checkbox.

        :id: f91d2868-0d87-4cc5-984b-a114badd366f

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher for Parameter for some attribute.
            3.  Provide some Value for matcher.
            4.  Check Required checkbox in 'Optional Input Validator'.
            5.  Submit the change.

        :expectedresults: Error not raised for matcher value by 'Required'
            checkbox.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_with_regex(self):
        """Error raised for default value not matching with regex.

        :id: 1854c189-8a5f-410c-b195-ea2a51e72b30

        :steps:
            1.  Check the Override checkbox.
            2.  Provide default value that doesn't matches the regex of step 3.
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for default value not matching with
            regex.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_with_regex(self):
        """Error not raised for default value matching with regex.

        :id: 81ab3074-dc22-4c60-b638-62fdfabe60fb

        :steps:
            1.  Check the Override checkbox.
            2.  Provide default value that matches the regex of step 3..
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for default value matching with
            regex.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_regex(self):
        """Error raised for matcher value not matching with regex.

        :id: 77e56e9b-ddee-41e8-bd9f-e1a43f5053b2

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher with value that doesn't matches the regex of
                step 3.
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for matcher value not matching with
            regex.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_regex(self):
        """Error not raised for matcher value matching with regex.

        :id: e642fcb1-f1dc-4263-adf1-8f881ce06f68

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher with value that matches the regex of step 3.
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for matcher value matching with
            regex.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_with_list(self):
        """Error raised for default value not in list.

        :id: 3d353610-97cd-45a3-8e99-425bc948ee51

        :steps:
            1.  Check the Override checkbox.
            2.  Provide default value that doesn't matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for default value not in list.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_with_list(self):
        """Error not raised for default value in list.

        :id: 62658cde-becd-4083-ba06-1fd4c8904173

        :steps:
            1.  Check the Override checkbox.
            2.  Provide default value that matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for default value in list.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_list(self):
        """Error raised for matcher value not in list.

        :id: ab8000e9-0110-473e-9c86-eeb709cbfd08

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher with value that doesn't matches the list of
                step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for matcher value not in list.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_list(self):
        """Error not raised for matcher value in list.

        :id: ae5b38e5-f7ea-4325-8a2c-917120470688

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher with value that matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for matcher value in list.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_default_type(self):
        """Error raised for matcher value not of default type.

        :id: 70109667-c72e-4045-92a4-6b8bbbd615eb

        :steps:
            1.  Check the Override checkbox.
            2.  Update parameter default type with valid value.
            3.  Create a matcher with value that doesn't matches the default
                type.
            4.  Submit the change.

        :expectedresults: Error raised for matcher value not of default type.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_default_type(self):
        """No error for matcher value of default type.

        :id: 57d4d82a-fc5b-4d85-8e8e-9a7ca880c5a2

        :steps:
            1.  Check the Override checkbox.
            2.  Update parameter default type with valid value.
            3.  Create a matcher with value that matches the default type.
            4.  Submit the change.

        :expectedresults: Error not raised for matcher value of default type.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_and_default_value(self):
        """Error for invalid default and matcher value both at a time.

        :id: 141b9e6a-7c4c-4ab0-8e30-7c3ddff0b9c8

        :steps:
            1.  Check the Override checkbox.
            2.  Update parameter default type with Invalid value.
            3.  Create a matcher with value that doesn't matches the default
                type.
            4.  Submit the change.

        :expectedresults: Error raised for invalid default and matcher value
            both.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Error while creating matcher for Non Existing Attribute.

        :id: 46fd985d-2e7f-4a8a-8059-0c4d2ffcc8cd

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher with non existing attribute in org.
            3.  Attempt to submit the change.

        :expectedresults: Error raised for non existing attribute.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher(self):
        """Create matcher for attribute in parameter.

        :id: 36ef93af-d79a-4e94-9759-fbdfa77df98b

        :steps:
            1.  Check the Override checkbox.
            2.  Set some default Value.
            3.  Click on 'Add Matcher' button to add matcher.
            4.  Choose valid attribute type, name and value.
            5.  Submit the change.

        :expectedresults: The matcher has been created successfully.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_puppet_default_value(self):
        """Create matcher for attribute in parameter,
        Where Value is puppet default value.

        :id: 656f25cd-4394-414a-bd8e-458f0e51c668

        :steps:
            1.  Check the Override checkbox.
            2.  Set some default Value.
            3.  Click on 'Add Matcher' button to add matcher.
            4.  Choose valid attribute type, name and puppet default value.
            5.  Submit the change.

        :expectedresults: The matcher has been created successfully.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host.

        :id: b83afe54-207e-4d6b-b705-1f3601c484a6

        :steps:
            1.  Check the Override checkbox.
            2.  Set some default Value.
            3.  Set fqdn as top priority attribute.
            4.  Create first matcher for fqdn with valid details.
            5.  Create second matcher for some attribute with valid details.
                Note - The fqdn/host should have this attribute.
            6.  Submit the change.
            7.  Go to YAML output of associated host.

        :expectedresults: The YAML output has the value only for fqdn matcher.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host - alternate priority.

        :id: f494b815-b9fd-4648-b984-e5a07e29b5b9

        :steps:
            1.  Check the Override checkbox.
            2.  Set some default Value.
            3.  Set some attribute(other than fqdn) as top priority attribute.
                Note - The fqdn/host should have this attribute.
            4.  Create first matcher for fqdn with valid details.
            5.  Create second matcher for attribute of step 3 with valid
                details.
            6.  Submit the change.
            7.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the value only for step 5 matcher.
            2.  The YAML output doesn't have value for fqdn/host matcher.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_override(self):
        """Merge the values of all the associated matchers.

        :id: adf9823b-714d-490f-8dfa-f4f9cc888be1

        :steps:
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

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output doesn't have the default value of parameter.
            3.  Duplicate values in YAML output if any are displayed.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_override(self):
        """Attempt to merge the values from non associated matchers.

        :id: 46326bd6-e51f-48e7-87b2-6d65ad602af9

        :steps:
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

        :expectedresults:

            1.  The YAML output has the values only for fqdn.
            2.  The YAML output doesn't have the values for attribute
                which are not associated to host.
            3.  The YAML output doesn't have the default value of parameter.
            4.  Duplicate values in YAML output if any are displayed.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_oveeride_puppet_value(self):
        """Merge the values of all the associated matchers + puppet default value.

        :id: 4eed74ac-0ead-4723-af4d-8638406691f6

        :steps:
            1.  Check the Override checkbox.
            2.  Set some default Value.
            3.  Create first matcher for attribute fqdn with valid details.
            4.  Create second matcher for other attribute with value as puppet
                default.
                Note - The fqdn/host should have this attribute.
            5.  Create more matchers for some more attributes with value as
                puppet default.
                Note - The fqdn/host should have this attributes.
            6.  Select 'Merge overrides' checkbox.
            7.  Select 'Merge default' checkbox.
            8.  Submit the change.
            9.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the value only for fqdn.
            2.  The YAML output doesn't have the puppet default values of
                matchers.
            3.  Duplicate values in YAML output if any are displayed.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_default(self):
        """Merge the values of all the associated matchers + default value.

        :id: b79ce9fd-2497-4f6e-85cc-957077c4f097

        :steps:
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

        :expectedresults:

            1.  The YAML output has the values merged from all
                the associated matchers.
            2.  The YAML output has the default value of parameter.
            3.  Duplicate values in YAML output if any are displayed.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_default(self):
        """Empty default value is not shown in merged values.

        :id: b9c46949-34ea-4edd-ac3f-53708bf7885d

        :steps:
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

        :expectedresults:

            1.  The YAML output has the values merged from all
                the associated matchers.
            2.  The YAML output doesn't have the empty default value of
                parameter.
            3.  Duplicate values in YAML output if any are displayed.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_puppet_default(self):
        """Merge the values of all the associated matchers + puppet default value.

        :id: 8e9075c1-adc5-474e-8aa3-4252f507c155

        :steps:
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

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output doesn't have the puppet default value.
            3.  Duplicate values in YAML output if any are displayed.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_avoid_duplicate(self):
        """Merge the values of all the associated matchers, remove duplicates.

        :id: c8557813-2c09-4196-b1c1-f7e609aa0310

        :steps:
            1.  Check the Override checkbox.
            2.  Set some default Value of array type.
            3.  Create first matcher for attribute fqdn with some value.
            4.  Create second matcher for other attribute with same value as
                fqdn matcher.
                Note - The fqdn/host should have this attribute.
            5.  Select 'Merge overrides' checkbox.
            6.  Select 'Merge default' checkbox.
            7.  Select 'Avoid Duplicates' checkbox.
            8.  Submit the change.
            9.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output has the default value of parameter.
            3.  Duplicate values in YAML output are removed / not displayed.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_avoid_duplicate(self):
        """Duplicates not removed as they were not really present.

        :id: f7a34928-c3a3-4b85-907b-f95c26240652

        :steps:
            1.  Check the Override checkbox.
            2.  Set some default Value of array type.
            3.  Create first matcher for attribute fqdn with some value.
            4.  Create second matcher for other attribute with other value than
                fqdn matcher and default value.
                Note - The fqdn/host should have this attribute.
            5.  Select 'Merge overrides' checkbox.
            6.  Select 'Merge default' checkbox.
            7.  Select 'Avoid Duplicates' checkbox.
            8.  Submit the change.
            9.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all matchers.
            2.  The YAML output has the default value of parameter.
            3.  No value removed as duplicate value.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_enable_merge_overrides_default_checkboxes(self):
        """Enable Merge Overrides, Merge Default checkbox for supported types.

        :id: d6323648-4720-4c33-b25f-2b2b569d9df0

        :steps:
            1.  Check the Override checkbox.
            2.  Set parameter type to array/hash.

        :expectedresults: The Merge Overrides, Merge Default checkbox are
            enabled to check.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_merge_overrides_default_checkboxes(self):
        """Disable Merge Overrides, Merge Default checkboxes for non supported types.

        :id: 58e42a4d-fabb-4a93-8787-3399cd6d3394

        :steps:
            1.  Check the Override checkbox.
            2.  Set parameter type other than array/hash.

        :expectedresults: The Merge Overrides, Merge Default checkboxes are not
            enabled to check.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_enable_avaoid_duplicates_checkbox(self):
        """Enable Avoid duplicates checkbox for supported type- array.

        :id: 77eaa0b6-4388-4e49-88cd-b059d0c53e02

        :steps:
            1.  Check the Override checkbox.
            2.  Set parameter type to array.
            3.  Check Merge Overrides checkbox.

        :expectedresults: The Avoid Duplicates checkbox is enabled to check.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_avaoid_duplicates_checkbox(self):
        """Disable Avoid duplicates checkbox for non supported types.

        :id: 2b69cec7-1136-4566-9c75-80c71e917fbf

        :steps:
            1.  Check the Override checkbox.
            2.  Set parameter type other than array.

        :expectedresults: 1.  The Merge Overrides checkbox is only enabled to
            check for type hash. 2.  The Avoid duplicates checkbox not enabled
            to check for any type than array.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_impact_parameter_delete_attribute(self):
        """Impact on parameter after deleting associated attribute.

        :id: 5d9bed6d-d9c0-4eb3-aaf7-bdda1f9203dd

        :steps:
            1.  Override the parameter and create a matcher for some attribute.
            2.  Delete the attribute.
            3.  Recreate the attribute with same name as earlier.

        :expectedresults: 1.  The matcher for deleted attribute removed from
            parameter. 2.  On recreating attribute, the matcher should not
            reappear in parameter.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_override_from_attribute(self):
        """Impact on parameter on overriding the parameter value from attribute.

        :id: dcc8a9f5-191d-42d1-bff5-3083cc46cce1

        :steps:
            1.  Check the override checkbox for the parameter.
            2.  Associate parameter with fqdn/hostgroup.
            3.  From host/hostgroup, override the parameter value.
            4.  Submit the changes.

        :expectedresults: 1.  The host/hostgroup is saved with changes. 2.  New
            matcher for fqdn/hostgroup created inside parameter.
            :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_override_from_attribute(self):
        """No impact on parameter on overriding the parameter
        with invalid value from attribute.

        :id: 475d71cc-d52c-4a94-adb6-27ea52493176

        :steps:
            1.  Check the override checkbox for the parameter.
            2.  Associate parameter with fqdn/hostgroup.
            3.  From host/hostgroup, Attempt to override the parameter with
                some other key type of value.
        :expectedresults: 1.  Error thrown for invalid type value. 2.  No
            matcher for fqdn/hostgroup is created inside parameter.
            :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_override_from_attribute_puppet_default(self):
        """Impact on parameter on overriding the parameter value
        from attribute - puppet default.

        :id: 2a013541-a4f2-4b54-b6ab-52932b17eb4a

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Associate parameter with fqdn/hostgroup.
            3.  From host/hostgroup, override the parameter value as puppet
                default value.
            4.  Submit the changes.

        :expectedresults:

            1.  The host/hostgroup is saved with changes.
            2.  New matcher for fqdn/hostgroup created inside parameter.
            3.  In matcher, 'Use Puppet Default' checkbox is checked.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_override_from_attribute_required_checked(self):
        """Error for empty value on overriding the parameter value
        from attribute - Required checked.

        :id: c4fadfa6-0747-475f-8fc5-227c147d585a

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Check 'Required' checkbox in parameter.
            3.  Associate parameter with fqdn/hostgroup.
            4.  From host/hostgroup, Attempt to override the parameter with
                empty value.

        :expectedresults:

            1.  Error thrown for empty value as the value is required to pass.
            2.  The info icon changed to warning icon for that parameter.
            3.  No matcher for fqdn/hostgroup created inside parameter.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_matcher_from_attribute(self):
        """Impact on parameter on editing the parameter value from attribute.

        :id: a7b3ecde-a311-421c-be4b-0f72ab1f44ba

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Associate parameter with fqdn/hostgroup.
            3.  Create a matcher for fqdn/hostgroup with valid details.
            4.  From host/hostgroup, edit the parameter value.
            5.  Submit the changes.

        :expectedresults:

            1.  The host/hostgroup is saved with changes.
            2.  Matcher value in parameter is updated from fqdn/hostgroup.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_matcher_from_attribute(self):
        """No Impact on parameter on editing the parameter with
        invalid value from attribute.

        :id: 554de8b7-0ddb-4f2e-b406-882b13eac882

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Associate parameter with fqdn/hostgroup.
            3.  Create a matcher for fqdn/hostgroup with valid details.
            4.  From host/hostgroup, attempt to edit the parameter with invalid
                value.

        :expectedresults:

            1.  Error thrown for invalid value.
            2.  Matcher value in parameter is not updated from fqdn/hostgroup.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1295179)
    @stubbed()
    @tier1
    def test_positive_update_parameter_in_nested_hostgroup(self):
        """Update parameter value in nested hostgroup.

        :id: 9aacec96-593c-4089-ad14-d4bbbbd43ef8

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Associate parameter with one hostgroup.
            3.  Create a nested hostgroup from above parent hostgroup.
            4.  And Update the value of parameter from nested hostgroup.
            5.  Submit the changes.

        :expectedresults:

            1.  The parameter value updated in nested hostgroup.
            2.  Changes submitted successfully.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_parameter_default_value(self):
        """Hide the default value of parameter.

        :id: 8b3d294e-58e7-454c-b19e-ead1c6a6a342

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Enter some valid default value.
            3.  Check 'Hidden Value' checkbox.

        :expectedresults:

            1.  The default value shown in hidden state.
            2.  Changes submitted successfully.
            3.  Matcher values shown hidden if any.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_unhide_parameter_default_value(self):
        """Unhide the default value of parameter.

        :id: fca478b9-eeb9-41ea-8c41-2d9601f4ea4f

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Enter some valid default value.
            3.  Hide the value of parameter.
            4.  After hiding, uncheck the 'Hidden Value' checkbox.

        :expectedresults:

            1.  The default value shown in unhidden state.
            2.  Changes submitted successfully.
            3.  Matcher values shown unhidden if any.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_default_value_in_attribute(self):
        """Hide the default value of parameter in attribute.

        :id: a44d35df-877c-469b-b82c-e5f85e592e8d

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Enter some valid default value.
            3.  Hide the default Value.
            4.  Submit the changes.
            5.  Associate parameter on host/hostgroup.

        :expectedresults:

            1.  In host/hostgroup, the parameter value shown in hidden state.
            2.  The button for unhiding the value is displayed and accessible.
            3.  The button for overriding the value is displayed and
                accessible.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_unhide_default_value_in_attribute(self):
        """Unhide the default value of parameter in attribute.

        :id: 76611ba0-e583-4c4b-b794-005a21240d26

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Enter some valid default value.
            3.  Hide the default Value.
            4.  Submit the changes.
            5.  Associate parameter on host/hostgroup.
            6.  In host/hostgroup, Click Unhide button icon.

        :expectedresults:

            1.  In host/hostgroup, the parameter value shown in unhidden state.
            2.  The button for hiding the value is displayed and accessible.
            3.  The button for overriding the value is displayed and
                accessible.
            4.  In parameter, the default value is still hidden.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_hidden_value_in_parameter(self):
        """Update the hidden default value of parameter.

        :id: e7a6e172-d0b9-48e4-81ae-16d866d6f63b

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Enter some valid default value.
            3.  Hide the default Value.
            4.  Again update the default value.
            5.  Submit the changes.

        :expectedresults:

            1.  The parameter default value is updated.
            2.  The parameter default value displayed as hidden.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_hidden_value_in_attribute(self):
        """Update the hidden default value of parameter in attribute.

        :id: c10c20bd-0284-4e5d-b789-fddd3b81b81b

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Enter some valid default value.
            3.  Hide the default Value.
            4.  Submit the changes.
            5.  Associate parameter on host/hostgroup.
            6.  In host/hostgroup, update the parameter value.

        :expectedresults:

            1.  In host/hostgroup, the parameter value is updated.
            2.  The parameter Value displayed as hidden.
            3.  In parameter, new matcher created for fqdn/hostgroup.
            4.  And the value shown hidden.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value.

        :id: 8b02e575-c7bf-45d1-a5eb-4640b65a4d60

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Don't enter any value, keep blank.
            3.  Check the 'Hidden Value' icon.
            4.  Create a matcher with some value.

        :expectedresults:

            1.  The 'Hidden Value' checkbox is enabled to check.
            2.  The default value shows empty on hide.
            3.  Matcher Value shown as hidden.

        :caseautomation: notautomated

        :CaseLevel: System
        """
