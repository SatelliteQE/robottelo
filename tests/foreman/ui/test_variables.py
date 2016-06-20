# -*- encoding: utf-8 -*-
"""Test class for Puppet Smart Variables

@Requirement: Variables

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier3
)
from robottelo.test import UITestCase


class SmartVariablesTestCase(UITestCase):
    """Implements Smart Variables tests in UI"""

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create(self):
        """Create a Smart Variable.

        @id: 4a8589bf-7b11-48e8-a25d-984bea2ba676

        @steps:

        1. Create a smart Variable with Valid name and default value.

        @assert:

        1. The smart Variable is created successfully.
        2. In YAML output of associated host, the variable with name and its
        default value is displayed.
        3. In Host-> variables tab, the smart variable should be displayed with
        its respective puppet class.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create(self):
        """Smart Variable is not created with invalid data.

        @id: 09a67cb6-5de0-41b3-90f4-593323936c6c

        @steps:

        1. Create a smart Variable with Invalid name and valid default value.

        @assert:

        1. Error is displayed for invalid variable name.
        2. The smart Variable is not created.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_delete_smart_variables_menu(self):
        """Delete a Smart Variable from Smart Variables Menu.

        @id: 19fedbdf-48a1-46a7-b184-615a0efd7b4e

        @steps:

        1. Delete a smart Variable from Configure - Smart Variables menu.

        @assert:

        1. The smart Variable is deleted successfully.
        2. In YAML output of associated Host, the variable should be removed.
        3. In Host-> variables tab, the smart variable should be removed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_variable_puppet_class(self):
        """Update Smart Variable's puppet class.

        @id: 6c3e2da9-420c-4e39-8b71-e5be6b605bd7

        @steps:

        1. In Puppet class, Create a smart Variable with Valid name and
        default value.
        2. After successful creation, Update the puppet class of variable.

        @assert:

        1. The variable is updated with new puppet class.
        2. In Host/HostGroup -> variables tab, the smart variable is updated
        with its newly updated puppet class.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_globality(self):
        """Smart Variable with same names are not allowed.

        @id: 7f37194d-4a12-437b-a284-3350cf048eea

        @steps:

        1. In Puppet class, Create a smart Variable with Valid name and
        default value.
        2. After successful creation, Attempt to create a variable with
        same name from same/other class.

        @assert:

        1. An Error is displayed in front of Variable Key field as
        'has already been taken'.
        2. The variable with same name are not allowed to create from
        any class.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_type(self):
        """Variable is Updated for variable types - Valid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        @id: d89cdd32-dd2b-46fe-bcc2-8c66d92cc6f8

        @steps:

        1.  Update the Key Type.
        2.  Enter a 'valid' default Value.
        3.  Submit the changes.

        @assert: Variable is Updated with a new type successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_type(self):
        """Variable not updated for variable types - Invalid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        @id: d64d1b6d-028a-4782-a6d4-e3029d7118b6

        @steps:

        1.  Update the Key Type.
        2.  Enter an 'Invalid' default Value.
        3.  Submit the changes.

        @assert: Variable is not updated with new type for invalid value.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_required_checkbox(self):
        """Error is raised for blank default Value - Required checkbox.

        @id: cdbe5feb-daf1-49c4-98c0-5bbbd436c3e8

        @steps:

        1.  Create a variable with empty value.
        2.  Check Required checkbox in 'Optional Input Validator'.
        3.  Submit the change.

        @assert: Error is raised for blank default value by 'Required'
        checkbox.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_required_checkbox(self):
        """Error is not raised for default Value - Required checkbox.

        @id: 09e42df9-2fe1-444f-a603-6f7b6b3f127e

        @steps:

        1.  Provide some default value.
        2.  Check Required checkbox in 'Optional Input Validator'.
        3.  Submit the change.

        @assert: Error is not raised default value by 'Required' checkbox.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_required_checkbox(self):
        """Error is raised for blank matcher Value - Required checkbox.

        @id: 7e02efb6-e1a2-4872-877a-78075b2de182

        @steps:

        1.  Create a matcher for variable for some attribute.
        2.  Dont provide Value for matcher. Keep blank.
        3.  Check Required checkbox in 'Optional Input Validator'.
        4.  Submit the change.

        @assert: Error is raised for blank matcher value by 'Required'
        checkbox.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_required_checkbox(self):
        """Error is not raised for matcher Value - Required checkbox.

        @id: 6c742180-ddb1-4cd0-a04c-911b2a8f4ea4

        @steps:

        1.  Create a matcher for variable for some attribute.
        2.  Provide some Value for matcher.
        3.  Check Required checkbox in 'Optional Input Validator'.
        4.  Submit the change.

        @assert: Error is not raised for matcher value by 'Required' checkbox.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_with_regex(self):
        """Error is raised for default value not matching with regex.

        @id: 5285b784-e02c-4f3b-a053-93b36bf9fbfc

        @steps:

        1.  Provide default value that doesn't match the regex of step 2.
        2.  Validate this value with regex validator type and rule.
        3.  Submit the change.

        @assert: Error is raised for default value not matching with regex.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_with_regex(self):
        """Error is not raised for default value matching with regex.

        @id: 7a329b05-7efd-42d2-b472-1a36d0ee6464

        @steps:

        1.  Provide default value that matches the regex of step 2.
        2.  Validate this value with regex validator type and rule.
        3.  Submit the change.

        @assert: Error is not raised for default value matching with regex.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_regex(self):
        """Error is raised for matcher value not matching with regex.

        @id: b8e039b3-2491-4dba-a91b-a4aa3fc7f544

        @steps:

        1.  Create a matcher with value that doesn't match the regex of step 2.
        2.  Validate this value with regex validator type and rule.
        3.  Submit the change.

        @assert: Error is raised for matcher value not matching with regex.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_regex(self):
        """Error is not raised for matcher value matching with regex.

        @id: 04a8f849-6323-4e54-9f07-fb750b911a4c

        @steps:

        1.  Create a matcher with value that matches the regex of step 2.
        2.  Validate this value with regex validator type and rule.
        3.  Submit the change.

        @assert: Error is not raised for matcher value matching with regex.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_with_list(self):
        """Error is raised for default value not in list.

        @id: d1aa9149-9025-4492-95d0-e72aec8eadc3

        @steps:

        1.  Provide default value that doesn't match the list of step 2.
        2.  Validate this value with list validator type and rule.
        3.  Submit the change.

        @assert: Error is raised for default value not in list.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_with_list(self):
        """Error is not raised for default value in list.

        @id: 5ea443f2-ec91-4986-b97c-1c28fb862e1c

        @steps:

        1.  Provide default value that matches the list of step 2.
        2.  Validate this value with list validator type and rule.
        3.  Submit the change.

        @assert: Error is not raised for default value in list.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_list(self):
        """Error is raised for matcher value not in list.

        @id: 87d128b9-c7f7-4396-b162-60021b0ef682

        @steps:

        1.  Create a matcher with value that doesn't match
        the list of step 2.
        2.  Validate this value with list validator type and rule.
        3.  Submit the change.

        @assert: Error is raised for matcher value not in list.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_list(self):
        """Error is not raised for matcher value in list.

        @id: ac91eaf5-2a15-4d54-b078-a37b60074287

        @steps:

        1.  Create a matcher with value that matches the list of step 2.
        2.  Validate this value with list validator type and rule.
        3.  Submit the change.

        @assert: Error is not raised for matcher value in list.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_default_type(self):
        """Error is raised for matcher value not of default type.

        @id: 466197ea-44f0-46d0-b111-686b72183fe5

        @steps:

        1.  Update variable default type with valid value.
        2.  Create a matcher with value that doesn't match the default type.
        3.  Submit the change.

        @assert: Error is raised for matcher value not of default type.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_default_type(self):
        """No error for matcher value of default type.

        @id: 033bf7d8-a488-49c1-b900-9e7169e945e0

        @steps:

        1.  Update variable default type with valid value.
        2.  Create a matcher with value that matches the default type.
        3.  Submit the change.

        @assert: Error is not raised for matcher value of default type.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_and_default_value(self):
        """Error for invalid default and matcher value both at a time.

        @id: 9f5987d1-ac40-4031-bcfe-979dc95866d3

        @steps:

        1.  Update variable default type with Invalid value.
        2.  Create a matcher with value that doesn't match the default type.
        3.  Submit the change.

        @assert: Error is raised for invalid default and matcher value both.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Error while creating matcher for Non Existing Attribute.

        @id: 27ef1ef0-1c89-47eb-89e0-3da161154513

        @steps:

        1.  Create a matcher with non existing attribute in org.
        2.  Attempt to submit the change.

        @assert: Error is raised for non existing attribute.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1259174)
    @stubbed()
    @tier1
    def test_positive_create_matcher(self):
        """Create a Smart Variable with matcher.

        @id: 42113584-d2db-4b91-8775-06bffee36be4

        @steps:

        1. Create a smart Variable with Valid name and default value.
        2. Create a matcher for Host with valid value.

        @assert:

        1. The smart Variable with matcher is created successfully.
        2. In YAML output, the variable name with overrided value for
        host is displayed.
        3. In Host-> variables tab, the variable name with overrided value
        for host is displayed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host.

        @id: 65144295-f0ca-4bd0-ae01-96c50ca829fe

        @steps:

        1.  Create variable with some default value.
        2.  Set fqdn as top priority attribute.
        3.  Create first matcher for fqdn with valid details.
        4.  Create second matcher for some attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5.  Submit the change.
        6.  Go to YAML output of associated host.

        @assert: The YAML output has the value only for fqdn matcher.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host - alternate priority.

        @id: 7e52b054-4fcb-4c58-ae49-0d3348d14570

        @steps:

        1.  Create variable with some default value.
        2.  Set some attribute(other than fqdn) as top priority attribute.
        Note - The fqdn/host should have this attribute.
        3.  Create first matcher for fqdn with valid details.
        4.  Create second matcher for attribute of step 3 with valid details.
        5.  Submit the change.
        6.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the value only for step 5 matcher.
        2.  The YAML output doesn't have value for fqdn/host matcher.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_override(self):
        """Merge the values of all the associated matchers.

        @id: b9c9b1c7-ff9a-4080-aeee-3b61b5414332

        @steps:

        1.  Create variable with some default value.
        2.  Create first matcher for attribute fqdn with valid details.
        3.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        4.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        5.  Select 'Merge overrides' checkbox.
        6.  Submit the change.
        7.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all the associated
        matchers.
        2.  The YAML output doesn't have the default value of variable.
        3.  Duplicate values in YAML output if any are displayed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_override(self):
        """Attempt to merge the values from non associated matchers.

        @id: 3cc2a7b3-7b46-4c8c-b719-79c004ae04c6

        @steps:

        1.  Create variable with some default value.
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
        3.  The YAML output doesn't have the default value of variable.
        4.  Duplicate values in YAML output if any are displayed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_default(self):
        """Merge the values of all the associated matchers + default value.

        @id: 21d8fde8-0844-4384-b86a-30547c82b221

        @steps:

        1.  Create variable with some default value.
        2.  Create first matcher for attribute fqdn with valid details.
        3.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        4.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        5.  Select 'Merge overrides' checkbox.
        6.  Select 'Merge default' checkbox.
        7.  Submit the change.
        8.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all
        the associated matchers.
        2.  The YAML output has the default value of variable.
        3.  Duplicate values in YAML output if any are displayed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_default(self):
        """Empty default value is not shown in merged values.

        @id: 98f8fe63-d125-4d27-a15a-2550c9e5f0ff

        @steps:

        1.  Create variable with some default value.
        2.  Create first matcher for attribute fqdn with valid details.
        3.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        4.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        5.  Select 'Merge overrides' checkbox.
        6.  Select 'Merge default' checkbox.
        7.  Submit the change.
        8.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all
        the associated matchers.
        2.  The YAML output doesn't have the empty default value of variable.
        3.  Duplicate values in YAML output if any are displayed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_avoid_duplicate(self):
        """Merge the values of all the associated matchers, remove duplicates.

        @id: 75fc514f-70dd-4cc1-8069-221e9edda89a

        @steps:

        1.  Create variable with type array and value.
        2.  Create first matcher for attribute fqdn with some value.
        3.  Create second matcher for other attribute with
        same value as fqdn matcher.
        Note - The fqdn/host should have this attribute.
        4.  Select 'Merge overrides' checkbox.
        5.  Select 'Merge default' checkbox.
        6.  Select 'Avoid Duplicates' checkbox.
        7.  Submit the change.
        8.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all
        the associated matchers.
        2.  The YAML output has the default value of variable.
        3.  Duplicate values in YAML output are removed / not displayed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_avoid_duplicate(self):
        """Duplicates not removed as they were not really present.

        @id: 050c7cef-eed6-4a61-b567-371f398647a2

        @steps:

        1.  Create variable with type array and value.
        2.  Create first matcher for attribute fqdn with some value.
        3.  Create second matcher for other attribute with other value
        than fqdn matcher and default value.
        Note - The fqdn/host should have this attribute.
        4.  Select 'Merge overrides' checkbox.
        5.  Select 'Merge default' checkbox.
        6.  Select 'Avoid Duplicates' checkbox.
        7.  Submit the change.
        8.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all matchers.
        2.  The YAML output has the default value of variable.
        3.  No value removed as duplicate value.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_enable_merge_overrides_default_checkboxes(self):
        """Enable Merge Overrides, Merge Default checkbox for supported types.

        @id: a86b3f97-f491-444b-ab7f-85218689e97f

        @steps:

        1.  Set variable type to array/hash.

        @assert: The Merge Overrides, Merge Default checkbox
        are enabled to check.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_merge_overrides_default_checkboxes(self):
        """Disable Merge Overrides, Merge Default checkboxes for non supported types.

        @id: 834af938-e056-4a40-8831-91f6400aedd3

        @steps:

        1.  Set variable type other than array/hash.

        @assert: The Merge Overrides, Merge Default checkboxes
        are not enabled to check.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_enable_avoid_duplicates_checkbox(self):
        """Enable Avoid duplicates checkbox for supported type- array.

        @id: 8856afbf-67cd-4470-9527-34bb0b2962e3

        @steps:

        1.  Set variable type to array.
        2.  Check Merge Overrides checkbox.

        @assert: The Avoid Duplicates checkbox is enabled to check.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_avaoid_duplicates_checkbox(self):
        """Disable Avoid duplicates checkbox for non supported types.

        @id: 8dc28e77-584a-46f9-aed7-dcc3345a2d9b

        @steps:

        1.  Set variable type other than array.

        @assert:

        1.  The Merge Overrides checkbox is only enabled to check
        for type hash.
        2.  The Avoid duplicates checkbox not enabled to check
        for any type than array.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_impact_delete_attribute(self):
        """Impact on variable after deleting associated attribute.

        @id: 26ce3c25-0deb-415d-a2f5-0eacaf354f92

        @steps:

        1.  Create a variable with matcher
        for some attribute.
        2.  Delete the attribute.
        3.  Recreate the attribute with same name as earlier.

        @assert:

        1.  The matcher for deleted attribute removed from variable.
        2.  On recreating attribute, the matcher should not
        reappear in variable.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_override_from_attribute(self):
        """Impact on variable on overriding the variable value from attribute.

        @id: 0d4a6b5f-09d8-4d64-ae4b-efa152815ea8

        @steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  From host/hostgroup, override the variable value.
        4.  Submit the changes.

        @assert:

        1.  The host/hostgroup is saved with changes.
        2.  New matcher for fqdn/hostgroup created inside variable.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_override_from_attribute(self):
        """No impact on variable on overriding the variable
        with invalid value from attribute.

        @id: 18071443-a511-49c4-9ca9-04c7594b831d

        @steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  From host/hostgroup, Attempt to override the variable with
        some other key type of value.

        @assert:

        1.  Error thrown for invalid type value.
        2.  No matcher for fqdn/hostgroup is created inside variable.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_override_from_attribute_required_checked(self):
        """Error for empty value on overriding the variable value
        from attribute - Required checked.

        @id: b0756aa8-3e9b-446d-b5dd-8205b2a9218d

        @steps:

        1.  Create a variable.
        2.  Check 'Required' checkbox in variable.
        3.  Associate variable with fqdn/hostgroup.
        4.  From host/hostgroup, Attempt to override the variable
        with empty value.

        @assert:

        1.  Error thrown for empty value as the value is required to pass.
        2.  The info icon changed to warning icon for that variable.
        3.  No matcher for fqdn/hostgroup created inside variable.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_matcher_from_attribute(self):
        """Impact on variable on editing the variable value from attribute.

        @id: e98a8404-5e32-4d2e-af81-4339d214658a

        @steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  Create a matcher for fqdn/hostgroup with valid details.
        4.  From host/hostgroup, edit the variable value.
        5.  Submit the changes.

        @assert:

        1.  The host/hostgroup is saved with changes.
        2.  Matcher value in variable is updated from fqdn/hostgroup.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_matcher_from_attribute(self):
        """No Impact on variable on editing the variable with
        invalid value from attribute.

        @id: bd4a2535-57dd-49a8-b8b5-c5e8de652aa7

        @steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  Create a matcher for fqdn/hostgroup with valid details.
        4.  From host/hostgroup, attempt to edit the variable
        with invalid value.

        @assert:

        1.  Error thrown for invalid value.
        2.  Matcher value in variable is not updated from fqdn/hostgroup.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_default_value(self):
        """Hide the default value of variable.

        @id: cd2ec5a5-4bf1-4239-9b3a-8fbca02d7070

        @steps:

        1.  Create a variable.
        2.  Enter some valid default value.
        3.  Check 'Hidden Value' checkbox.

        @assert:

        1.  The default value shown in hidden state.
        2.  Changes submitted successfully.
        3.  Matcher values shown hidden if any.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_unhide_default_value(self):
        """Unhide the default value of variable.

        @id: 708fbd15-5177-4eb5-800a-4266e2476439

        @steps:

        1.  Create a variable.
        2.  Enter some valid default value.
        3.  Hide the value of variable.
        4.  After hiding, uncheck the 'Hidden Value' checkbox.

        @assert:

        1.  The default value shown in unhidden state.
        2.  Changes submitted successfully.
        3.  Matcher values shown unhidden if any.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_default_value_in_attribute(self):
        """Hide the default value of variable in attribute.

        @id: 3b9661f9-f7f7-4dbe-8b08-1a712db6a83d

        @steps:

        1.  Create a variable.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate variable on host/hostgroup.

        @assert:

        1.  In host/hostgroup, the variable value shown in hidden state.
        2.  The button for unhiding the value is displayed and accessible.
        3.  The button for overriding the value is displayed and accessible.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_unhide_default_value_in_attribute(self):
        """Unhide the default value of variable in attribute.

        @id: 5d7c1eb2-3f98-4dfd-aac0-ff740b7f82ec

        @steps:

        1.  Create a variable.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate variable on host/hostgroup.
        6.  In host/hostgroup, Click Unhide button icon.

        @assert:

        1.  In host/hostgroup, the variable value shown in unhidden state.
        2.  The button for hiding the value is displayed and accessible.
        3.  The button for overriding the value is displayed and accessible.
        4.  In variable, the default value is still hidden.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_hidden_value(self):
        """Update the hidden default value of variable.

        @id: b56e2b84-ba31-4fd2-b65a-ac9f3eb1c1e1

        @steps:

        1.  Create a variable.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Again update the default value.
        5.  Submit the changes.

        @assert:

        1.  The variable default value is updated.
        2.  The variable default value displayed as hidden.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_hidden_value_in_attribute(self):
        """Update the hidden default value of variable in attribute.

        @id: 2f506d47-aed5-45ad-a6fb-133ece18eb14

        @steps:

        1.  Create a variable.
        2.  Enter some valid default value.
        3.  Hide the default Value.
        4.  Submit the changes.
        5.  Associate variable on host/hostgroup.
        6.  In host/hostgroup, update the variable value.

        @assert:

        1.  In host/hostgroup, the variable value is updated.
        2.  The variable Value displayed as hidden.
        3.  In variable, new matcher created for fqdn/hostgroup.
        4.  And the value shown hidden.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value.

        @id: ee96bc8c-5294-4580-8316-e62e72e9e3ea

        @steps:

        1.  Create a variable.
        2.  Don't enter any value, keep blank.
        3.  Check the 'Hidden Value' icon.
        4.  Create a matcher with some value.

        @assert:

        1.  The 'Hidden Value' checkbox is enabled to check.
        2.  The default value shows empty on hide.
        2.  Matcher Value shown as hidden.

        @caseautomation: notautomated

        @CaseLevel: System
        """
