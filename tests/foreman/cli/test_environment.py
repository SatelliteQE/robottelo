# -*- encoding: utf-8 -*-
"""Test for Environment  CLI"""
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
    bz_bug_is_open,
    run_only_on,
    skip_if_bug_open,
    tier1,
    tier2,
)
from robottelo.test import CLITestCase


class EnvironmentTestCase(CLITestCase):
    """Test class for Environment CLI"""
    @tier2
    @run_only_on('sat')
    def test_positive_list_with_name(self):
        """@Test: Test Environment List

        @Feature: Environment

        @Assert: Environment list is displayed
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
        """@Test: Successfully creates an Environment.

        @Feature: Environment

        @Assert: Environment is created.
        """
        for name in valid_environments_list():
            with self.subTest(name):
                environment = make_environment({'name': name})
                self.assertEqual(environment['name'], name)

    @tier1
    def test_negative_create_with_name(self):
        """@Test: Don't create an Environment with invalid data.

        @Feature: Environment

        @Assert: Environment is not created.
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    Environment.create({'name': name})

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_loc(self):
        """@Test: Check if Environment with Location can be created

        @Feature: Environment - Create

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
        """@Test: Check if Environment with Organization can be created

        @Feature: Environment - Create

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
        """@test: Create Environment with valid values then delete it
        by ID

        @feature: Environment

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
        """@test: Create Environment then delete it by wrong ID

        @feature: Environment

        @assert: Environment is not deleted
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    Environment.delete({'id': entity_id})

    @tier1
    @run_only_on('sat')
    def test_positive_delete_by_name(self):
        """@Test: Delete the environment by its name.

        @Feature: Environment

        @Assert: Environment is deleted.
        """
        environment = make_environment()
        Environment.delete({'name': environment['name']})
        with self.assertRaises(CLIReturnCodeError):
            Environment.info({'name': environment['name']})

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """@Test: Update the environment

        @Feature: Environment - Update

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
        """@Test: Update the Environment with invalid values

        @Feature: Environment

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
        """@Test: Update environment location with new value

        @Feature: Environment - Update

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
        """@Test: Update environment organization with new value

        @Feature: Environment - Update

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
    @skip_if_bug_open('bugzilla', 1219934)
    @run_only_on('sat')
    def test_positive_sc_params_by_id(self):
        """@Test: Check if environment sc-param subcommand works passing
        an environment id

        @Feature: Environment

        @Assert: The command runs without raising an error

        @BZ: 1219934

        """
        environment = make_environment()
        Environment.sc_params({
            'environment-id': environment['id'],
        })
        if not bz_bug_is_open(1219934):
            self.fail('BZ #1219934 is closed, should assert the content')

    @tier1
    @skip_if_bug_open('bugzilla', 1219934)
    @run_only_on('sat')
    def test_positive_sc_params_by_name(self):
        """@Test: Check if environment sc-param subcommand works passing
        an environment name

        @Feature: Environment

        @Assert: The command runs without raising an error

        @BZ: 1219934

        """
        environment = make_environment()
        Environment.sc_params({
            'environment': environment['name'],
        })
        if not bz_bug_is_open(1219934):
            self.fail('BZ #1219934 is closed, should assert the content')
