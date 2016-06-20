# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Class Parameter

@Requirement: Classparameters

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from robottelo.decorators import run_only_on, stubbed, tier1, tier2, tier3
from robottelo.test import CLITestCase


class SmartClassParametersTestCase(CLITestCase):
    """Implements Smart Class Parameter tests in CLI"""

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_parameters_by_host_name(self):
        """List all the parameters included in specific Host by its name.

        @id: a8165746-3480-4875-8931-b20ebec241dc

        @assert: Parameters listed for specific Host.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_parameters_by_host_id(self):
        """List all the parameters included in specific Host by its id.

        @id: 79050de6-b894-4a88-b155-32bf488b692c

        @assert: Parameters listed for specific Host.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_parameters_by_hostgroup_name(self):
        """List all the parameters included in specific HostGroup by its name.

        @id: a2a01ca7-4dd2-4db6-a654-a632864998d9

        @assert: Parameters listed for specific HostGroup.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_parameters_by_hostgroup_id(self):
        """List all the parameters included in specific HostGroup by id.

        @id: 80c1058d-b87d-4c09-957f-7d3daacdedf4

        @assert: Parameters listed for specific HostGroup.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_parameters_by_puppetclass_name(self):
        """List all the parameters for specific puppet class by name.

        @id: 6d62968f-dc5b-4d7f-ac21-c1335a827960

        @assert: Parameters listed for specific Puppet class.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_parameters_by_puppetclass_id(self):
        """List all the parameters for specific puppet class by id.

        @id: a7a8af1a-514b-4910-9e19-75306f634041

        @assert: Parameters listed for specific Puppet class.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_override_check(self):
        """Override the Default Parameter value.

        @id: 25e34bac-084c-4b68-a082-822633e19f7e

        @steps:

        1.  Override the parameter.
        2.  Set the new valid Default Value.
        3.  Submit the changes.

        @assert: Parameter Value overridden with new value.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_override_uncheck(self):
        """Override the Default Parameter value - override Unchecked.

        @id: eb24c44d-0e34-40a3-aa3e-05a3cd4ed1ea

        @steps:

        1.  Don't override the parameter.
        2.  Set the new valid Default Value.
        3.  Attempt to submit the changes.

        @assert: Parameter value not allowed/disabled to override.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_puppet_default(self):
        """On Override, Set Puppet Default Value.

        @id: 360be750-ee96-414c-ac04-b2762f77503a

        @steps:

        1.  Override the parameter.
        2.  Set puppet default value to 'Use Puppet Default'.
        3.  Submit the changes.

        @assert: Puppet Default Value applied on parameter.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_parameter_type(self):
        """Positive Parameter Update for parameter types - Valid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        @id: 19567098-2087-4633-bdb6-1450a233285c

        @steps:

        1.  Override the parameter.
        2.  Update the Key Type.
        3.  Provide a 'valid' default Value.
        3.  Submit the changes.

        @assert: Parameter Updated with a new type successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_parameter_type(self):
        """Negative Parameter Update for parameter types - Invalid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        @id: 5c2c859a-8164-4733-8b41-d37f333656c7

        @steps:

        1.  Override the parameter.
        2.  Update the Key Type.
        3.  Enter an 'Invalid' default Value.
        3.  Submit the changes.

        @assert:

        1.  Parameter not updated with string type for invalid value.
        2.  Error raised for invalid default value.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_puppet_default_value(self):
        """Validation doesn't works on puppet default value.

        @id: ca69f1e8-d383-4563-a302-9758ffae1129

        @steps:

        1.  Override the parameter.
        2.  Set puppet default value to 'Use Puppet Default'.
        3.  Validate this value under section 'Optional Input Validator'.

        @assert: Validation shouldn't work with puppet default value.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_required_check(self):
        """Error raised for blank default Value - Required check.

        @id: 6ceeae8c-86ba-4ccc-a0b9-7da2d687aaee

        @steps:

        1.  Override the parameter.
        2.  Set empty default value.
        3.  Set '--required' check.
        4.  Submit the change.

        @assert: Error raised for blank default value.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_required_check(self):
        """No error raised for non-empty default Value - Required check.

        @id: 812aceb8-8d5e-4374-bf73-61d7085ee510

        @steps:

        1.  Override the parameter.
        2.  Provide some default value, Not empty.
        3.  Set '--required' check.
        4.  Submit the change.

        @assert: No error raised for non-empty default value

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_required_check(self):
        """Error raised for blank matcher Value - Required check.

        @id: 5f9a65d7-b4e4-42d1-8e29-220f41e7450f

        @steps:

        1.  Override the parameter.
        2.  Create a matcher for Parameter for some attribute.
        3.  Dont provide Value for matcher. Keep blank.
        4.  Set '--required' check.
        5.  Submit the change.

        @assert: Error raised for blank matcher value.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_required_check(self):
        """Error not raised for matcher Value - Required check.

        @id: e62c3c5a-d900-44d4-9793-2c17202974e5

        @steps:

        1.  Override the parameter.
        2.  Create a matcher for Parameter for some attribute.
        3.  Provide some Value for matcher.
        4.  Set '--required' check.
        5.  Submit the change.

        @assert: Error not raised for matcher value.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_with_regex(self):
        """Error raised for default value not matching with regex.

        @id: f36ed6e8-04ef-4614-98b3-38703d8aeeb0

        @steps:

        1.  Override the parameter.
        2.  Provide default value that doesn't matches the regex of step 3.
        3.  Validate this value with regex validator type and rule.
        4.  Submit the change.

        @assert: Error raised for default value not matching with regex.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_with_regex(self):
        """Error not raised for default value matching with regex.

        @id: 74666d12-e3be-46c1-8bd5-18d86dcf7f4b

        @steps:

        1.  Override the parameter.
        2.  Provide default value that matches the regex of step 3.
        3.  Validate this value with regex validator type and rule.
        4.  Submit the change.

        @assert: Error not raised for default value matching with regex.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_regex(self):
        """Error raised for matcher value not matching with regex.

        @id: b8b2f1c2-a20c-42d6-a687-79e6eee0268e

        @steps:

        1.  Override the parameter.
        2.  Create a matcher with value that doesn't match
        the regex of step 3.
        3.  Validate this value with regex validator type and rule.
        4.  Submit the change.

        @assert: Error raised for matcher value not matching with regex.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_regex(self):
        """Error not raised for matcher value matching with regex.

        @id: 2c8273aa-e621-4d4e-b03e-f8d50a596bc2

        @steps:

        1.  Override the parameter.
        2.  Create a matcher with value that matches the regex of step 3.
        3.  Validate this value with regex validator type and rule.
        4.  Submit the change.

        @assert: Error not raised for matcher value matching with regex.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_default_value_with_list(self):
        """Error raised for default value not in list.

        @id: cdcafbea-612e-4b60-90de-fa0c76442bbe

        @steps:

        1.  Override the parameter.
        2.  Provide default value that doesn't matches the list of step 3.
        3.  Validate this value with list validator type and rule.
        4.  Submit the change.

        @assert: Error raised for default value not in list.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_default_value_with_list(self):
        """Error not raised for default value in list.

        @id: b03708e8-e597-40fb-bb24-a1ac87475846

        @steps:

        1.  Override the parameter.
        2.  Provide default value that matches the list of step 3.
        3.  Validate this value with list validator type and rule.
        4.  Submit the change.

        @assert: Error not raised for default value in list.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_list(self):
        """Error raised for matcher value not in list.

        @id: 6e02c3f2-40aa-49ec-976d-7a12f5fa1e04

        @steps:

        1.  Override the parameter.
        2.  Create a matcher with value that doesn't match
        the list of step 3.
        3.  Validate this value with list validator type and rule.
        4.  Submit the change.

        @assert: Error raised for matcher value not in list.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_list(self):
        """Error not raised for matcher value in list.

        @id: 16927050-0bf2-4cbd-bb34-43c669f81304

        @steps:

        1.  Override the parameter.
        2.  Create a matcher with value that matches the list of step 3.
        3.  Validate this value with list validator type and rule.
        4.  Submit the change.

        @assert: Error not raised for matcher value in list.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_value_with_default_type(self):
        """Error raised for matcher value not of default type.

        @id: 307b0ea1-a035-4ce1-bcc5-f582147359e7

        @steps:

        1.  Override the parameter.
        2.  Update parameter default type with valid value.
        3.  Create a matcher with value that doesn't matches the default type.
        4.  Submit the change.

        @assert: Error raised for matcher value not of default type.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_matcher_value_with_default_type(self):
        """No error for matcher value of default type.

        @id: a247adac-4631-4b90-ae4a-a768cd05be34

        @steps:

        1.  Override the parameter.
        2.  Update parameter default type with valid value.
        3.  Create a matcher with value that matches the default type.
        4.  Submit the change.

        @assert: Error not raised for matcher value of default type.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_and_default_value(self):
        """Error for invalid default and matcher value both at a time.

        @id: 07dfcdad-e619-4672-9fe8-75a8352e44a4

        @steps:

        1.  Override the parameter.
        2.  Update parameter default type with Invalid value.
        3.  Create a matcher with value that doesn't matches the default type.
        4.  Attempt to submit the change.

        @assert: Error raised for invalid default and matcher value both.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Error while creating matcher for Non Existing Attribute.

        @id: 5223e582-81b4-442d-b4ba-b16ede460ef6

        @steps:

        1.  Override the parameter.
        2.  Create a matcher with non existing attribute in org.
        4.  Attempt to submit the change.

        @assert: Error raised for non existing attribute.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher(self):
        """Create matcher for attribute in parameter.

        @id: 37fe299b-1e81-4faf-b1c3-2edfc3d53dc1

        @steps:

        1.  Override the parameter.
        2.  Set some default Value.
        3.  Create a matcher with all valid values.
        4.  Submit the change.

        @assert: The matcher has been created successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_puppet_default_value(self):
        """Create matcher for attribute in parameter,
        Where Value is puppet default value.

        @id: c08fcf25-e5c7-411e-beed-3741a24496fd

        @steps:

        1.  Override the parameter.
        2.  Set some default Value.
        3.  Create matcher with valid attribute type, name and
        puppet default value.
        4.  Submit the change.

        @assert: The matcher has been created successfully.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host.

        @id: 77894977-0355-4309-8c96-09589ea7e814

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

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host - alternate priority.

        @id: 593a9327-9439-49f7-b952-70934c924535

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

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_override(self):
        """Merge the values of all the associated matchers.

        @id: f394a41f-f516-4759-bfff-89d6e5ccffd5

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

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_override(self):
        """Attempt to merge the values from non associated matchers.

        @id: fe936ad0-997f-468b-8113-f6a47d3e41eb

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

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_override_puppet_value(self):
        """Merge the values of all the associated matchers + puppet default value.

        @id: 64e0e9f4-7b75-410a-938e-67f8b32b7e1f

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

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_default(self):
        """Merge the values of all the associated matchers + default value.

        @id: df5a482a-09ec-4942-bc1f-1354eced6f66

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

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_default(self):
        """Empty default value is not shown in merged values.

        @id: d0ccb1fc-5620-4071-8bbc-7970def16cae

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

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_puppet_default(self):
        """Merge the values of all the associated matchers + puppet default value.

        @id: 3a69a439-987a-4901-b2cf-efc95945c634

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

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_matcher_avoid_duplicate(self):
        """Merge the values of all the associated matchers, remove duplicates.

        @id: 671c27c8-8270-41d6-8958-f76061a20c36

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

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_matcher_avoid_duplicate(self):
        """Duplicates not removed as they were not really present.

        @id: 98966558-475a-4f84-ba66-31eba38eb13f

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

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_matcher(self):
        """Removal of matcher from parameter.

        @id: f51ea9ca-f57c-482e-841f-3ea5cc8f8958

        @steps:

        1. Override the parameter and create a matcher
        for some attribute.
        2. Remove the matcher created in step 1.

        @assert: The matcher removed from parameter.

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_impact_parameter_delete_attribute(self):
        """Impact on parameter after deleting associated attribute.

        @id: 8d221485-ca88-49cb-a3d3-7ed5f1ce4653

        @steps:

        1.  Override the parameter and create a matcher
        for some attribute.
        2.  Delete the attribute.
        3.  Recreate the attribute with same name as earlier.

        @assert:

        1.  The matcher for deleted attribute removed from parameter.
        2.  On recreating attribute, the matcher should not
        reappear in parameter.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_parameter_default_value(self):
        """Hide the default value of parameter.

        @id: a1e206ae-67dc-48f0-886e-d543c682af34

        @steps:

        1. Set the override flag for the parameter.
        2. Set some valid default value.
        3. Set 'Hidden Value' to true.

        @assert: The 'hidden value' set to true for that parameter.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_unhide_parameter_default_value(self):
        """Unhide the default value of parameter.

        @id: 3daf662f-a0dd-469c-8088-262bfaa5246a

        @steps:

        1. Set the override flag for the parameter.
        2. Set some valid default value.
        3. Set 'Hidden Value' to true and submit.
        4. After hiding, set the 'Hidden Value' to false.

        @assert: The 'hidden value' set to false for that parameter.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_update_hidden_value_in_parameter(self):
        """Update the hidden default value of parameter.

        @id: 8602abc9-80bd-412d-bf46-68a1c7f832e4

        @steps:

        1. Set the override flag for the parameter.
        2. Set some valid default value.
        3. Set 'Hidden Value' to true and submit.
        4. Now in hidden state, update the default value.

        @assert:

        1. The parameter default value is updated.
        2. The 'hidden value' displayed as true for that parameter.

        @caseautomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value.

        @id: 31069fff-c6d5-42b6-94f2-9551057eb15b

        @steps:

        1. Set the override flag for the parameter.
        2. Don't set any default value/Set empty value.
        3. Set 'Hidden Value' to true and submit.

        @assert:

        1. The 'hidden value' set to true for that parameter.
        2. The default value is still empty on hide.

        @caseautomation: notautomated

        @CaseLevel: System
        """
