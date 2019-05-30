# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Class Parameter

:Requirement: Classparameters

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from nailgun import entities

from robottelo.api.utils import delete_puppet_class
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.environment import Environment
from robottelo.cli.factory import (
    add_role_permissions,
    make_hostgroup,
    make_location,
    make_org,
    make_role,
    make_user,
    publish_puppet_module,
)
from robottelo.cli.puppet import Puppet
from robottelo.cli.scparams import SmartClassParameter
from robottelo.cli.user import User
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    run_in_one_thread,
    stubbed,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import CLITestCase


@run_in_one_thread
class SmartClassParametersTestCase(CLITestCase):
    """Implements Smart Class Parameter tests in CLI"""

    @classmethod
    def setUpClass(cls):
        """Import some parametrized puppet classes. This is required to make
        sure that we have smart class variable available.
        Read all available smart class parameters for imported puppet class to
        be able to work with unique entity for each specific test.
        """
        super(SmartClassParametersTestCase, cls).setUpClass()
        cls.puppet_modules = [
            {'author': 'robottelo', 'name': 'cli_test_classparameters'},
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
        cls.puppet_class = Puppet.info({
            'name': cls.puppet_modules[0]['name'],
            'environment': cls.env['name'],
        })
        cls.sc_params_list = SmartClassParameter.list({
            'environment': cls.env['name'],
            'search': u'puppetclass="{0}"'.format(cls.puppet_class['name'])
        })
        cls.sc_params_ids_list = [
            sc_param['id'] for sc_param in cls.sc_params_list]
        cls.host = entities.Host(organization=cls.org['id'],
                                 location=cls.loc['id'],
                                 environment=cls.env['name'],).create()
        cls.host.add_puppetclass(
            data={'puppetclass_id': cls.puppet_class['id']})
        cls.hostgroup = make_hostgroup({
            'environment-id': cls.env['id'],
            'puppet-class-ids': cls.puppet_class['id']
        })

    @classmethod
    def tearDownClass(cls):
        """Removes puppet class."""
        super(SmartClassParametersTestCase, cls).tearDownClass()
        delete_puppet_class(cls.puppet_class['name'])

    def setUp(self):
        """Checks that there is at least one not overridden
        smart class parameter before executing test.
        """
        super(SmartClassParametersTestCase, self).setUp()
        if len(self.sc_params_list) == 0:
            raise Exception("Not enough smart class parameters. Please "
                            "update puppet module.")

    @tier2
    def test_positive_list(self):
        """List all the parameters included in specific elements.

        :id: 9fcfbe32-d388-435d-a629-6969a50a4243

        :expectedresults: Parameters listed for specific Environment
            (by name and id), Host (name, id), Hostgroup (name, id),
            and puppetclass (name)

        :CaseLevel: Integration
        """

        list_queries = [
            {'environment': self.env['name']},
            {'environment-id': self.env['id']},
            {'host': self.host.name},
            {'host-id': self.host.id},
            {'hostgroup': self.hostgroup["name"]},
            {'hostgroup-id': self.hostgroup["id"]},
            {'puppet-class': self.puppet_class['name']},
        ]

        # override an example parameter
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'id': sc_param_id,
            'override': 1,
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['override'], True)

        # check listing parameters for selected queries
        for query in list_queries:
            sc_params = SmartClassParameter.list(query)
            self.assertGreater(
                    len(sc_params), 0,
                    "Failed to list parameters for query: {}".format(query))

            self.assertIn(sc_param_id, [scp['id'] for scp in sc_params])

            # Check that only unique results are returned
            self.assertEqual(
                len(sc_params),
                len({scp['id'] for scp in sc_params}),
                "Not only unique resutls returned for query: {}".format(query)
            )

    @tier1
    def test_positive_list_with_non_admin_user(self):
        """List all the parameters for specific puppet class by id.

        :id: 00fbf150-34fb-45d0-80e9-d5798d24a24f

        :expectedresults: Parameters listed for specific Puppet class.

        :BZ: 1391556

        :CaseImportance: Critical
        """
        password = gen_string('alpha')
        required_user_permissions = {
            'Puppetclass': {'permissions': ['view_puppetclasses']},
            'PuppetclassLookupKey': {'permissions': [
                    'view_external_parameters',
                    'create_external_parameters',
                    'edit_external_parameters',
                    'destroy_external_parameters',
                ]},
        }
        user = make_user({
            'admin': '0',
            'password': password,
        })
        role = make_role()
        add_role_permissions(role['id'], required_user_permissions)
        # Add the created and initiated role with permissions to user
        User.add_role({'id': user['id'], 'role-id': role['id']})
        sc_params = SmartClassParameter.with_user(
            user['login'],
            password,
        ).list({'puppet-class-id': self.puppet_class['id']})
        self.assertGreater(len(sc_params), 0)
        # Check that only unique results are returned
        self.assertEqual(len(sc_params), len({scp['id'] for scp in sc_params}))

    @tier1
    def test_positive_import_twice_list_by_puppetclass_id(self):
        """Import same puppet class twice (e.g. into different Content Views)
        but list class parameters only for specific puppet class.

        :id: 79a33641-54af-4e04-89ff-3b7f9a4e3ec2

        :expectedresults: Parameters listed for specific Puppet class.

        BZ: 1385351

        :CaseImportance: Critical
        """
        cv = publish_puppet_module(
            self.puppet_modules, CUSTOM_PUPPET_REPO, self.org['id'])
        env = Environment.list({
            'search': u'content_view="{0}"'.format(cv['name'])
        })[0]
        puppet_class = Puppet.info({
            'name': self.puppet_modules[0]['name'],
            'environment': env['name'],
        })
        sc_params = SmartClassParameter.list({
            'environment': env['name'],
            'puppet-class-id': puppet_class['id'],
            'per-page': 1000,
        })
        self.assertGreater(len(sc_params), 0)
        # Check that only unique results are returned
        self.assertEqual(len(sc_params), len({scp['id'] for scp in sc_params}))

    @tier1
    @upgrade
    def test_positive_override(self):
        """Override the Default Parameter value.

        :id: 25e34bac-084c-4b68-a082-822633e19f7e

        :steps:

            1.  Override the parameter.
            2.  Set the new valid Default Value.
            3.  Set puppet default value to 'Use Puppet Default'.
            4.  Submit the changes.

        :expectedresults: Parameter Value overridden with new value.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        value = gen_string('alpha')
        SmartClassParameter.update({
            'default-value': value,
            'use-puppet-default': 1,
            'id': sc_param_id,
            'override': 1,
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['default-value'], value)
        self.assertEqual(sc_param['use-puppet-default'], True)

    @tier1
    def test_negative_override(self):
        """Override the Default Parameter value - override Unchecked.

        :id: eb24c44d-0e34-40a3-aa3e-05a3cd4ed1ea

        :steps:

            1.  Don't override the parameter.
            2.  Set the new valid Default Value.
            3.  Attempt to submit the changes.

        :expectedresults: Not overridden parameter value cannot be updated.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        with self.assertRaises(CLIReturnCodeError):
            SmartClassParameter.update({
                'default-value': gen_string('alpha'),
                'id': sc_param_id,
            })

    @tier1
    @upgrade
    def test_positive_validate_default_value_required_check(self):
        """No error raised for non-empty default Value - Required check.

        :id: 812aceb8-8d5e-4374-bf73-61d7085ee510

        :steps:

            1.  Override the parameter.
            2.  Provide some default value, Not empty.
            3.  Set '--required' check.
            4.  Submit the change.

        :expectedresults: No error raised for non-empty default value

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'parameter-type': 'boolean',
            'id': sc_param_id,
            'default-value': u'true',
            'override': 1,
            'required': 1
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['required'], True)
        self.assertEqual(sc_param['default-value'], True)

    @tier1
    def test_positive_validate_matcher_value_required_check(self):
        """Error not raised for matcher Value - Required check.

        :id: e62c3c5a-d900-44d4-9793-2c17202974e5

        :steps:

            1.  Override the parameter.
            2.  Create a matcher for Parameter for some attribute.
            3.  Provide some Value for matcher.
            4.  Set '--required' check.
            5.  Submit the change.

        :expectedresults: Error not raised for matcher value.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.add_override_value({
            'smart-class-parameter-id': sc_param_id,
            'match': 'domain=example.com',
            'value': gen_string('alpha')
        })
        SmartClassParameter.update({
            'id': sc_param_id,
            'override': 1,
            'required': 1
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['required'], True)

    @tier1
    def test_negative_validate_default_value_with_regex(self):
        """Error raised for default value not matching with regex.

        :id: f36ed6e8-04ef-4614-98b3-38703d8aeeb0

        :steps:

            1.  Override the parameter.
            2.  Provide default value that doesn't matches the regex of step 3.
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for default value not matching with
            regex.

        :CaseImportance: Critical
        """
        value = gen_string('alpha')
        sc_param_id = self.sc_params_ids_list.pop()
        with self.assertRaises(CLIReturnCodeError):
            SmartClassParameter.update({
                'id': sc_param_id,
                'default-value': value,
                'override': 1,
                'validator-type': 'regexp',
                'validator-rule': '[0-9]',
            })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertNotEqual(sc_param['default-value'], value)

    @tier1
    @upgrade
    def test_positive_validate_default_value_with_regex(self):
        """Error not raised for default value matching with regex.

        :id: 74666d12-e3be-46c1-8bd5-18d86dcf7f4b

        :steps:

            1.  Override the parameter.
            2.  Provide default value that matches the regex of step 3.
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for default value matching with
            regex.

        :CaseImportance: Critical
        """
        value = gen_string('numeric')
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'id': sc_param_id,
            'default-value': value,
            'override': 1,
            'validator-type': 'regexp',
            'validator-rule': '[0-9]',
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['default-value'], value)
        self.assertEqual(sc_param['validator']['type'], 'regexp')
        self.assertEqual(sc_param['validator']['rule'], '[0-9]')

    @tier1
    def test_negative_validate_matcher_value_with_regex(self):
        """Error raised for matcher value not matching with regex.

        :id: b8b2f1c2-a20c-42d6-a687-79e6eee0268e

        :steps:

            1.  Override the parameter.
            2.  Create a matcher with value that doesn't match the regex of
                step 3.
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for matcher value not matching with
            regex.

        :CaseImportance: Critical
        """
        value = gen_string('numeric')
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.add_override_value({
            'smart-class-parameter-id': sc_param_id,
            'match': 'domain=test.com',
            'value': gen_string('alpha')
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartClassParameter.update({
                'id': sc_param_id,
                'default-value': value,
                'override': 1,
                'validator-type': 'regexp',
                'validator-rule': '[0-9]',
            })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertNotEqual(sc_param['default-value'], value)

    @tier1
    def test_positive_validate_matcher_value_with_regex(self):
        """Error not raised for matcher value matching with regex.

        :id: 2c8273aa-e621-4d4e-b03e-f8d50a596bc2

        :steps:

            1.  Override the parameter.
            2.  Create a matcher with value that matches the regex of step 3.
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for matcher value matching with
            regex.

        :CaseImportance: Critical
        """
        value = gen_string('numeric')
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.add_override_value({
            'smart-class-parameter-id': sc_param_id,
            'match': 'domain=test.com',
            'value': gen_string('numeric')
        })
        SmartClassParameter.update({
            'id': sc_param_id,
            'default-value': value,
            'override': 1,
            'validator-type': 'regexp',
            'validator-rule': '[0-9]',
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['default-value'], value)

    @tier1
    def test_negative_validate_default_value_with_list(self):
        """Error raised for default value not in list.

        :id: cdcafbea-612e-4b60-90de-fa0c76442bbe

        :steps:

            1.  Override the parameter.
            2.  Provide default value that doesn't matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for default value not in list.

        :CaseImportance: Critical
        """
        value = gen_string('alphanumeric')
        sc_param_id = self.sc_params_ids_list.pop()
        with self.assertRaises(CLIReturnCodeError):
            SmartClassParameter.update({
                'id': sc_param_id,
                'default-value': value,
                'override': 1,
                'validator-type': 'list',
                'validator-rule': '5, test',
            })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertNotEqual(sc_param['default-value'], value)

    @tier1
    def test_positive_validate_default_value_with_list(self):
        """Error not raised for default value in list.

        :id: b03708e8-e597-40fb-bb24-a1ac87475846

        :steps:

            1.  Override the parameter.
            2.  Provide default value that matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for default value in list.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'id': sc_param_id,
            'default-value': 'test',
            'override': 1,
            'validator-type': 'list',
            'validator-rule': '5, test',
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['default-value'], 'test')
        self.assertEqual(sc_param['validator']['type'], 'list')
        self.assertEqual(sc_param['validator']['rule'], '5, test')

    @tier1
    def test_negative_validate_matcher_value_with_list(self):
        """Error raised for matcher value not in list.

        :id: 6e02c3f2-40aa-49ec-976d-7a12f5fa1e04

        :steps:

            1.  Override the parameter.
            2.  Create a matcher with value that doesn't match the list of step
                3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for matcher value not in list.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.add_override_value({
            'smart-class-parameter-id': sc_param_id,
            'match': 'domain=test.com',
            'value': 'myexample'
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartClassParameter.update({
                'id': sc_param_id,
                'default-value': '50',
                'override': 1,
                'validator-type': 'list',
                'validator-rule': '25, example, 50',
            })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertNotEqual(sc_param['default-value'], '50')

    @tier1
    @upgrade
    def test_positive_validate_matcher_value_with_list(self):
        """Error not raised for matcher value in list.

        :id: 16927050-0bf2-4cbd-bb34-43c669f81304

        :steps:

            1.  Override the parameter.
            2.  Create a matcher with value that matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for matcher value in list.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.add_override_value({
            'smart-class-parameter-id': sc_param_id,
            'match': 'domain=test.com',
            'value': '30'
        })
        SmartClassParameter.update({
            'id': sc_param_id,
            'default-value': 'example',
            'override': 1,
            'validator-type': 'list',
            'validator-rule': 'test, example, 30',
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['default-value'], 'example')

    @tier1
    def test_negative_validate_matcher_value_with_default_type(self):
        """Error raised for matcher value not of default type.

        :id: 307b0ea1-a035-4ce1-bcc5-f582147359e7

        :steps:

            1.  Override the parameter.
            2.  Update parameter default type with valid value.
            3.  Create a matcher with value that doesn't matches the default
                type.
            4.  Submit the change.

        :expectedresults: Error raised for matcher value not of default type.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'id': sc_param_id,
            'parameter-type': 'boolean',
            'override': 1,
            'default-value': u'true',
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartClassParameter.add_override_value({
                'smart-class-parameter-id': sc_param_id,
                'match': 'domain=test.com',
                'value': gen_string('alpha')
            })

    @tier1
    def test_positive_validate_matcher_value_with_default_type(self):
        """No error for matcher value of default type.

        :id: a247adac-4631-4b90-ae4a-a768cd05be34

        :steps:

            1.  Override the parameter.
            2.  Update parameter default type with valid value.
            3.  Create a matcher with value that matches the default type.
            4.  Submit the change.

        :expectedresults: Error not raised for matcher value of default type.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'id': sc_param_id,
            'parameter-type': 'boolean',
            'override': 1,
            'default-value': u'true',
        })
        SmartClassParameter.add_override_value({
            'smart-class-parameter-id': sc_param_id,
            'match': 'domain=test.com',
            'value': u'false'
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(
            sc_param['override-values']['values']['1']['match'],
            'domain=test.com'
        )
        self.assertEqual(
            sc_param['override-values']['values']['1']['value'], False)

    @tier1
    def test_negative_validate_matcher_and_default_value(self):
        """Error for invalid default and matcher value both at a time.

        :id: 07dfcdad-e619-4672-9fe8-75a8352e44a4

        :steps:

            1.  Override the parameter.
            2.  Update parameter default type with Invalid value.
            3.  Create a matcher with value that doesn't matches the default
                type.
            4.  Attempt to submit the change.

        :expectedresults: Error raised for invalid default and matcher value
            both.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.add_override_value({
            'smart-class-parameter-id': sc_param_id,
            'match': 'domain=test.com',
            'value': gen_string('alpha'),
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartClassParameter.update({
                'id': sc_param_id,
                'parameter-type': 'boolean',
                'override': 1,
                'default-value': gen_string('alpha'),
            })

    @tier1
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Error while creating matcher for Non Existing Attribute.

        :id: 5223e582-81b4-442d-b4ba-b16ede460ef6

        :steps:

            1.  Override the parameter.
            2.  Create a matcher with non existing attribute in org.
            3.  Attempt to submit the change.

        :expectedresults: Error raised for non existing attribute.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        with self.assertRaises(CLIReturnCodeError):
            SmartClassParameter.add_override_value({
                'smart-class-parameter-id': sc_param_id,
                'match': 'hostgroup=nonexistingHG',
                'value': gen_string('alpha')
            })

    @tier1
    def test_positive_create_matcher(self):
        """Create matcher for attribute in parameter.

        :id: 37fe299b-1e81-4faf-b1c3-2edfc3d53dc1

        :steps:

            1.  Override the parameter.
            2.  Set some default Value.
            3.  Create a matcher with all valid values.
            4.  Submit the change.

        :expectedresults: The matcher has been created successfully.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        value = gen_string('alpha')
        SmartClassParameter.update({
            'id': sc_param_id,
            'override': 1,
            'override-value-order': 'is_virtual',
        })
        SmartClassParameter.add_override_value({
            'smart-class-parameter-id': sc_param_id,
            'match': 'is_virtual=true',
            'value': value
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(
            sc_param['override-values']['values']['1']['match'],
            'is_virtual=true'
        )
        self.assertEqual(
            sc_param['override-values']['values']['1']['value'], value)

    @tier1
    def test_negative_create_matcher(self):
        """Error while creating matcher with empty value

        :id: d4d9f730-152c-428d-b48c-294a23b183ea

        :steps:

            1.  Override the parameter.
            2.  Create a matcher with empty value.
            3.  Attempt to submit the change.

        :expectedresults: Error is raised for attempt to add matcher with empty
            value

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'id': sc_param_id,
            'override': 1,
            'override-value-order': 'is_virtual',
        })
        with self.assertRaises(CLIReturnCodeError):
            SmartClassParameter.add_override_value({
                'smart-class-parameter-id': sc_param_id,
                'match': 'is_virtual=true',
                'value': '',
            })

    @tier1
    def test_positive_create_matcher_puppet_default_value(self):
        """Create matcher for attribute in parameter,
        Where Value is puppet default value.

        :id: c08fcf25-e5c7-411e-beed-3741a24496fd

        :steps:

            1.  Override the parameter.
            2.  Set some default Value.
            3.  Create matcher with valid attribute type, name and puppet
                default value.
            4.  Submit the change.

        :expectedresults: The matcher has been created successfully.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'id': sc_param_id,
            'override': 1,
            'default-value': gen_string('alpha'),
        })
        SmartClassParameter.add_override_value({
            'smart-class-parameter-id': sc_param_id,
            'match': 'domain=test.com',
            'use-puppet-default': 1
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(
            sc_param['override-values']['values']['1']['match'],
            'domain=test.com'
        )

    @stubbed()
    @tier1
    def test_positive_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host.

        :id: 77894977-0355-4309-8c96-09589ea7e814

        :steps:

            1.  Override the parameter.
            2.  Set some default Value.
            3.  Set fqdn as top priority attribute.
            4.  Create first matcher for fqdn with valid details.
            5.  Create second matcher for some attribute with valid details.
                Note - The fqdn/host should have this attribute.
            6.  Submit the change.
            7.  Go to YAML output of associated host.

        :expectedresults: The YAML output has the value only for fqdn matcher.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_create_matcher_attribute_priority(self):
        """Matcher Value set on Attribute Priority for Host - alternate priority.

        :id: 593a9327-9439-49f7-b952-70934c924535

        :steps:

            1.  Override the parameter.
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

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_create_matcher_merge_override(self):
        """Merge the values of all the associated matchers.

        :id: f394a41f-f516-4759-bfff-89d6e5ccffd5

        :steps:

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

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output doesn't have the default value of parameter.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_override(self):
        """Attempt to merge the values from non associated matchers.

        :id: fe936ad0-997f-468b-8113-f6a47d3e41eb

        :steps:

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

        :expectedresults:

            1.  The YAML output has the values only for fqdn.
            2.  The YAML output doesn't have the values for attribute which are
                not associated to host.
            3.  The YAML output doesn't have the default value of parameter.
            4.  Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_override_puppet_value(self):
        """Merge the values of all the associated matchers + puppet default value.

        :id: 64e0e9f4-7b75-410a-938e-67f8b32b7e1f

        :steps:

            1.  Override the parameter.
            2.  Set some default Value.
            3.  Create first matcher for attribute fqdn with valid details.
            4.  Create second matcher for other attribute with value as puppet
                default.
                Note - The fqdn/host should have this attribute.
            5.  Create more matchers for some more attributes with value as
                puppet default.
                Note - The fqdn/host should have this attributes.
            6.  Set '--merge overrides' check.
            7.  Set '--merge default' check.
            8.  Submit the change.
            9.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the value only for fqdn.
            2.  The YAML output doesn't have the puppet default values of
                matchers.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_create_matcher_merge_default(self):
        """Merge the values of all the associated matchers + default value.

        :id: df5a482a-09ec-4942-bc1f-1354eced6f66

        :steps:

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

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output has the default value of parameter.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_create_matcher_merge_default(self):
        """Empty default value is not shown in merged values.

        :id: d0ccb1fc-5620-4071-8bbc-7970def16cae

        :steps:

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

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output doesn't have the empty default value of
                parameter.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_create_matcher_merge_puppet_default(self):
        """Merge the values of all the associated matchers + puppet default value.

        :id: 3a69a439-987a-4901-b2cf-efc95945c634

        :steps:

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

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output doesn't have the puppet default value.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_create_matcher_avoid_duplicate(self):
        """Merge the values of all the associated matchers, remove duplicates.

        :id: 671c27c8-8270-41d6-8958-f76061a20c36

        :steps:

            1.  Override the parameter.
            2.  Set some default Value of array type.
            3.  Create first matcher for attribute fqdn with some value.
            4.  Create second matcher for other attribute with same value as
                fqdn matcher.
                Note - The fqdn/host should have this attribute.
            5.  Set '--merge overrides' check.
            6.  Set '--merge default' check.
            7.  Set '--avoid duplicate' check.
            8.  Submit the change.
            9.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output has the default value of parameter.
            3.  Duplicate values in YAML output are removed / not displayed.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_create_matcher_avoid_duplicate(self):
        """Duplicates not removed as they were not really present.

        :id: 98966558-475a-4f84-ba66-31eba38eb13f

        :steps:

            1.  Override the parameter.
            2.  Set some default Value of array type.
            3.  Create first matcher for attribute fqdn with some value.
            4.  Create second matcher for other attribute with other value than
                fqdn matcher and default value.
                Note - The fqdn/host should have this attribute.
            5.  Set '--merge overrides' check.
            6.  Set '--merge default' check.
            7.  Set '--merge avoid duplicates' check.
            8.  Submit the change.
            9.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all matchers.
            2.  The YAML output has the default value of parameter.
            3.  No value removed as duplicate value.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @upgrade
    def test_positive_remove_matcher(self):
        """Removal of matcher from parameter.

        :id: f51ea9ca-f57c-482e-841f-3ea5cc8f8958

        :steps:

            1. Override the parameter and create a matcher for some attribute.
            2. Remove the matcher created in step 1.

        :expectedresults: The matcher removed from parameter.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        value = gen_string('alpha')
        SmartClassParameter.update({
            'id': sc_param_id,
            'override': 1,
            'override-value-order': 'is_virtual',
        })
        SmartClassParameter.add_override_value({
            'smart-class-parameter-id': sc_param_id,
            'match': 'is_virtual=true',
            'value': value
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(len(sc_param['override-values']['values']), 1)
        SmartClassParameter.remove_override_value({
            'smart-class-parameter-id': sc_param_id,
            'id': sc_param['override-values']['values']['1']['id'],
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(len(sc_param['override-values']['values']), 0)

    @tier1
    def test_positive_hide_parameter_default_value(self):
        """Hide the default value of parameter.

        :id: a1e206ae-67dc-48f0-886e-d543c682af34

        :steps:

            1. Set the override flag for the parameter.
            2. Set some valid default value.
            3. Set 'Hidden Value' to true.

        :expectedresults: The 'hidden value' set to true for that parameter.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'id': sc_param_id,
            'override': 1,
            'default-value': gen_string('alpha'),
            'hidden-value': 1,
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['hidden-value?'], True)
        self.assertEqual(sc_param['default-value'], '*****')

    @tier1
    def test_positive_unhide_parameter_default_value(self):
        """Unhide the default value of parameter.

        :id: 3daf662f-a0dd-469c-8088-262bfaa5246a

        :steps:

            1. Set the override flag for the parameter.
            2. Set some valid default value.
            3. Set 'Hidden Value' to true and submit.
            4. After hiding, set the 'Hidden Value' to false.

        :expectedresults: The 'hidden value' set to false for that parameter.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'id': sc_param_id,
            'override': 1,
            'default-value': gen_string('alpha'),
            'hidden-value': 1,
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['hidden-value?'], True)
        SmartClassParameter.update({
            'id': sc_param_id,
            'hidden-value': 0,
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['hidden-value?'], False)

    @tier1
    @upgrade
    def test_positive_update_hidden_value_in_parameter(self):
        """Update the hidden default value of parameter.

        :id: 8602abc9-80bd-412d-bf46-68a1c7f832e4

        :steps:

            1. Set the override flag for the parameter.
            2. Set some valid default value.
            3. Set 'Hidden Value' to true and submit.
            4. Now in hidden state, update the default value.

        :expectedresults:

            1. The parameter default value is updated.
            2. The 'hidden value' displayed as true for that parameter.

        :CaseImportance: Critical
        """
        sc_param_id = self.sc_params_ids_list.pop()
        old_value = gen_string('alpha')
        new_value = gen_string('alpha')
        SmartClassParameter.update({
            'id': sc_param_id,
            'override': 1,
            'default-value': old_value,
            'hidden-value': 1,
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
            'show-hidden': 1,
        })
        self.assertEqual(sc_param['hidden-value?'], True)
        self.assertEqual(sc_param['default-value'], old_value)
        SmartClassParameter.update({
            'id': sc_param_id,
            'default-value': new_value,
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
            'show-hidden': 1,
        })
        self.assertEqual(sc_param['hidden-value?'], True)
        self.assertEqual(sc_param['default-value'], new_value)

    @tier1
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value.

        :id: 31069fff-c6d5-42b6-94f2-9551057eb15b

        :steps:

            1. Set the override flag for the parameter.
            2. Don't set any default value/Set empty value.
            3. Set 'Hidden Value' to true and submit.

        :expectedresults:

            1. The 'hidden value' set to true for that parameter.
            2. The default value is still empty on hide.

        :CaseImportance: Critical

        :CaseAutomation: automated
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'id': sc_param_id,
            'override': 1,
            'hidden-value': 1,
            'default-value': '',
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
            'show-hidden': 1,
        })
        self.assertFalse(sc_param['default-value'])
        self.assertEqual(sc_param['hidden-value?'], True)
