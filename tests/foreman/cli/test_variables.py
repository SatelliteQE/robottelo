# -*- encoding: utf-8 -*-
"""Test class for Puppet Smart Variables

:Requirement: Variables

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:TestType: Functional

:CaseImportance: Medium

:Upstream: No
"""
from random import choice

from nailgun import entities

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.environment import Environment
from robottelo.cli.factory import make_hostgroup
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_smart_variable
from robottelo.cli.factory import publish_puppet_module
from robottelo.cli.host import Host
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.puppet import Puppet
from robottelo.cli.smart_variable import SmartVariable
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.datafactory import gen_string
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
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
        cls.puppet_modules = [{'author': 'robottelo', 'name': 'cli_test_variables'}]
        cls.org = make_org()
        cls.loc = make_location()
        cv = publish_puppet_module(cls.puppet_modules, CUSTOM_PUPPET_REPO, cls.org['id'])
        cls.env = Environment.list({'search': u'content_view="{0}"'.format(cv['name'])})[0]
        Environment.update(
            {
                'name': cls.env['name'],
                'organization-ids': cls.org['id'],
                'location-ids': cls.loc['id'],
            }
        )
        # Find imported puppet class
        cls.puppet_class = Puppet.info(
            {'name': cls.puppet_modules[0]['name'], 'environment': cls.env['name']}
        )
        # And all its subclasses
        cls.puppet_subclasses = Puppet.list(
            {
                'search': "name ~ {0}:: and environment = {1}".format(
                    cls.puppet_class['name'], cls.env['name']
                )
            }
        )

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
        smart_variable = make_smart_variable({'puppet-class': self.puppet_class['name']})

        # List by host name and id
        host = entities.Host(organization=self.org['id'], location=self.loc['id']).create()
        Host.update(
            {
                'name': host.name,
                'environment-id': self.env['id'],
                'puppet-classes': self.puppet_class['name'],
                'organization-id': self.org['id'],
            }
        )
        host_variables = SmartVariable.list({'host': host.name})
        self.assertGreater(len(host_variables), 0)
        self.assertIn(smart_variable['variable'], [sv['variable'] for sv in host_variables])
        host_variables = SmartVariable.list({'host-id': host.id})
        self.assertGreater(len(host_variables), 0)
        self.assertIn(smart_variable['id'], [sv['id'] for sv in host_variables])

        # List by hostgroup name and id
        hostgroup = make_hostgroup(
            {'environment-id': self.env['id'], 'puppet-class-ids': self.puppet_class['id']}
        )
        hostgroup_variables = SmartVariable.list({'hostgroup': hostgroup['name']})
        self.assertGreater(len(hostgroup_variables), 0)
        self.assertIn(smart_variable['variable'], [sv['variable'] for sv in hostgroup_variables])
        hostgroup_variables = SmartVariable.list({'hostgroup-id': hostgroup['id']})
        self.assertGreater(len(hostgroup_variables), 0)
        self.assertIn(smart_variable['id'], [sv['id'] for sv in hostgroup_variables])

        # List by puppetclass name and id
        sc_params_list = SmartVariable.list({'puppet-class': self.puppet_class['name']})
        self.assertGreater(len(sc_params_list), 0)
        self.assertIn(smart_variable['variable'], [sv['variable'] for sv in sc_params_list])
        sc_params_list = SmartVariable.list({'puppet-class-id': self.puppet_class['id']})
        self.assertGreater(len(sc_params_list), 0)
        self.assertIn(smart_variable['id'], [sv['id'] for sv in sc_params_list])

    @tier1
    def test_positive_CRUD(self):
        """Create, Update, and Delete Smart Variable.

        :id: 8be9ed26-9a27-42a8-8edd-b255637f205e

        :steps: Create a smart Variable with Valid name.

        :expectedresults: The smart Variable is created successfully.

        :CaseImportance: Critical
        """
        name = valid_data_list()[0]
        smart_variable = make_smart_variable(
            {'variable': name, 'puppet-class': self.puppet_class['name']}
        )
        self.assertEqual(smart_variable['variable'], name)

        # Update name and puppet class
        new_name = valid_data_list()[0]
        new_puppet = Puppet.info({u'name': choice(self.puppet_subclasses)['name']})
        SmartVariable.update(
            {
                'id': smart_variable['id'],
                'new-variable': new_name,
                'puppet-class': new_puppet['name'],
            }
        )
        updated_sv = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(updated_sv['puppet-class'], new_puppet['name'])
        self.assertEqual(updated_sv['variable'], new_name)

        # Delete
        SmartVariable.delete({'variable': updated_sv['variable']})
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.info({'variable': updated_sv['variable']})

    @tier2
    def test_negative_create(self):
        """Create Smart Variable with invalid name.

        :id: 3f71f39f-4178-42e7-be40-2a3538361466

        :steps: Create a smart Variable with Invalid name.

        :expectedresults: The smart Variable is not created.

        """
        name = invalid_values_list()[0]
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.create({'variable': name, 'puppet-class': self.puppet_class['name']})

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
        make_smart_variable({'variable': name, 'puppet-class': self.puppet_class['name']})
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.create({'variable': name, 'puppet-class': self.puppet_class['name']})

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
        smart_variable = make_smart_variable(
            {'puppet-class': self.puppet_class['name'], 'default-value': value}
        )
        self.assertEqual(smart_variable['default-value'], value)

    @tier2
    def test_negative_create_empty_matcher_value(self):
        """Create matcher with empty value for non string type.

        :id: 677a0881-c42a-4063-ac7b-7e7d9b5bc307

        :steps: Create a matcher for variable with type other than string and
            empty value

        :expectedresults: Matcher is not created with empty value

        """
        smart_variable = make_smart_variable(
            {
                'puppet-class': self.puppet_class['name'],
                'default-value': '20',
                'variable-type': 'integer',
                'override-value-order': 'is_virtual',
            }
        )
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.add_override_value(
                {
                    'smart-variable-id': smart_variable['id'],
                    'match': 'is_virtual=true',
                    'value': '',
                }
            )

    @tier2
    def test_negative_create_with_invalid_match_value(self):
        """Attempt to create matcher with invalid match value.

        :id: 1026bc74-1bd0-40ab-81f1-d1371cc49d8f

        :steps: Create a matcher for variable with invalid match value

        :expectedresults: Matcher is not created

        """
        smart_variable = make_smart_variable({'puppet-class': self.puppet_class['name']})
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.add_override_value(
                {
                    'smart-variable-id': smart_variable['id'],
                    'match': 'invalid_value',
                    'value': gen_string('alpha'),
                }
            )

    @tier2
    def test_positive_validate_default_value_with_regex(self):
        """Test variable is created for matched validator type regex.

        :id: f720c888-0ed0-4d32-bf72-8f5db5c1b5ed

        :steps:

            1.  Create a variable with some default value that matches the
                regex of step 2
            2.  Validate this value with regex validator type and rule.

        :expectedresults: Variable is created for matched validator rule.

        :CaseImportance: High
        """
        value = gen_string('numeric').lstrip('0')
        smart_variable = make_smart_variable(
            {'puppet-class': self.puppet_class['name'], 'default-value': gen_string('alpha')}
        )
        SmartVariable.update(
            {
                'id': smart_variable['id'],
                'default-value': value,
                'validator-type': 'regexp',
                'validator-rule': '[0-9]',
            }
        )
        updated_sv = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(updated_sv['default-value'], value)
        self.assertEqual(updated_sv['validator']['type'], 'regexp')
        self.assertEqual(updated_sv['validator']['rule'], '[0-9]')

    @tier2
    def test_positive_validate_matcher_value_with_regex(self):
        """Test matcher is created for matched validator type regex.

        :id: 67e20b4b-cf39-4dbc-b553-80c5d54b7ad2

        :steps:

            1.  Create a matcher with value that matches the regex of step 2.
            2.  Validate this value with regex validator type and rule.

        :expectedresults: Matcher is created for matched validator rule.

        :CaseImportance: High
        """
        value = gen_string('numeric').lstrip('0')
        smart_variable = make_smart_variable(
            {
                'puppet-class': self.puppet_class['name'],
                'default-value': gen_string('numeric'),
                'validator-type': 'regexp',
                'validator-rule': '[0-9]',
            }
        )
        SmartVariable.add_override_value(
            {'smart-variable-id': smart_variable['id'], 'match': 'domain=test.com', 'value': value}
        )
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(smart_variable['validator']['type'], 'regexp')
        self.assertEqual(smart_variable['validator']['rule'], '[0-9]')
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'], 'domain=test.com'
        )
        self.assertEqual(smart_variable['override-values']['values']['1']['value'], value)

    @tier2
    def test_negative_validate_default_value_with_list(self):
        """Test variable is not created for unmatched validator type list.

        :id: dc2b6471-99d7-448b-b90a-9675baacbebe

        :steps: Attempt to create variable with default value that doesn't
            match values from validator list

        :expectedresults: Variable is not created for unmatched validator rule.

        :CaseImportance: High
        """
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.create(
                {
                    'puppet-class': self.puppet_class['name'],
                    'default-value': gen_string('alphanumeric'),
                    'validator-type': 'list',
                    'validator-rule': '5, test',
                }
            )

    @tier2
    def test_positive_validate_matcher_value_with_list(self):
        """Test matcher is created for matched validator type list.

        :id: 751e70ba-f1a4-4b73-878f-b2ab260a8a78

        :steps:

            1.  Create smart variable with proper validator
            2.  Create a matcher with value that matches the values from
                validator list

        :expectedresults: Matcher is created for matched validator rule.

        :CaseImportance: High
        """
        smart_variable = make_smart_variable(
            {
                'puppet-class': self.puppet_class['name'],
                'default-value': 'example',
                'validator-type': 'list',
                'validator-rule': 'test, example, 30',
            }
        )
        SmartVariable.add_override_value(
            {'smart-variable-id': smart_variable['id'], 'match': 'domain=test.com', 'value': '30'}
        )
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(smart_variable['validator']['type'], 'list')
        self.assertEqual(smart_variable['validator']['rule'], 'test, example, 30')
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'], 'domain=test.com'
        )
        self.assertEqual(smart_variable['override-values']['values']['1']['value'], '30')

    @tier2
    def test_positive_validate_matcher_value_with_default_type(self):
        """Matcher is created for default type value.

        :id: fc29aeb4-ead9-48ff-92de-3db659e8b0d1

        :steps:

            1.  Create variable default type with valid value.
            2.  Create a matcher with value that matches the default type.

        :expectedresults: Matcher is created for matched type.

        :CaseImportance: High
        """
        smart_variable = make_smart_variable(
            {
                'puppet-class': self.puppet_class['name'],
                'default-value': 'true',
                'variable-type': 'boolean',
                'override-value-order': 'is_virtual',
            }
        )
        SmartVariable.add_override_value(
            {
                'smart-variable-id': smart_variable['id'],
                'match': 'is_virtual=true',
                'value': 'false',
            }
        )
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'], 'is_virtual=true'
        )
        self.assertEqual(smart_variable['override-values']['values']['1']['value'], False)

    @tier2
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Attempt to create Smart Variable with a matcher that has value for
        non existing attribute.

        :id: bde1edf6-12b8-457e-ac8f-a909666abfb5

        :expectedresults: Matcher is not created and error is raised

        :CaseImportance: High
        """
        smart_variable = make_smart_variable(
            {
                'puppet-class': self.puppet_class['name'],
                'default-value': 'true',
                'variable-type': 'boolean',
            }
        )
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.add_override_value(
                {
                    'smart-variable-id': smart_variable['id'],
                    'match': 'hostgroup={0}'.format(gen_string('alpha')),
                    'value': 'false',
                }
            )

    @tier2
    def test_negative_create_matcher_with_invalid_attribute(self):
        """Attempt to create Smart Variable with a matcher that has value for
        invalid attribute that is not in order priority list.

        :id: 35c0edab-31f5-4795-ba75-010ec355744c

        :expectedresults: Matcher is not created and error is raised

        :BZ: 1379277

        :CaseImportance: High
        """
        smart_variable = make_smart_variable(
            {
                'puppet-class': self.puppet_class['name'],
                'default-value': 'true',
                'variable-type': 'boolean',
            }
        )
        with self.assertRaises(CLIReturnCodeError):
            SmartVariable.add_override_value(
                {
                    'smart-variable-id': smart_variable['id'],
                    'match': 'something_is_here=true',
                    'value': 'false',
                }
            )

    @tier1
    @upgrade
    def test_positive_add_and_remove_matcher(self):
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
        smart_variable = make_smart_variable(
            {'puppet-class': self.puppet_class['name'], 'override-value-order': 'is_virtual'}
        )
        SmartVariable.add_override_value(
            {'smart-variable-id': smart_variable['id'], 'match': 'is_virtual=true', 'value': value}
        )
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'], 'is_virtual=true'
        )
        self.assertEqual(smart_variable['override-values']['values']['1']['value'], value)
        SmartVariable.remove_override_value(
            {
                'id': smart_variable['override-values']['values']['1']['id'],
                'smart-variable-id': smart_variable['id'],
            }
        )
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(len(smart_variable['override-values']['values']), 0)

    @tier2
    def test_positive_enable_merge_overrides_default_flags(self):
        """Enable Merge Overrides, Merge Default flags for supported types.

        :id: c000f408-c293-4915-9432-6b597a2e6ad0

        :steps:

            1.  Create smart variable with array/hash type.
            2.  Update smart variable and set corresponding flags to True
                state.

        :expectedresults: The Merge Overrides, Merge Default flags are allowed
            to set True.

        """
        smart_variable = make_smart_variable(
            {
                'puppet-class': self.puppet_class['name'],
                'default-value': '[56]',
                'variable-type': 'array',
            }
        )
        SmartVariable.update(
            {'variable': smart_variable['variable'], 'merge-overrides': 1, 'merge-default': 1}
        )
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(smart_variable['override-values']['merge-overrides'], True)
        self.assertEqual(smart_variable['override-values']['merge-default-value'], True)

    @tier2
    def test_positive_enable_avoid_duplicates_flag(self):
        """Enable Avoid duplicates flag for supported array type.

        :id: 0c7063e0-8e85-44b7-abae-4def7f68833a

        :steps:

            1. Create smart variable with array/hash type.
            2. Set '--merge-overrides' to true.

        :expectedresults: The '--avoid-duplicates' flag is allowed to set true.

        """
        smart_variable = make_smart_variable(
            {
                'puppet-class': self.puppet_class['name'],
                'default-value': '[test]',
                'variable-type': 'array',
            }
        )
        SmartVariable.update({'variable': smart_variable['variable'], 'merge-overrides': 1})
        SmartVariable.update({'variable': smart_variable['variable'], 'avoid-duplicates': 1})
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(smart_variable['override-values']['avoid-duplicates'], True)

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
        smart_variable = make_smart_variable({'puppet-class': self.puppet_class['name']})
        hostgroup = make_hostgroup(
            {
                'name': hostgroup_name,
                'environment-id': self.env['id'],
                'puppet-class-ids': self.puppet_class['id'],
            }
        )
        SmartVariable.add_override_value(
            {
                'smart-variable-id': smart_variable['id'],
                'match': 'hostgroup={0}'.format(hostgroup_name),
                'value': matcher_value,
            }
        )
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(
            smart_variable['override-values']['values']['1']['match'],
            'hostgroup={0}'.format(hostgroup_name),
        )
        self.assertEqual(smart_variable['override-values']['values']['1']['value'], matcher_value)
        HostGroup.delete({'id': hostgroup['id']})
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(len(smart_variable['override-values']['values']), 0)
        make_hostgroup(
            {
                'name': hostgroup_name,
                'environment-id': self.env['id'],
                'puppet-class-ids': self.puppet_class['id'],
            }
        )
        smart_variable = SmartVariable.info({'id': smart_variable['id']})
        self.assertEqual(len(smart_variable['override-values']['values']), 0)

    @tier2
    def test_positive_hide_update_and_unhide_default_value(self):
        """Test hiding of the default value of variable.

        :id: 00dd5627-5d7c-4fb2-9bbc-bf812205459e

        :steps:

            1. Create a variable.
            2. Enter some valid default value.
            3. Set '--hidden-value' to true.
            4. After hiding, set '--hidden-value' to false.

        :BZ: 1371794

        :expectedresults: The 'hidden value' set to true for that variable.
            Default value is hidden

        """
        smart_variable = make_smart_variable(
            {
                'puppet-class': self.puppet_class['name'],
                'default-value': gen_string('alpha'),
                'hidden-value': 1,
            }
        )
        self.assertEqual(smart_variable['hidden-value?'], True)
        self.assertEqual(smart_variable['default-value'], '*****')

        # Update hidden value to empty
        SmartVariable.update({'variable': smart_variable['variable'], 'default-value': ''})
        updated_sv = SmartVariable.info(
            {'variable': smart_variable['variable'], 'show-hidden': 'true'}
        )
        self.assertEqual(updated_sv['default-value'], '')

        # Unhide value
        SmartVariable.update({'variable': smart_variable['variable'], 'hidden-value': 0})
        updated_sv = SmartVariable.info({'variable': smart_variable['variable']})
        self.assertEqual(updated_sv['hidden-value?'], False)
