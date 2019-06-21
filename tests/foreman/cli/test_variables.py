# -*- encoding: utf-8 -*-
"""Test class for Puppet Smart Variables

:Requirement: Variables

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

from nailgun import entities

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.environment import Environment
from robottelo.cli.factory import (
    make_hostgroup,
    make_location,
    make_org,
    make_smart_variable,
    publish_puppet_module)
from robottelo.cli.host import Host
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.puppet import Puppet
from robottelo.cli.smart_variable import SmartVariable
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.datafactory import (
    gen_string,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import (
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    upgrade
)
from robottelo.decorators.func_locker import lock_function
from robottelo.test import CLITestCase


class SmartVariablesTestCase(CLITestCase):
    """Implements Smart Variables tests in CLI"""

    @classmethod
    @lock_function
    def setUpClass(cls):
        """Import some parametrized puppet classes. This is required to make
        sure that we have data to be able to perform interactions with smart
        class variables.
        """
        super(SmartVariablesTestCase, cls).setUpClass()
        cls.puppet_modules = [
            {'author': 'robottelo', 'name': 'cli_test_variables'},
        ]
        cls.org = make_org()
        cls.loc = make_location()
        cv = publish_puppet_module(
            cls.puppet_modules, CUSTOM_PUPPET_REPO, cls.org['id'])
        cls.env = Environment.list({
            'search': u'content_view="{0}"'.format(cv['name'])
        })[0]
        Environment.update({
            'name': cls.env['name'],
            'organization-ids': cls.org['id'],
            'location-ids': cls.loc['id'],
        })
        # Find imported puppet class
        cls.puppet_class = Puppet.info({
            'name': cls.puppet_modules[0]['name'],
            'environment': cls.env['name'],
        })
        # And all its subclasses
        cls.puppet_subclasses = Puppet.list({
            'search': "name ~ {0}:: and environment = {1}".format(
                cls.puppet_class['name'], cls.env['name'])
        })

    # TearDown brakes parallel tests run as every test depends on the same
    # puppet class that will be removed during TearDown
    # Uncomment for developing or debugging and do not forget to import
    # `robottelo.api.utils.delete_puppet_class`.
    #
    # @classmethod
    # def tearDownClass(cls):
    #     """Removes puppet class."""
    #     super(SmartVariablesTestCase, cls).tearDownClass()
    #     delete_puppet_class(cls.puppet_class['name'])

    @tier2
    def test_positive_list(self):
        """List all smart variables associated to host, hostgroup, puppetlass

        :id: ee0da54c-ab60-4dde-8e1f-d548b52bac73

        :expectedresults: Smart Variables listed based on selected filter

        :CaseLevel: Integration
        """
        smart_variable = make_smart_variable(
            {'puppet-class': self.puppet_class['name']})

        # List by host name and id
        host = entities.Host(organization=self.org['id'],
                             location=self.loc['id']).create()
        Host.update({
            u'name': host.name,
            u'environment': self.env['name'],
            u'puppet-classes': self.puppet_class['name'],
        })
        host_variables = SmartVariable.list({'host': host.name})
        self.assertGreater(len(host_variables), 0)
        self.assertIn(
            smart_variable['variable'],
            [sv['variable'] for sv in host_variables]
        )
        host_variables = SmartVariable.list({'host-id': host.id})
        self.assertGreater(len(host_variables), 0)
        self.assertIn(
            smart_variable['id'], [sv['id'] for sv in host_variables])

        # List by hostgroup name and id
        hostgroup = make_hostgroup({
            'environment-id': self.env['id'],
            'puppet-class-ids': self.puppet_class['id']
        })
        hostgroup_variables = SmartVariable.list(
            {'hostgroup': hostgroup['name']})
        self.assertGreater(len(hostgroup_variables), 0)
        self.assertIn(
            smart_variable['variable'],
            [sv['variable'] for sv in hostgroup_variables]
        )
        hostgroup_variables = SmartVariable.list(
            {'hostgroup-id': hostgroup['id']})
        self.assertGreater(len(hostgroup_variables), 0)
        self.assertIn(
            smart_variable['id'], [sv['id'] for sv in hostgroup_variables])

        # List by puppetclass name and id
        sc_params_list = SmartVariable.list({
            'puppet-class': self.puppet_class['name']
        })
        self.assertGreater(len(sc_params_list), 0)
        self.assertIn(
            smart_variable['variable'],
            [sv['variable'] for sv in sc_params_list]
        )
        sc_params_list = SmartVariable.list({
            'puppet-class-id': self.puppet_class['id']
        })
        self.assertGreater(len(sc_params_list), 0)
        self.assertIn(
            smart_variable['id'], [sv['id'] for sv in sc_params_list])

    @tier1
    def test_positive_CRUD(self):
        """Create, Update, and Delete Smart Variable.

        :id: 8be9ed26-9a27-42a8-8edd-b255637f205e

        :steps: Create a smart Variable with Valid name.

        :expectedresults: The smart Variable is created successfully.

        :CaseImportance: Critical
        """
        name = valid_data_list()[0]
        smart_variable = make_smart_variable({
            'variable': name,
            'puppet-class': self.puppet_class['name']
        })
        self.assertEqual(smart_variable['variable'], name)

        # Update name and puppet class
        new_name = valid_data_list()[1]
        new_puppet = Puppet.info(
            {u'name': choice(self.puppet_subclasses)['name']})
        SmartVariable.update({
            'id': smart_variable['id'],
            'new-variable': new_name,
            'puppet-class': new_puppet['name']
        })
        updated_sv = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(updated_sv['puppet-class'], new_puppet['name'])
        self.assertEqual(updated_sv['variable'], new_name)

        # Delete
        SmartVariable.delete({'variable': smart_variable['variable']})
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.info({'variable': smart_variable['variable']})

    @tier1
    def test_negative_create(self):
        """Create Smart Variable with invalid name.

        :id: 3f71f39f-4178-42e7-be40-2a3538361466

        :steps: Create a smart Variable with Invalid name.

        :expectedresults: The smart Variable is not created.

        :CaseImportance: Critical
        """
        name = invalid_values_list()[0]
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.create({
                'variable': name,
                'puppet-class': self.puppet_class['name']
            })

    @tier1
    def test_negative_duplicate_name_variable(self):
        """Create Smart Variable with an existing name.

        :id: cc219111-1d2a-47ae-9b22-0b399f2d586d

        :steps:

            1. Create a smart Variable with Valid name and default value.
            2. Attempt to create a variable with same name from same/other
               class.

        :expectedresults: The variable with same name are not allowed to create
            from any class.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        make_smart_variable(
            {'variable': name, 'puppet-class': self.puppet_class['name']})
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.create({
                'variable': name, 'puppet-class': self.puppet_class['name']})

    @tier1
    def test_positive_create_with_default_value(self):
        """Create a Smart Variable with default value.

        :id: 31c9e92d-94d2-4cbf-b496-c5f038182c20

        :steps: Create a smart Variable with Valid name and valid default
            value.

        :expectedresults: The smart Variable is created successfully.

        :CaseImportance: Critical
        """
        value = valid_data_list()[0]
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': value,
        })
        self.assertEqual(smart_variable['default-value'], value)

    @tier1
    def test_positive_create_empty_matcher_value(self):
        """Create matcher with empty value for string type.

        :id: 00fe9a2b-a4c0-4f3e-9bc3-db22f8625005

        :steps: Create a matcher for variable with type string and empty value

        :expectedresults: Matcher is created with empty value

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': gen_string('alpha'),
            'override-value-order': 'is_virtual',
        })
        SmartVariable.add_override_value({
            'smart-variable-id': smart_variable['id'],
            'match': 'is_virtual=true',
            'value': '',
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'],
            'is_virtual=true'
        )
        self.assertEqual(
            smart_variable['override-values']['values']['1']['value'], '')

    @tier1
    def test_negative_create_empty_matcher_value(self):
        """Create matcher with empty value for non string type.

        :id: 677a0881-c42a-4063-ac7b-7e7d9b5bc307

        :steps: Create a matcher for variable with type other than string and
            empty value

        :expectedresults: Matcher is not created with empty value

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': '20',
            'variable-type': 'integer',
            'override-value-order': 'is_virtual',
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.add_override_value({
                'smart-variable-id': smart_variable['id'],
                'match': 'is_virtual=true',
                'value': '',
            })

    @tier1
    def test_negative_create_with_invalid_match_value(self):
        """Attempt to create matcher with invalid match value.

        :id: 1026bc74-1bd0-40ab-81f1-d1371cc49d8f

        :steps: Create a matcher for variable with invalid match value

        :expectedresults: Matcher is not created

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.add_override_value({
                'smart-variable-id': smart_variable['id'],
                'match': 'invalid_value',
                'value': gen_string('alpha'),
            })

    @tier1
    def test_negative_validate_default_value_with_regex(self):
        """Test variable is not created for unmatched validator type regex.

        :id: f728ea2c-f7f4-4d9b-8c92-9681e0b21769

        :steps:

            1.  Create a variable with value that doesn't match the regex of
                step 2
            2.  Validate this value with regex validator type and valid rule.

        :expectedresults: Variable is not created for unmatched validator rule.

        :CaseImportance: Critical
        """
        value = gen_string('alpha')
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': value
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.update({
                'id': smart_variable['id'],
                'default-value': gen_string('alpha'),
                'validator-type': 'regexp',
                'validator-rule': '[0-9]',
            })
        sc_param = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(sc_param['default-value'], value)

    @tier1
    def test_positive_validate_default_value_with_regex(self):
        """Test variable is created for matched validator type regex.

        :id: f720c888-0ed0-4d32-bf72-8f5db5c1b5ed

        :steps:

            1.  Create a variable with some default value that matches the
                regex of step 2
            2.  Validate this value with regex validator type and rule.

        :expectedresults: Variable is created for matched validator rule.

        :CaseImportance: Critical
        """
        value = gen_string('numeric').lstrip('0')
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': gen_string('alpha')
        })
        SmartVariable.update({
            'id': smart_variable['id'],
            'default-value': value,
            'validator-type': 'regexp',
            'validator-rule': '[0-9]',
        })
        updated_sv = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(updated_sv['default-value'], value)
        self.assertEqual(updated_sv['validator']['type'], 'regexp')
        self.assertEqual(updated_sv['validator']['rule'], '[0-9]')

    @tier1
    def test_negative_validate_matcher_value_with_regex(self):
        """Test matcher is not created for unmatched validator type regex.

        :id: 6542a847-7627-4bc2-828f-33b06d30d4e4

        :steps:

            1.  Create a matcher with value that doesn't match the regex of
                step 2.
            2.  Validate this value with regex validator type and rule.

        :expectedresults: Matcher is not created for unmatched validator rule.

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': gen_string('numeric'),
            'validator-type': 'regexp',
            'validator-rule': '[0-9]',
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.add_override_value({
                'smart-variable-id': smart_variable['id'],
                'match': 'domain=test.com',
                'value': gen_string('alpha')
            })

    @tier1
    def test_positive_validate_matcher_value_with_regex(self):
        """Test matcher is created for matched validator type regex.

        :id: 67e20b4b-cf39-4dbc-b553-80c5d54b7ad2

        :steps:

            1.  Create a matcher with value that matches the regex of step 2.
            2.  Validate this value with regex validator type and rule.

        :expectedresults: Matcher is created for matched validator rule.

        :CaseImportance: Critical
        """
        value = gen_string('numeric').lstrip('0')
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': gen_string('numeric'),
            'validator-type': 'regexp',
            'validator-rule': '[0-9]',
        })
        SmartVariable.add_override_value({
            'smart-variable-id': smart_variable['id'],
            'match': 'domain=test.com',
            'value': value
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(smart_variable['validator']['type'], 'regexp')
        self.assertEqual(smart_variable['validator']['rule'], '[0-9]')
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'],
            'domain=test.com'
        )
        self.assertEqual(
            smart_variable['override-values']['values']['1']['value'], value)

    @tier1
    def test_negative_validate_default_value_with_list(self):
        """Test variable is not created for unmatched validator type list.

        :id: dc2b6471-99d7-448b-b90a-9675baacbebe

        :steps: Attempt to create variable with default value that doesn't
            match values from validator list

        :expectedresults: Variable is not created for unmatched validator rule.

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.create({
                'puppet-class': self.puppet_class['name'],
                'default-value': gen_string('alphanumeric'),
                'validator-type': 'list',
                'validator-rule': '5, test',
            })

    @tier1
    def test_positive_validate_default_value_with_list(self):
        """Test variable is created for matched validator type list.

        :id: e3cbb3a6-5ac0-43b4-a566-6da758ae4cf6

        :steps: Create a variable with default value that matches the values
            from validator list

        :expectedresults: Variable is created for matched validator rule.

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': 'test',
            'validator-type': 'list',
            'validator-rule': '5, test',
        })
        self.assertEqual(smart_variable['default-value'], 'test')
        self.assertEqual(smart_variable['validator']['type'], 'list')
        self.assertEqual(smart_variable['validator']['rule'], '5, test')

    @tier1
    def test_negative_validate_matcher_value_with_list(self):
        """Test matcher is not created for unmatched validator type list.

        :id: b6523714-8d6f-4b23-8ecf-6972a584bfee

        :steps:

            1.  Create smart variable with proper validator
            2.  Attempt to associate a matcher with value that doesn't match
                values from validator list

        :expectedresults: Matcher is not created for unmatched validator rule.

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': '50',
            'validator-type': 'list',
            'validator-rule': '25, example, 50',
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.add_override_value({
                'smart-variable-id': smart_variable['id'],
                'match': 'domain=test.com',
                'value': 'myexample'
            })

    @tier1
    def test_positive_validate_matcher_value_with_list(self):
        """Test matcher is created for matched validator type list.

        :id: 751e70ba-f1a4-4b73-878f-b2ab260a8a78

        :steps:

            1.  Create smart variable with proper validator
            2.  Create a matcher with value that matches the values from
                validator list

        :expectedresults: Matcher is created for matched validator rule.

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': 'example',
            'validator-type': 'list',
            'validator-rule': 'test, example, 30',
        })
        SmartVariable.add_override_value({
            'smart-variable-id': smart_variable['id'],
            'match': 'domain=test.com',
            'value': '30'
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(smart_variable['validator']['type'], 'list')
        self.assertEqual(
            smart_variable['validator']['rule'], 'test, example, 30')
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'],
            'domain=test.com'
        )
        self.assertEqual(
            smart_variable['override-values']['values']['1']['value'], '30')

    @tier1
    def test_negative_validate_matcher_value_with_default_type(self):
        """Matcher is not created for value not of default type.

        :id: 84463d56-839f-4d5b-8646-cb6772fe5875

        :steps:

            1.  Create variable with valid default value.
            2.  Create matcher with value that doesn't match the default type.

        :expectedresults: Matcher is not created for unmatched type.

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': 'true',
            'variable-type': 'boolean',
            'override-value-order': 'is_virtual',
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.add_override_value({
                'smart-variable-id': smart_variable['id'],
                'match': 'is_virtual=true',
                'value': 50,
            })

    @tier1
    def test_positive_validate_matcher_value_with_default_type(self):
        """Matcher is created for default type value.

        :id: fc29aeb4-ead9-48ff-92de-3db659e8b0d1

        :steps:

            1.  Create variable default type with valid value.
            2.  Create a matcher with value that matches the default type.

        :expectedresults: Matcher is created for matched type.

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': 'true',
            'variable-type': 'boolean',
            'override-value-order': 'is_virtual',
        })
        SmartVariable.add_override_value({
            'smart-variable-id': smart_variable['id'],
            'match': 'is_virtual=true',
            'value': 'false',
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'],
            'is_virtual=true'
        )
        self.assertEqual(
            smart_variable['override-values']['values']['1']['value'], False)

    @tier1
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Attempt to create Smart Variable with a matcher that has value for
        non existing attribute.

        :id: bde1edf6-12b8-457e-ac8f-a909666abfb5

        :expectedresults: Matcher is not created and error is raised

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': 'true',
            'variable-type': 'boolean',
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.add_override_value({
                'smart-variable-id': smart_variable['id'],
                'match': 'hostgroup={0}'.format(gen_string('alpha')),
                'value': 'false',
            })

    @tier1
    def test_negative_create_matcher_with_invalid_attribute(self):
        """Attempt to create Smart Variable with a matcher that has value for
        invalid attribute that is not in order priority list.

        :id: 35c0edab-31f5-4795-ba75-010ec355744c

        :expectedresults: Matcher is not created and error is raised

        :BZ: 1379277

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': 'true',
            'variable-type': 'boolean',
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.add_override_value({
                'smart-variable-id': smart_variable['id'],
                'match': 'something_is_here=true',
                'value': 'false',
            })

    @tier1
    def test_positive_create_matcher(self):
        """Create a Smart Variable with matcher.

        :id: 9ab8ae74-ee58-4738-8d8b-0e465eee8696

        :steps:

            1. Create a smart variable with valid name and default value.
            2. Create a matcher for Host with valid value.

        :expectedresults:

            1. The smart Variable with matcher is created successfully.
            2. The variable is associated with host with match.

        :CaseImportance: Critical
        """
        value = gen_string('alpha')
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'override-value-order': 'is_virtual',
        })
        SmartVariable.add_override_value({
            'smart-variable-id': smart_variable['id'],
            'match': 'is_virtual=true',
            'value': value,
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'],
            'is_virtual=true'
        )
        self.assertEqual(
            smart_variable['override-values']['values']['1']['value'], value)

    @tier1
    @upgrade
    def test_positive_remove_matcher(self):
        """Create a Smart Variable with matcher and remove that matcher
        afterwards.

        :id: 883e0f3b-6367-4fbb-a0b2-434fbeb10fcf

        :steps:

            1. Create a smart variable with valid name and default value.
            2. Create a matcher for that variable.
            3. Remove just assigned matcher.

        :expectedresults:

            1. The smart Variable is created successfully.
            2. The matcher is associated with variable.
            3. Matcher removed successfully

        :CaseImportance: Critical
        """
        value = gen_string('alpha')
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'override-value-order': 'is_virtual',
        })
        SmartVariable.add_override_value({
            'smart-variable-id': smart_variable['id'],
            'match': 'is_virtual=true',
            'value': value,
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'],
            'is_virtual=true'
        )
        self.assertEqual(
            smart_variable['override-values']['values']['1']['value'], value)
        SmartVariable.remove_override_value({
            'id': smart_variable['override-values']['values']['1']['id'],
            'smart-variable-id': smart_variable['id'],
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(len(smart_variable['override-values']['values']), 0)

    @stubbed()
    @tier2
    def test_positive_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host.

        :id: 1a774df6-d704-4e89-b951-bc6740c233cd

        :steps:

            1.  Create variable with some default value.
            2.  Set fqdn as top priority attribute.
            3.  Create first matcher for fqdn with valid details.
            4.  Create second matcher for some attribute with valid details.
                Note - The fqdn/host should have this attribute.
            5.  Go to YAML output of associated host.

        :expectedresults: The YAML output has the value only for fqdn matcher.

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_negative_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host - alternate priority.

        :id: e4e8da4d-f37c-44c8-8cbb-17171cc0648b

        :steps:

            1.  Create variable with some default value.
            2.  Set some attribute(other than fqdn) as top priority attribute.
                Note - The fqdn/host should have this attribute.
            3.  Create first matcher for fqdn with valid details.
            4.  Create second matcher for attribute of step 3 with valid
                details.
            5.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the value only for step 5 matcher.
            2.  The YAML output doesn't have value for fqdn/host matcher.

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_create_matcher_merge_override(self):
        """Merge the values of all the associated matchers.

        :id: 2f8e80ff-612f-461e-9498-90ebab2352c5

        :steps:

            1.  Create variable with some default value.
            2.  Create first matcher for attribute fqdn with valid details.
            3.  Create second matcher for other attribute with valid details.
                Note - The fqdn/host should have this attribute.
            4.  Create more matchers for some more attributes if any.
                Note - The fqdn/host should have this attributes.
            5.  Set --merge-overrides to true.
            6.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output doesn't have the default value of variable.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': '[56]',
            'variable-type': 'array'
        })
        SmartVariable.add_override_value({
            'smart-variable-id': smart_variable['id'],
            'match': 'os=rhel6',
            'value': '[67, 66]',
        })
        SmartVariable.add_override_value({
            'smart-variable-id': smart_variable['id'],
            'match': 'os=rhel7',
            'value': '[23, 44, 66]',
        })
        SmartVariable.update({
            'variable': smart_variable['variable'],
            'merge-overrides': 1,
            'merge-default': 1,
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})

    @stubbed()
    @tier2
    def test_negative_create_matcher_merge_override(self):
        """Test merge the values from non associated matchers.

        :id: 97831f91-c55a-4861-8730-4857c92f8829

        :steps:

            1.  Create variable with some default value.
            2.  Create first matcher for attribute fqdn with valid details.
            3.  Create second matcher for other attribute with valid details.
                Note - The fqdn/host should not have this attribute.
            4.  Create more matchers for some more attributes if any.
                Note - The fqdn/host should not have this attributes.
            5.  Set --merge-overrides to true.
            6.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values only for fqdn.
            2.  The YAML output doesn't have the values for attribute which are
                not associated to host.
            3.  The YAML output doesn't have the default value of variable.
            4.  Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_create_matcher_merge_default(self):
        """Merge the values of all the associated matchers + default value.

        :id: 3ff6bddd-c384-41bf-9209-d554b9859da0

        :steps:

            1. Create variable with some default value.
            2. Create first matcher for attribute fqdn with valid details.
            3. Create second matcher for other attribute with valid details.
               Note - The fqdn/host should have this attribute.
            4. Create more matchers for some more attributes if any.
               Note - The fqdn/host should have this attributes.
            5. Set --merge-overrides to true.
            6. Set --merge-default to true.
            7. Go to YAML output of associated host.

        :expectedresults:

            1. The YAML output has the values merged from all the associated
               matchers.
            2. The YAML output has the default value of variable.
            3. Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_negative_create_matcher_merge_default(self):
        """Test empty default value in merged values.

        :id: 7a7211f2-be81-4d5b-9a9b-755ba064fc76

        :steps:

            1. Create variable with some default value.
            2. Create first matcher for attribute fqdn with valid details.
            3. Create second matcher for other attribute with valid details.
               Note - The fqdn/host should have this attribute.
            4. Create more matchers for some more attributes if any.
               Note - The fqdn/host should have this attributes.
            5. Set --merge-overrides to true.
            6. Set --merge-default to true.
            7. Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output doesn't have the empty default value of
                variable.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_create_matcher_avoid_duplicate(self):
        """Merge the values of all the associated matchers, remove duplicates.

        :id: d37bb265-796b-485f-8305-85c84f830fe5

        :steps:

            1.  Create variable with type array and value.
            2.  Create first matcher for attribute fqdn with some value.
            3.  Create second matcher for other attribute with same value as
                fqdn matcher.
                Note - The fqdn/host should have this attribute.
            4.  Set --merge-overrides to true.
            5.  Set --merge-default to true.
            6.  Set --avoid -duplicates' to true.
            7.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output has the default value of variable.
            3.  Duplicate values in YAML output are removed / not displayed.

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_negative_create_matcher_avoid_duplicate(self):
        """Duplicates not removed as they were not really present.

        :id: 972cf68b-fd3d-4731-97bf-119e03c61b33

        :steps:

            1.  Create variable with type array and value.
            2.  Create first matcher for attribute fqdn with some value.
            3.  Create second matcher for other attribute with other value than
                fqdn matcher and default value.
                Note - The fqdn/host should have this attribute.
            4.  Set --merge-overrides to true.
            5.  Set --merge-default to true.
            6.  Set --avoid -duplicates' to true.
            7.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all matchers.
            2.  The YAML output has the default value of variable.
            3.  No value removed as duplicate value.

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @tier1
    def test_positive_enable_merge_overrides_default_flags(self):
        """Enable Merge Overrides, Merge Default flags for supported types.

        :id: c000f408-c293-4915-9432-6b597a2e6ad0

        :steps:

            1.  Create smart variable with array/hash type.
            2.  Update smart variable and set corresponding flags to True
                state.

        :expectedresults: The Merge Overrides, Merge Default flags are allowed
            to set True.

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': '[56]',
            'variable-type': 'array'
        })
        SmartVariable.update({
            'variable': smart_variable['variable'],
            'merge-overrides': 1,
            'merge-default': 1,
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['merge-overrides'], True)
        self.assertEqual(
            smart_variable['override-values']['merge-default-value'], True)

    @tier1
    def test_negative_enable_merge_overrides_default_flags(self):
        """Attempt to enable Merge Overrides, Merge Default flags for non
        supported types.

        :id: 306400df-e823-48d6-b541-ef3b20181c78

        :steps:

            1.  Create smart variable with type that is not array/hash.
            2.  Attempt to update smart variable and set corresponding flags to
                True state.

        :expectedresults: The Merge Overrides, Merge Default flags are not
            allowed to set to True.

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': gen_string('numeric'),
            'variable-type': 'integer'
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.update({
                'variable': smart_variable['variable'],
                'merge-overrides': 1,
                'merge-default': 1,
            })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['merge-overrides'], False)
        self.assertEqual(
            smart_variable['override-values']['merge-default-value'], False)

    @tier1
    def test_positive_enable_avoid_duplicates_flag(self):
        """Enable Avoid duplicates flag for supported array type.

        :id: 0c7063e0-8e85-44b7-abae-4def7f68833a

        :steps:

            1. Create smart variable with array/hash type.
            2. Set '--merge-overrides' to true.

        :expectedresults: The '--avoid-duplicates' flag is allowed to set true.

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': '[test]',
            'variable-type': 'array'
        })
        SmartVariable.update({
            'variable': smart_variable['variable'],
            'merge-overrides': 1,
        })
        SmartVariable.update({
            'variable': smart_variable['variable'],
            'avoid-duplicates': 1,
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['avoid-duplicates'], True)

    @tier1
    def test_negative_enable_avoid_duplicates_flag(self):
        """Attempt to enable Avoid duplicates flag for non supported types.

        :id: ea1e8e31-4374-4172-82fd-538d29d70c03

        :steps:

            1.  Create smart variable with type that is not array/hash.
            2.  Attempt to update smart variable and set corresponding flags to
                True state.

        :expectedresults:

            1.  The '--merge-overrides' is only allowed to set to true for type
                hash.
            2.  The '--avoid-duplicates' is not allowed to set to true for type
                other than array.

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': gen_string('numeric'),
            'variable-type': 'integer'
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.update({
                'variable': smart_variable['variable'],
                'merge-overrides': 1,
                'avoid-duplicates': 1,
            })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['merge-overrides'], False)
        self.assertEqual(
            smart_variable['override-values']['avoid-duplicates'], False)

    @tier2
    @upgrade
    def test_positive_impact_delete_attribute(self):
        """Impact on variable after deleting associated attribute.

        :id: ac6f3a65-ed39-4e97-bdee-349f08bd878e

        :steps:

            1.  Create a variable with matcher for some attribute.
            2.  Delete the attribute.
            3.  Recreate the attribute with same name as earlier.

        :expectedresults:

            1.  The matcher for deleted attribute removed from variable.
            2.  On recreating attribute, the matcher should not reappear in
                variable.

        :CaseLevel: Integration
        """
        hostgroup_name = gen_string('alpha')
        matcher_value = gen_string('alpha')
        smart_variable = make_smart_variable(
            {'puppet-class': self.puppet_class['name']})
        hostgroup = make_hostgroup({
            'name': hostgroup_name,
            'environment-id': self.env['id'],
            'puppet-class-ids': self.puppet_class['id']
        })
        SmartVariable.add_override_value({
            'smart-variable-id': smart_variable['id'],
            'match': 'hostgroup={0}'.format(hostgroup_name),
            'value': matcher_value,
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'],
            'hostgroup={0}'.format(hostgroup_name)
        )
        self.assertEqual(
            smart_variable['override-values']['values']['1']['value'],
            matcher_value,
        )
        HostGroup.delete({'id': hostgroup['id']})
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(len(smart_variable['override-values']['values']), 0)
        make_hostgroup({
            'name': hostgroup_name,
            'environment-id': self.env['id'],
            'puppet-class-ids': self.puppet_class['id']
        })
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(len(smart_variable['override-values']['values']), 0)

    @skip_if_bug_open('bugzilla', 1371794)
    @tier1
    def test_positive_hide_default_value(self):
        """Test hiding of the default value of variable.

        :id: 00dd5627-5d7c-4fb2-9bbc-bf812205459e

        :steps:

            1. Create a variable.
            2. Enter some valid default value.
            3. Set '--hidden-value' to true.

        :expectedresults: The 'hidden value' set to true for that variable.
            Default value is hidden

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': gen_string('alpha'),
            'hidden-value': 1,
        })
        self.assertEqual(smart_variable['hidden-value?'], True)
        self.assertEqual(smart_variable['default-value'], '*****')

    @tier1
    def test_positive_unhide_default_value(self):
        """Test unhiding of the default value of variable.

        :id: e1928ebf-32dd-4fb6-a40b-4c84507c1e2f

        :steps:

            1. Create a variable with some default value.
            2. Set '--hidden-value' to true.
            3. After hiding, set '--hidden-value' to false.

        :expectedresults: The hidden value is set to false.

        :CaseImportance: Critical
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': gen_string('alpha'),
            'hidden-value': 1,
        })
        self.assertEqual(smart_variable['hidden-value?'], True)
        SmartVariable.update({
            'variable': smart_variable['variable'],
            'hidden-value': 0
        })
        updated_sv = SmartVariable.info(
            {'variable': smart_variable['variable']})
        self.assertEqual(updated_sv['hidden-value?'], False)

    @tier1
    @upgrade
    def test_positive_update_hidden_value(self):
        """Update the hidden default value of variable.

        :id: 944d3fb9-ce90-47d8-bc54-fdf505bd5317

        :steps:

            1. Create a variable with some valid default value.
            2. Set '--hidden-value' to true.
            3. Again update the default value.

        :expectedresults:

            1. The variable default value is updated.
            2. The variable '--hidden-value' is set true.

        :CaseImportance: Critical
        """
        value = gen_string('alpha')
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': gen_string('alpha'),
            'hidden-value': 1,
        })
        self.assertEqual(smart_variable['hidden-value?'], True)
        SmartVariable.update({
            'variable': smart_variable['variable'],
            'default-value': value,
        })
        updated_sv = SmartVariable.info({
            'variable': smart_variable['variable'],
            'show-hidden': 'true',
        })
        self.assertEqual(updated_sv['default-value'], value)

    @tier1
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value.

        :id: dc4f7200-dd20-4b63-a27a-e6dc4d5607a5

        :steps:

            1.  Create a variable with empty value.
            2.  Set '--hidden-value' to true.

        :expectedresults:

            1.  The '--hidden-value' is set to true.
            2.  The default value is empty.

        :CaseImportance: Critical

        :CaseAutomation: automated
        """
        smart_variable = make_smart_variable({
            'puppet-class': self.puppet_class['name'],
            'default-value': '',
            'hidden-value': 1,
        })
        smart_variable = SmartVariable.info({
            'variable': smart_variable['variable'],
            'show-hidden': 'true',
        })
        self.assertEqual(smart_variable['hidden-value?'], True)
        self.assertEqual(smart_variable['default-value'], '')
