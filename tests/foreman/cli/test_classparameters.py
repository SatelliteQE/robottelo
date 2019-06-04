# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Class Parameter

:Requirement: Classparameters

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Puppet

:TestType: Functional

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
    tier1,
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

    @tier1
    def test_positive_list(self):
        """List all the parameters included in specific elements.

        :id: 9fcfbe32-d388-435d-a629-6969a50a4243

        :expectedresults: Parameters listed for specific Environment
            (by name and id), Host (name, id), Hostgroup (name, id),
            and puppetclass (name)

        :CaseImportance: Medium
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

        :CaseImportance: Medium
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

        :CaseImportance: Low
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

        :CaseImportance: Medium
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

        :CaseImportance: Medium
        """
        sc_param_id = self.sc_params_ids_list.pop()
        with self.assertRaises(CLIReturnCodeError):
            SmartClassParameter.update({
                'default-value': gen_string('alpha'),
                'id': sc_param_id,
            })

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

        :CaseImportance: Medium
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
        """Error not raised for default value in list and required

        :id: b03708e8-e597-40fb-bb24-a1ac87475846

        :steps:

            1.  Override the parameter.
            2.  Provide default value that matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for default value in list.

        :CaseImportance: Medium
        """
        sc_param_id = self.sc_params_ids_list.pop()
        SmartClassParameter.update({
            'id': sc_param_id,
            'default-value': 'test',
            'override': 1,
            'validator-type': 'list',
            'validator-rule': '5, test',
            'required': 1
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertEqual(sc_param['default-value'], 'test')
        self.assertEqual(sc_param['validator']['type'], 'list')
        self.assertEqual(sc_param['validator']['rule'], '5, test')

    @tier1
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Error while creating matcher for Non Existing Attribute.

        :id: 5223e582-81b4-442d-b4ba-b16ede460ef6

        :steps:

            1.  Override the parameter.
            2.  Create a matcher with non existing attribute in org.
            3.  Attempt to submit the change.

        :expectedresults: Error raised for non existing attribute.

        :CaseImportance: Medium
        """
        sc_param_id = self.sc_params_ids_list.pop()
        with self.assertRaises(CLIReturnCodeError):
            SmartClassParameter.add_override_value({
                'smart-class-parameter-id': sc_param_id,
                'match': 'hostgroup=nonexistingHG',
                'value': gen_string('alpha')
            })

    @tier1
    @upgrade
    def test_positive_create_and_remove_matcher(self):
        """Create and remove matcher for attribute in parameter.

        :id: 37fe299b-1e81-4faf-b1c3-2edfc3d53dc1

        :steps:

            1.  Override the parameter.
            2.  Set some default Value.
            3.  Create a matcher with all valid values.
            4.  Create matcher with valid attribute type, name and puppet
                default value.
            5.  Submit the change.
            6.  Remove the matcher created in step 1

        :expectedresults: The matcher has been created successfully.

        :CaseImportance: Medium
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
            'value': value,
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

        :CaseImportance: Medium
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

    @tier1
    @upgrade
    def test_positive_test_hidden_parameter_value(self):
        """Unhide the default value of parameter.

        :id: 3daf662f-a0dd-469c-8088-262bfaa5246a

        :steps:

            1. Set the override flag for the parameter.
            2. Set some valid default value.
            3. Set 'Hidden Value' to true and submit.
            4. After hiding, set the 'Hidden Value' to false.
            5. Update the hidden value to empty value
            6. Unhide the variable

        :expectedresults:
            1. The 'hidden value' is corrctly created
            2. It is successfull updated
            3. It remains hidden when empty
            4. It is successfully unhidden

        :CaseImportance: Low
        """
        # Create with hidden value
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

        # Update to empty value
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

        # Unhide
        SmartClassParameter.update({
            'id': sc_param_id,
            'hidden-value': 0,
        })
        sc_param = SmartClassParameter.info({
            'puppet-class': self.puppet_class['name'],
            'id': sc_param_id,
        })
        self.assertFalse(sc_param['default-value'])
        self.assertEqual(sc_param['hidden-value?'], False)
