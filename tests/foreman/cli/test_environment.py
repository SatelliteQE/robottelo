# -*- encoding: utf-8 -*-
"""Test for Environment  CLI

@Requirement: Environment

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.environment import Environment
from robottelo.cli.factory import make_environment, make_location, make_org
from robottelo.datafactory import (
    invalid_id_list,
    invalid_values_list,
    valid_environments_list,
)
from robottelo.decorators import (
    run_only_on,
    tier1,
    tier2,
)
from robottelo.test import CLITestCase


class EnvironmentTestCase(CLITestCase):
    """Test class for Environment CLI"""
    @tier2
    @run_only_on('sat')
    def test_positive_list_with_name(self):
        """Test Environment List

        @id: 8a81f853-929c-4eaa-8ae0-4c92ebf1f250

        @Assert: Environment list is displayed

        @CaseLevel: Integration
        """
        for name in valid_environments_list():
            with self.subTest(name):
                Environment.create({'name': name})
                result = Environment.list({
                    'search': 'name={0}'.format(name)
                })
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]['name'], name)

    @tier1
    def test_positive_create_with_name(self):
        """Successfully creates an Environment.

        @id: 3b22f035-ee3a-489e-89c5-e54571584af1

        @Assert: Environment is created.
        """
        for name in valid_environments_list():
            with self.subTest(name):
                environment = make_environment({'name': name})
                self.assertEqual(environment['name'], name)

    @tier1
    def test_negative_create_with_name(self):
        """Don't create an Environment with invalid data.

        @id: 8a4141b0-3bb9-47e5-baca-f9f027086d4c

        @Assert: Environment is not created.
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    Environment.create({'name': name})

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_loc(self):
        """Check if Environment with Location can be created

        @id: d2187971-86b2-40c9-a93c-66f37691ae2b

        @Assert: Environment is created and has new Location assigned

        """
        new_loc = make_location()
        new_environment = make_environment({
            'location-ids': new_loc['id'],
            'name': gen_string('alpha'),
        })
        self.assertIn(new_loc['name'], new_environment['locations'])

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_org(self):
        """Check if Environment with Organization can be created

        @id: 9fd9d2d5-db46-40a7-b341-41cdbde4356a

        @Assert: Environment is created and has new Organization assigned

        """
        new_org = make_org()
        new_environment = make_environment({
            'name': gen_string('alpha'),
            'organization-ids': new_org['id'],
        })
        self.assertIn(new_org['name'], new_environment['organizations'])

    @tier1
    @run_only_on('sat')
    def test_positive_delete_by_id(self):
        """Create Environment with valid values then delete it
        by ID

        @id: e25af73a-d4ef-4287-83bf-625337d91392

        @assert: Environment is deleted
        """
        for name in valid_environments_list():
            with self.subTest(name):
                environment = make_environment({'name': name})
                Environment.delete({'id': environment['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Environment.info({'id': environment['id']})

    @tier1
    @run_only_on('sat')
    def test_negative_delete_by_id(self):
        """Create Environment then delete it by wrong ID

        @id: fe77920c-62fd-4e0e-b960-a940a1370d10

        @assert: Environment is not deleted
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    Environment.delete({'id': entity_id})

    @tier1
    @run_only_on('sat')
    def test_positive_delete_by_name(self):
        """Delete the environment by its name.

        @id: 48765173-6086-4b91-9da7-594135f68751

        @Assert: Environment is deleted.
        """
        environment = make_environment()
        Environment.delete({'name': environment['name']})
        with self.assertRaises(CLIReturnCodeError):
            Environment.info({'name': environment['name']})

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Update the environment

        @id: 7b34ce64-24be-4b3b-8f7e-1de07daafdd9

        @Assert: Environment Update is displayed
        """
        environment = make_environment()
        for new_name in valid_environments_list():
            with self.subTest(new_name):
                Environment.update({
                    'id': environment['id'],
                    'new-name': new_name,
                })
                environment = Environment.info({'id': environment['id']})
                self.assertEqual(environment['name'], new_name)

    @tier1
    @run_only_on('sat')
    def test_negative_update_name(self):
        """Update the Environment with invalid values

        @id: adc5ad73-0547-40f9-b4d4-649780cfb87a

        @Assert: Environment is not updated
        """
        environment = make_environment()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    Environment.update({
                        'id': environment['id'],
                        'new-name': new_name,
                    })
                result = Environment.info({'id': environment['id']})
                self.assertEqual(environment['name'], result['name'])

    @tier1
    @run_only_on('sat')
    def test_positive_update_loc(self):
        """Update environment location with new value

        @id: d58d6dc5-a820-4c61-bd69-0c631c2d3f2e

        @Assert: Environment Update finished and new location is assigned

        """
        old_loc = make_location()
        new_loc = make_location()
        new_env = make_environment({'location-ids': old_loc['id']})
        self.assertIn(old_loc['name'], new_env['locations'])
        Environment.update({
            'location-ids': new_loc['id'],
            'name': new_env['name'],
        })
        new_env = Environment.info({'name': new_env['name']})
        self.assertIn(new_loc['name'], new_env['locations'])
        self.assertNotIn(old_loc['name'], new_env['locations'])

    @tier1
    @run_only_on('sat')
    def test_positive_update_org(self):
        """Update environment organization with new value

        @id: 2c40caf9-95a0-4b87-bd97-0a4448746052

        @Assert: Environment Update finished and new organization is assigned

        """
        old_org = make_org()
        new_org = make_org()
        env_name = gen_string('alphanumeric', 10)
        env = make_environment({
            'name': env_name,
            'organization-ids': old_org['id'],
        })
        self.assertIn(old_org['name'], env['organizations'])
        Environment.update({
            'name': env_name,
            'organization-ids': new_org['id']
        })
        env = Environment.info({'name': env_name})
        self.assertIn(new_org['name'], env['organizations'])
        self.assertNotIn(old_org['name'], env['organizations'])

    @tier1
    @run_only_on('sat')
    def test_positive_sc_params_by_id(self):
        """Check if environment sc-param subcommand works passing
        an environment id

        @id: 32de4f0e-7b52-411c-a111-9ed472c3fc34

        @Assert: The command runs without raising an error

        """
        environment = make_environment()
        Environment.sc_params({'environment-id': environment['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_sc_params_by_name(self):
        """Check if environment sc-param subcommand works passing
        an environment name

        @id: e2fdd262-9b09-4252-8a5a-4e578e3b8547

        @Assert: The command runs without raising an error

        """
        environment = make_environment()
        Environment.sc_params({'environment': environment['name']})
