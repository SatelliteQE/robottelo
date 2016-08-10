# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Variables

@Requirement: Smart_Variables

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import run_only_on, stubbed, tier1, tier2, tier3
from robottelo.test import APITestCase


class SmartVariablesTestCase(APITestCase):
    """Implements Smart Variables tests in API"""

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create(self):
        """Create a Smart Variable with valid name

        @id: 4cd20cca-d419-43f5-9734-e9ae1caae4cb

        @steps: Create a smart Variable with Valid name and valid default value

        @assert: The smart Variable is created successfully

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create(self):
        """Create a Smart Variable with invalid name

        @id: d92f8bdd-93de-49ba-85a3-685aac9eda0a

        @steps: Create a smart Variable with invalid name and valid default
        value

        @assert: The smart Variable is not created

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_delete_smart_variable_by_id(self):
        """Delete a Smart Variable by id

        @id: 6d8354db-a028-4ae0-bcb6-87aa1cb9ec5d

        @steps: Delete a smart Variable by id

        @assert: The smart Variable is deleted successfully

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_delete_smart_variable_by_name(self):
        """Delete a Smart Variable by name

        @id: 5ee2e72f-4224-4505-bf2e-2a29a16d55c1

        @steps: Delete a smart Variable by name

        @assert: The smart Variable is deleted successfully

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_variables_by_host_id(self):
        """List all the variables associated to Host by host id

        @id: 4fc1f249-5da7-493b-a1d3-4ce7b625ad96

        @assert: All variables listed for Host

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_variables_by_hostgroup_id(self):
        """List all the variables associated to HostGroup by hostgroup id

        @id: db6861cc-b390-45bc-8c7d-cf10f46aecb3

        @assert: All variables listed for HostGroup

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_variables_by_puppetclass_id(self):
        """List all the variables associated to puppet class by puppet class id

        @id: cd743329-b354-4ddc-ada0-3ddd774e2701

        @assert: All variables listed for puppet class

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_variable_type(self):
        """Create variable for variable types - Valid Value

        Types - string, boolean, integer, real, array, hash, yaml, json

        @id: 4c8b4134-33c1-4f7f-83f9-a751c49ae2da

        @steps: Create a variable with all valid key types and default values

        @assert: Variable created with all given types successfully

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_variable_type(self):
        """Negative variable Update for variable types - Invalid Value

        Types - string, boolean, integer, real, array, hash, yaml, json

        @id: 9709d67c-682f-4e6c-8b8b-f02f6c2d3b71

        @steps: Create a variable with all valid key types and invalid default
        values

        @assert: Variable is not created for invalid value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_empty_value(self):
        """Create matcher with empty value with string type

        @id: a90b5bcd-f76c-4663-bf41-2f96e7e15c0f

        @steps:

        1. Create a matcher for variable with empty value and type string

        @assert: Matcher is created with empty value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_empty_value(self):
        """Create matcher with empty value with type other than string

        @id: a90b5bcd-f76c-4663-bf41-2f96e7e15c0f

        @steps:

        1. Create a matcher for variable with empty value and type any other
           than string

        @assert: Matcher is not created for empty value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_default_value_with_regex(self):
        """Create variable with non matching regex validator

        @id: 0c80bd58-26aa-4c2a-a087-ed3b88b226a7

        @steps:

        1. Create variable with default value that doesn't matches the regex
           of step 2
        2. Validate this value with regexp validator type and rule

        @assert: Variable is not created for non matching value with regex

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_default_value_with_regex(self):
        """Create variable with matching regex validator

        @id: aa9803b9-9a45-4ad8-b502-e0e32fc4b7d8

        @steps:

        1. Create variable with default value that matches the regex of
           step 2
        2. Validate this value with regex validator type and rule

        @assert: Variable is created for matching value with regex

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_value_with_regex(self):
        """Create matcher with non matching regexp validator

        @id: 8a0f9251-7992-4d1e-bace-7e32637bf56f

        @steps:

        1. Create a matcher with value that doesn't matches the regex of step 2
        2. Validate this value with regex validator type and rule

        @assert: Matcher is not created for non matching value with regexp

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_value_with_regex(self):
        """Create matcher with matching regex validator

        @id: 3ad09261-eb55-4758-b915-84006c9e527c

        @steps:

        1. Create a matcher with value that matches the regex of step 2
        2. Validate this value with regex validator type and rule

        @assert: Matcher is created for matching value with regex

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_default_value_with_list(self):
        """Create variable with non matching list validator

        @id: cacb83a5-3e50-490b-b94f-a5d27f44ae12

        @steps:

        1. Create variable with default value that doesn't matches the list
           validator of step 2
        2. Validate this value with list validator type and rule

        @assert: Variable is not created for non matching value with list
        validator

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_default_value_with_list(self):
        """Create variable with matching list validator

        @id: 6bc2caa0-1300-4751-8239-34b96517465b

        @steps:

        1. Create variable with default value that matches the list validator
           of step 2
        2. Validate this value with list validator type and rule

        @assert: Variable is created for matching value with list

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_value_with_list(self):
        """Create matcher with non matching list validator

        @id: 0aff0fdf-5a62-49dc-abe1-b727459d030a

        @steps:

        1. Create a matcher with value that doesn't matches the list validator
           of step 2
        2. Validate this value with list validator type and rule

        @assert: Matcher is not created for non matching value with list
        validator

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_value_with_list(self):
        """Create matcher with matching list validator

        @id: f5eda535-6623-4130-bea0-97faf350a6a6

        @steps:

        1. Create a matcher with value that matches the list validator
           of step 2
        2. Validate this value with list validator type and rule

        @assert: Matcher is created for matching value with list validator

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_value_with_default_type(self):
        """Create matcher with non matching type of default value

        @id: 790c63d7-4e8a-4187-8566-3d85d57f9a4f

        @steps:

        1. Create variable with valid type and value
        2. Create a matcher with value that doesn't matches the default type

        @assert: Matcher is not created for non matching the type of default
        value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_value_with_default_type(self):
        """Create matcher with matching type of default value

        @id: 99057f05-62cb-4230-b16c-d96ca6a5ae91

        @steps:


        1. Create variable with valid type and value
        2. Create a matcher with value that matches the default type

        @assert: Matcher is created for matching the type of default value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_non_existing_attribute(self):
        """Create matcher for non existing attribute

        @id: 23b16e7f-0626-467e-b53b-35e1634cc30d

        @steps: Create matcher for non existing attribute

        @assert: Matcher is not created for non existing attribute

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher(self):
        """Create matcher for attribute in variable

        @id: f0b3d51a-cf9a-4b43-9567-eb12cd973299

        @steps: Create a matcher with all valid values

        @assert: The matcher has been created successfully

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_variable_attribute_priority(self):
        """Variable value set on Attribute Priority for Host

        @id: 78474b5e-7a50-4de0-b22c-3413ac06d067

        @bz: 1362372

        @steps:

        1. Create variable with some valid value and type
        2. Set fqdn as top priority attribute
        3. Create first matcher for fqdn with valid details
        4. Create second matcher for some attribute with valid details
           Note - The FQDN/host should have this attribute
        5. Check ENC output of associated host.

        @assert: The ENC output shows variable value of fqdn matcher only

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_variable_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host - alternate priority

        @id: f6ef2193-5d63-43f1-8d91-e30984b2c0c5

        @bz: 1362372

        @steps:

        1. Create variable with valid value and type
        2. Set some attribute(other than fqdn) as top priority attribute
           Note - The fqdn/host should have this attribute
        3. Create first matcher for fqdn with valid details
        4. Create second matcher for attribute of step 3 with valid details
        5. Check ENC output of associated host.

        @assert: The ENC output shows variable value of step 4 matcher only

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_variable_merge_override(self):
        """Merge the values of all the associated matchers

        Note - This TC is only for array and hash key types

        @id: bb37995e-71f9-441c-b4d5-79e5b5ff3973

        @bz: 1362372

        @steps:

        1. Create variable with valid value and type
        2. Create first matcher for attribute fqdn with valid details
        3. Create second matcher for other attribute with valid details.
           Note - The fqdn/host should have this attribute
        4. Create more matchers for some more attributes if any
           Note - The fqdn/host should have this attributes
        5. Set 'merge overrides' to True
        6. Check ENC output of associated host

        @assert:

        1. The ENC output shows variable values merged from all the
           associated matchers
        2. The variable doesn't show the default value of variable.
        3. Duplicate values in any are displayed

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_variable_merge_override(self):
        """Merge the override values from non associated matchers

        Note - This TC is only for array and hash key types

        @id: afcb7ef4-38dd-484b-8a02-bc4e3d027204

        @bz: 1362372

        @steps:

        1. Create variable with valid value and type
        2. Create first matcher for attribute fqdn with valid details
        3. Create second matcher for other attribute with valid details
           Note - The fqdn/host should not have this attribute
        4. Create more matchers for some more attributes if any
           Note - The fqdn/host should not have this attributes
        5. Set 'merge overrides' to True
        6. Check ENC output of associated host

        @assert:

        1. The ENC output shows variable values only for fqdn
        2. The variable doesn't have the values for attribute
           which are not associated to host
        3. The variable doesn't have the default value of variable
        4. Duplicate values if any are displayed

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_variable_merge_default(self):
        """Merge the values of all the associated matchers + default value

        Note - This TC is only for array and hash key types

        @id: 9607c52c-f4c7-468b-a741-d179de144646

        @bz: 1362372

        @steps:

        1. Create variable with valid value and type
        2. Create first matcher for attribute fqdn with valid details
        3. Create second matcher for other attribute with valid details
           Note - The fqdn/host should have this attribute
        4. Create more matchers for some more attributes if any
           Note - The fqdn/host should have this attributes
        5. Set 'merge overrides' to True
        6. Set 'merge default' to True
        7. Check ENC output of associated host

        @assert:

        1. The ENC output shows the variable values merged from all the
           associated matchers
        2. The variable values has the default value of variable
        3. Duplicate values if any are displayed

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_variable_merge_default(self):
        """Empty default value is not shown in merged values

        Note - This TC is only for array and hash key types

        @id: 9033de15-f7e8-42be-b2be-c04c13aa039b

        @bz: 1362372

        @steps:

        1. Create variable with empty value and type
        2. Create first matcher for attribute fqdn with valid details
        3. Create second matcher for other attribute with valid details
           Note - The fqdn/host should have this attribute
        4. Create more matchers for some more attributes if any
           Note - The fqdn/host should have this attributes
        5. Set 'merge overrides' to True
        6. Set 'merge default' to True
        7. Check ENC output of associated host

        @assert:

        1. The ENC output shows variable values merged from all the associated
           matchers
        2. The variable doesn't have the empty default value of variable
        3. Duplicate values if any are displayed

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_variable_avoid_duplicate(self):
        """Merge the values of all the associated matchers, remove duplicates

        Note - This TC is only for array and hash key types

        @id: fcb2dfb9-64d6-4647-bbcc-3e5c900aca1b

        @bz: 1362372

        @steps:

        1. Create variable with valid value and type
        2. Create first matcher for attribute fqdn with some value
        3. Create second matcher for other attribute with same value as fqdn
           matcher.
           Note - The fqdn/host should have this attribute
        4. Set 'merge overrides' to True
        5. Set 'merge default' to True
        6. Set 'avoid duplicate' to True
        7. Check ENC output of associated host

        @assert:

        1. The ENC output shows the variable values merged from all the
           associated matchers
        2. The variable shows the default value of variable
        3. Duplicate values are removed / not displayed

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_variable_avoid_duplicate(self):
        """Duplicates are not removed as they were not really present

        Note - This TC is only for array and hash key types

        @id: 1f8a06de-0c53-424e-b2c9-b48a580d6298

        @bz: 1362372

        @steps:

        1. Create variable with valid value and type
        2. Create first matcher for attribute fqdn with some value
        3. Create second matcher for other attribute with other value than fqdn
           matcher and default value.
           Note - The fqdn/host should have this attribute
        4. Set 'merge overrides' to True
        5. Set 'merge default' to True
        6. Set 'avoid duplicates' to True
        7. Check ENC output of associated host

        @assert:

        1. The ENC output shows the variable values merged from all matchers
        2. The variable shows default value of variable
        3. No value removed as duplicate value

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_enable_merge_overrides_and_default_flags(self):
        """Enable Merge Overrides, Merge Default flags for supported types

        @id: af2c16e1-9a78-4615-9bc3-34fadca6a179

        @steps: Set variable type to array/hash

        @assert: The Merge Overrides, Merge Default flags are enabled to set

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_merge_overrides_default_flags(self):
        """Disable Merge Overrides, Merge Default flags for non supported types

        @id: f62a7e23-6fb4-469a-8589-4c987ff589ef

        @steps: Set variable type other than array/hash

        @assert: The Merge Overrides, Merge Default flags are not enabled to
        set

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_enable_avaoid_duplicates_flag(self):
        """Enable Avoid duplicates flag for supported type

        @id: 98fb1884-ad2b-45a0-b376-66bbc5ef6f72

        @steps:

        1. Set variable type to array
        2. Set 'merge overrides' to True

        @assert: The Avoid Duplicates is enabled to set to True

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_enable_avoid_duplicates_flag(self):
        """Disable Avoid duplicates flag for non supported types

        @id: c7a2f718-6346-4851-b5f1-ab36c2fa8c6a

        @steps: Set variable type other than array

        @assert:

        1. The Merge Overrides flag is only enabled to set for type hash
           other than array
        2. The Avoid duplicates flag not enabled to set for any type than
           array

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_remove_matcher(self):
        """Removal of matcher from variable

        @id: 7a932a99-2bd9-43ee-bcda-2b01a389787c

        @steps:

        1. Override the variable and create a matcher for some attribute
        2. Remove the matcher created in step 1

        @assert: The matcher removed from variable

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_impact_variable_delete_attribute(self):
        """Impact on variable after deleting associated attribute

        @id: d4faec04-be29-48e6-8585-10ff1c361a9e

        @steps:

        1. Create a variable and matcher for some attribute
        2. Delete the attribute
        3. Recreate the attribute with same name as earlier

        @assert:

        1. The matcher for deleted attribute removed from variable
        2. On recreating attribute, the matcher should not reappear in variable

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_hide_variable_default_value(self):
        """Hide the default value of variable

        @id: 04bed7fa8-a5be-4fc0-8e9b-d68da00f8de0

        @steps:

        1. Create variable with valid type and value
        2. Set 'Hidden Value' flag to true

        @assert: The 'hidden value' flag is set

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_unhide_variable_default_value(self):
        """Unhide the default value of variable

        @id: e8b3ec03-1abb-48d8-9409-17178bb887cb

        @steps:

        1. Create variable with valid type and value
        2. Set 'Hidden Value' flag to True
        3. After hiding, set the 'Hidden Value' flag to False

        @assert: The 'hidden value' flag set to false

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_hidden_value_in_variable(self):
        """Update the hidden default value of variable

        @id: 21b5586e-9434-45ea-ae85-12e24c549412

        @steps:

        1. Create variable with valid type and value
        2. Set 'Hidden Value' flag to true
        3. Now in hidden state, update the default value

        @assert:

        1. The variable default value is updated
        2. The 'hidden value' flag set to True

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value

        @id: 010253f4-5f33-42b8-a40b-796a373670a6

        @steps:

        1. Create variable with valid type and empty value
        2. Set 'Hidden Value' to true

        @assert:

        1. The 'hidden value' flag set to True
        2. The default value is empty after hide

        @caseautomation: notautomated

        @CaseLevel: System
        """
