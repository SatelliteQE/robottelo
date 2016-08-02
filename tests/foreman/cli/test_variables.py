# -*- encoding: utf-8 -*-
"""Test class for Puppet Smart Variables

@Requirement: Variables

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier1,
    tier2,
    tier3
)
from robottelo.test import CLITestCase


class SmartVariablesTestCase(CLITestCase):
    """Implements Smart Variables tests in CLI"""

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_list_variables_by_host_name(self):
        """List all smart variables associated to host by hostname.

        @id: ee0da54c-ab60-4dde-8e1f-d548b52bac73

        @steps: List all the smart variables associated to specific host by
        hostname.

        @assert: Smart Variables listed for specific Host by hostname.

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_list_variables_by_host_id(self):
        """List all smart variables associated to host by host id.

        @id: ee2e994b-2a6d-4069-a2f7-e244a3134772

        @steps: List all the smart variables associated to specific host by
        host id.

        @assert: Smart Variables listed for specific Host by host id.

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_list_variables_by_hostgroup_name(self):
        """List all smart variables associated to hostgroup by hostgroup name

        @id: cb69abe0-2349-4114-91e9-ef93f261dc50

        @steps: List all smart variables associated to hostgroup by hostgroup
        name.

        @assert: Smart Variables listed for specific HostGroup by hostgroup
        name.

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_list_variables_by_hostgroup_id(self):
        """List all smart variables associated to hostgroup by hostgroup id

        @id: 0f167c4c-e4de-4b66-841f-d5a9e410391e

        @steps: List all smart variables associated to hostgroup by hostgroup
        id.

        @assert: Smart Variables listed for specific HostGroup by hostgroup id.

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_list_variables_by_puppetclass_name(self):
        """List all smart variables associated to puppet class by puppet class
        name.

        @id: 43b795c2-a64d-4a84-bb35-1e8fd0e1a0c9

        @steps: List all smart variables associated to puppet class by puppet
        class name.

        @assert: Smart Variables listed for specific puppet class by puppet
        class name.

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_list_variables_by_puppetclass_id(self):
        """List all smart variables associated to puppet class by puppet class
        id.

        @id: 57d290e8-2ae2-4c09-ab1e-7c7914bc4ba8

        @steps: List all smart variables associated to puppet class by puppet
        class id.

        @assert: Smart Variables listed for specific puppet class by puppet
        class id.

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create(self):
        """Create a Smart Variable.

        @id: 8be9ed26-9a27-42a8-8edd-b255637f205e

        @steps:

        1. Create a smart Variable with Valid name and default value.

        @assert: The smart Variable is created successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create(self):
        """Create Smart Variable with invalid name.

        @id: 3f71f39f-4178-42e7-be40-2a3538361466

        @steps:

        1. Create a smart Variable with Invalid name and valid default value.

        @assert: The smart Variable is not created.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_delete_smart_variable_by_id(self):
        """Delete a Smart Variable by id.

        @id: b0c4f7f0-d568-411f-94c2-fa525f36a8fd

        @steps:

        1. Delete a smart Variable by id.

        @assert: The smart Variable is deleted successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_delete_smart_variable_by_name(self):
        """Delete a Smart Variable by name.

        @id: 52900000-d7e1-4f0c-b67e-a2a1d25fc76e

        @steps:

        1. Delete a smart Variable by name.

        @assert: The smart Variable is deleted successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_variable_puppet_class(self):
        """Update Smart Variable's puppet class.

        @id: 0f2d617b-c9ec-46e9-ac84-7a0d59a84811

        @steps:

        1. Create a smart variable with valid name and default value.
        2. Add this variable to some host/hostgroup.
        3. Update the puppet class associated to the smart variable created in
        step1.

        @assert: The variable is updated with new puppet class.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_duplicate_name_variable(self):
        """Create Smart Variable with an existing name.

        @id: cc219111-1d2a-47ae-9b22-0b399f2d586d

        @steps:

        1. Create a smart Variable with Valid name and default value.
        2. Attempt to create a variable with same name from same/other class.

        @assert: The variable with same name are not allowed to create from
        any class.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_type(self):
        """Create smart variable with all valid key types and values.

        Types - string, boolean, integer, real, array, hash, yaml, json

        @id: 63d9c79a-5d54-44f8-b36d-45eb183cb148

        @steps:

        1.  Create a variable with valid key type and default value.

        @assert: Variable is created with a new type successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_type(self):
        """Create smart variable with all valid key types but invalid values.

        Types - string, boolean, integer, real, array, hash, yaml, json

        @id: aab8423e-3857-4ac9-9f18-aec64f95a90d

        @steps:

        1.  Create a variable with valid key type and invalid default value.

        @assert: Variable is not created with new type for invalid value.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_empty_matcher_value(self):
        """Create matcher with empty value for string type.

        @id: 00fe9a2b-a4c0-4f3e-9bc3-db22f8625005

        @steps: Create a matcher for variable with type string and empty value

        @assert: Matcher is created with empty value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_empty_matcher_value(self):
        """Create matcher with empty value for non string type.

        @id: 677a0881-c42a-4063-ac7b-7e7d9b5bc307

        @steps: Create a matcher for variable with type other than string and
        empty value

        @assert: Matcher is not created with empty value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_validate_default_value_with_regex(self):
        """Test variable is not created for unmatched validator type regex.

        @id: f728ea2c-f7f4-4d9b-8c92-9681e0b21769

        @steps:

        1.  Create a variable with value that doesn't match the regex of step 2
        2.  Validate this value with regex validator type and valid rule.

        @assert: Variable is not created for unmatched validator rule.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_validate_default_value_with_regex(self):
        """Test variable is created for matched validator type regex.

        @id: f720c888-0ed0-4d32-bf72-8f5db5c1b5ed

        @steps:

        1.  Create a variable with some default value that matches the regex of
        step 2
        2.  Validate this value with regex validator type and rule.

        @assert: Variable is created for matched validator rule.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_validate_matcher_value_with_regex(self):
        """Test matcher is not created for unmatched validator type regex.

        @id: 6542a847-7627-4bc2-828f-33b06d30d4e4

        @steps:

        1.  Create a matcher with value that doesn't match the regex of step 2.
        2.  Validate this value with regex validator type and rule.

        @assert: Matcher is not created for unmatched validator rule.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_validate_matcher_value_with_regex(self):
        """Test matcher is created for matched validator type regex.

        @id: 67e20b4b-cf39-4dbc-b553-80c5d54b7ad2

        @steps:

        1.  Create a matcher with value that matches the regex of step 2.
        2.  Validate this value with regex validator type and rule.

        @assert: Matcher is created for matched validator rule.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_validate_default_value_with_list(self):
        """Test variable is not created for unmatched validator type list.

        @id: dc2b6471-99d7-448b-b90a-9675baacbebe

        @steps:

        1.  Create variable with some default value that doesn't match the list
        of step 2.
        2.  Validate this value with list validator type and rule.

        @assert: Variable is not created for unmatched validator rule.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_validate_default_value_with_list(self):
        """Test variable is created for matched validator type list.

        @id: e3cbb3a6-5ac0-43b4-a566-6da758ae4cf6

        @steps:

        1.  Create a variable with some default value that matches the list of
        step 2.
        2.  Validate this value with list validator type and rule.

        @assert: Variable is created for matched validator rule.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_validate_matcher_value_with_list(self):
        """Test matcher is not created for unmatched validator type list.

        @id: b6523714-8d6f-4b23-8ecf-6972a584bfee

        @steps:

        1.  Create a matcher with value that doesn't match the list of step 2.
        2.  Validate this value with list validator type and rule.

        @assert: Matcher is not created for unmatched validator rule.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_validate_matcher_value_with_list(self):
        """Test matcher is created for matched validator type list.

        @id: 751e70ba-f1a4-4b73-878f-b2ab260a8a78

        @steps:

        1.  Create a matcher with value that matches the list of step 2.
        2.  Validate this value with list validator type and rule.

        @assert: Matcher is created for matched validator rule.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_validate_matcher_value_with_default_type(self):
        """Matcher is not created for value not of default type.

        @id: 84463d56-839f-4d5b-8646-cb6772fe5875

        @steps:

        1.  Create variable with valid default value.
        2.  Create matcher with value that doesn't match the default type.

        @assert: Matcher is not created for unmatched type.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_validate_matcher_value_with_default_type(self):
        """Matcher is created for default type value.

        @id: fc29aeb4-ead9-48ff-92de-3db659e8b0d1

        @steps:

        1.  Create variable default type with valid value.
        2.  Create a matcher with value that matches the default type.

        @assert: Matcher is created for matched type.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Test matcher creation for non-existing attribute.

        @id: bde1edf6-12b8-457e-ac8f-a909666abfb5

        @steps:

        1.  Attempt to create a matcher with non existing attribute.

        @assert: Matcher is not created for non-existing attribute.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher(self):
        """Create a Smart Variable with matcher.

        @id: 9ab8ae74-ee58-4738-8d8b-0e465eee8696

        @steps:

        1. Create a smart variable with valid name and default value.
        2. Create a matcher for Host with valid value.

        @assert:

        1. The smart Variable with matcher is created successfully.
        2. The variable is associated with host with match.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host.

        @id: 1a774df6-d704-4e89-b951-bc6740c233cd

        @steps:

        1.  Create variable with some default value.
        2.  Set fqdn as top priority attribute.
        3.  Create first matcher for fqdn with valid details.
        4.  Create second matcher for some attribute with valid details.
        Note - The fqdn/host should have this attribute.
        5.  Go to YAML output of associated host.

        @assert: The YAML output has the value only for fqdn matcher.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host - alternate priority.

        @id: e4e8da4d-f37c-44c8-8cbb-17171cc0648b

        @steps:

        1.  Create variable with some default value.
        2.  Set some attribute(other than fqdn) as top priority attribute.
        Note - The fqdn/host should have this attribute.
        3.  Create first matcher for fqdn with valid details.
        4.  Create second matcher for attribute of step 3 with valid details.
        5.  Go to YAML output of associated host.

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

        @id: 2f8e80ff-612f-461e-9498-90ebab2352c5

        @steps:

        1.  Create variable with some default value.
        2.  Create first matcher for attribute fqdn with valid details.
        3.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        4.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        5.  Set --merge-overrides to true.
        6.  Go to YAML output of associated host.

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
        """Test merge the values from non associated matchers.

        @id: 97831f91-c55a-4861-8730-4857c92f8829

        @steps:

        1.  Create variable with some default value.
        3.  Create first matcher for attribute fqdn with valid details.
        4.  Create second matcher for other attribute with valid details.
        Note - The fqdn/host should not have this attribute.
        5.  Create more matchers for some more attributes if any.
        Note - The fqdn/host should not have this attributes.
        6.  Set --merge-overrides to true.
        7.  Go to YAML output of associated host.

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

        @id: 3ff6bddd-c384-41bf-9209-d554b9859da0

        @steps:

        1. Create variable with some default value.
        2. Create first matcher for attribute fqdn with valid details.
        3. Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        4. Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        5. Set --merge-overrides to true.
        6. Set --merge-default to true.
        7. Go to YAML output of associated host.

        @assert:

        1. The YAML output has the values merged from all
        the associated matchers.
        2. The YAML output has the default value of variable.
        3. Duplicate values in YAML output if any are displayed.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_default(self):
        """Test empty default value in merged values.

        @id: 7a7211f2-be81-4d5b-9a9b-755ba064fc76

        @steps:

        1. Create variable with some default value.
        2. Create first matcher for attribute fqdn with valid details.
        3. Create second matcher for other attribute with valid details.
        Note - The fqdn/host should have this attribute.
        4. Create more matchers for some more attributes if any.
        Note - The fqdn/host should have this attributes.
        5. Set --merge-overrides to true.
        6. Set --merge-default to true.
        7. Go to YAML output of associated host.

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

        @id: d37bb265-796b-485f-8305-85c84f830fe5

        @steps:

        1.  Create variable with type array and value.
        2.  Create first matcher for attribute fqdn with some value.
        3.  Create second matcher for other attribute with
        same value as fqdn matcher.
        Note - The fqdn/host should have this attribute.
        4.  Set --merge-overrides to true.
        5.  Set --merge-default to true.
        6.  Set --avoid -duplicates' to true.
        7.  Go to YAML output of associated host.

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

        @id: 972cf68b-fd3d-4731-97bf-119e03c61b33

        @steps:

        1.  Create variable with type array and value.
        2.  Create first matcher for attribute fqdn with some value.
        3.  Create second matcher for other attribute with other value
        than fqdn matcher and default value.
        Note - The fqdn/host should have this attribute.
        4.  Set --merge-overrides to true.
        5.  Set --merge-default to true.
        6.  Set --avoid -duplicates' to true.
        7.  Go to YAML output of associated host.

        @assert:

        1.  The YAML output has the values merged from all matchers.
        2.  The YAML output has the default value of variable.
        3.  No value removed as duplicate value.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_enable_merge_overrides_default_flags(self):
        """Enable Merge Overrides, Merge Default flags for supported types.

        @id: c000f408-c293-4915-9432-6b597a2e6ad0

        @steps:

        1.  Set variable type to array/hash.

        @assert: The Merge Overrides, Merge Default flags are allowed to set
        true.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_merge_overrides_default_flags(self):
        """Disable Merge Overrides, Merge Default flags for non supported types.

        @id: 306400df-e823-48d6-b541-ef3b20181c78

        @steps:

        1.  Set variable type other than array/hash.

        @assert: The Merge Overrides, Merge Default flags are not allowed
        to set to true.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_enable_avoid_duplicates_flag(self):
        """Enable Avoid duplicates flag for supported type- array.

        @id: 0c7063e0-8e85-44b7-abae-4def7f68833a

        @steps:

        1. Set variable type to array.
        2. Set '--merge-overrides' to true.

        @assert: The '--avoid-duplicates' flag is allowed to set true.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_avoid_duplicates_flag(self):
        """Disable Avoid duplicates flag for non supported types.

        @id: ea1e8e31-4374-4172-82fd-538d29d70c03

        @steps:

        1.  Set variable type other than array.

        @assert:

        1.  The '--merge-overrides' is only allowed to set to true for type
        hash.
        2.  The '--avoid-duplicates' is not allowed to set to true for type
        other than array.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_impact_delete_attribute(self):
        """Impact on variable after deleting associated attribute.

        @id: ac6f3a65-ed39-4e97-bdee-349f08bd878e

        @steps:

        1.  Create a variable with matcher for some attribute.
        2.  Delete the attribute.
        3.  Recreate the attribute with same name as earlier.

        @assert:

        1.  The matcher for deleted attribute removed from variable.
        2.  On recreating attribute, the matcher should not reappear in
        variable.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_override_from_attribute(self):
        """Impact on variable on overriding the variable value from attribute.

        @id: 07622cab-26f9-4826-a61b-64748e4866a1

        @steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  From host/hostgroup, override the variable value.

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

        @id: 471fd4b3-c88a-4d3d-a142-343c75803c36

        @steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  From host/hostgroup, Attempt to override the variable with invalid
        key type of value.

        @assert:

        1.  No matcher for fqdn/hostgroup is created inside variable.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_empty_value_matcher_from_attribute(self):
        """Override variable value with empty value from attribute.

        @id: 49dab842-b310-4149-b187-bd7ccf5464a6

        @steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  From host/hostgroup, Attempt to override the variable with empty
        value.

        @assert:

        1.  Matcher for fqdn/hostgroup created for blank value.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_matcher_from_attribute(self):
        """Impact on variable on editing the variable value from attribute.

        @id: aa28f59f-0327-486b-8b16-64a2fe025e38

        @steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  Create a matcher for fqdn/hostgroup with valid details.
        4.  From host/hostgroup, edit the variable value.

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

        @id: 083dc374-9cc1-447c-98f0-54fa800d4ea7

        @steps:

        1.  Create a variable.
        2.  Associate variable with fqdn/hostgroup.
        3.  Create a matcher for fqdn/hostgroup with valid details.
        4.  From host/hostgroup, attempt to edit the variable
        with invalid value.

        @assert:

        1.  Matcher value in variable is not updated from fqdn/hostgroup for
        invalid value.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_default_value(self):
        """Test hiding of the default value of variable.

        @id: 00dd5627-5d7c-4fb2-9bbc-bf812205459e

        @steps:

        1. Create a variable.
        2. Enter some valid default value.
        3. Set '--hidden-value' to true.

        @assert: The default value is set to true.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_unhide_default_value(self):
        """Test unhiding of the default value of variable.

        @id: e1928ebf-32dd-4fb6-a40b-4c84507c1e2f

        @steps:

        1. Create a variable with some default value.
        2. Set '--hidden-value' to true.
        3. After hiding, set '--hidden-value' to false.

        @assert: The default value is set to false.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_hidden_value(self):
        """Update the hidden default value of variable.

        @id: 944d3fb9-ce90-47d8-bc54-fdf505bd5317

        @steps:

        1. Create a variable with some valid default value.
        2. Set '--hidden-value' to true.
        3. Again update the default value.

        @assert:

        1. The variable default value is updated.
        2. The variable '--hidden-value' is set true.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value.

        @id: dc4f7200-dd20-4b63-a27a-e6dc4d5607a5

        @steps:

        1.  Create a variable with empty value.
        2.  Set '--hidden-value' to true.

        @assert:

        1.  The '--hidden-value' is set to true.
        2.  The default value is empty.

        @caseautomation: notautomated

        @CaseLevel: System
        """
