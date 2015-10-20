# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test for Environment  CLI"""
from ddt import data
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.environment import Environment
from robottelo.cli.factory import make_environment, make_location, make_org
from robottelo.decorators import run_only_on, skip_if_bug_open
from robottelo.helpers import bz_bug_is_open, invalid_values_list
from robottelo.test import MetaCLITestCase


class TestEnvironment(MetaCLITestCase):
    """Test class for Environment CLI"""
    factory = make_environment
    factory_obj = Environment

    POSITIVE_CREATE_DATA = (
        {'name': gen_string('alpha', 10)},
        {'name': gen_string('alphanumeric', 10)},
        {'name': gen_string('numeric', 10)},
    )

    POSITIVE_UPDATE_DATA = (
        ({'name': gen_string('alpha', 10)},
         {'new-name': gen_string('alpha', 10)}),
        ({'name': gen_string('alphanumeric', 10)},
         {'new-name': gen_string('alphanumeric', 10)}),
        ({'name': gen_string('numeric', 10)},
         {'new-name': gen_string('numeric', 10)}),
    )

    NEGATIVE_UPDATE_DATA = (
        ({'name': gen_string('alphanumeric', 10)},
         {'new-name': gen_string('alphanumeric', 300)}),
        ({'name': gen_string('alphanumeric', 10)},
         {'new-name': gen_string('latin1', 10)}),
        ({'name': gen_string('alphanumeric', 10)},
         {'new-name': gen_string('utf8', 10)}),
        ({'name': gen_string('alphanumeric', 10)},
         {'new-name': gen_string('html', 6)}),
        ({'name': gen_string('alphanumeric', 10)},
         {'new-name': ''}),
    )

    POSITIVE_DELETE_DATA = (
        {'name': gen_string('alpha', 10)},
        {'name': gen_string('alphanumeric', 10)},
        {'name': gen_string('numeric', 10)},
    )

    @run_only_on('sat')
    def test_info(self):
        """@Test: Test Environment Info

        @Feature: Environment - Info

        @Assert: Environment Info is displayed

        """
        name = gen_string('alpha', 10)
        env = make_environment({'name': name})
        self.assertEquals(env['name'], name)

    @run_only_on('sat')
    def test_list(self):
        """@Test: Test Environment List

        @Feature: Environment - List

        @Assert: Environment List is displayed

        """
        name = gen_string('alpha', 10)
        Environment().create({'name': name})
        result = Environment().list({'search': name})
        self.assertEqual(len(result), 1)

    @run_only_on('sat')
    def test_create_environment_with_location(self):
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

    @run_only_on('sat')
    def test_create_environment_with_organization(self):
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

    @run_only_on('sat')
    def test_delete(self):
        """@Test: Delete the environment

        @Feature: Environment - Delete

        @Assert: Environment Delete is displayed

        """
        name = gen_string('alphanumeric', 10)
        make_environment({'name': name})
        Environment().delete({'name': name})
        with self.assertRaises(CLIReturnCodeError):
            Environment().info({'name': name})

    @data(
        gen_string('alpha', 10),
        gen_string('numeric', 10),
        gen_string('alphanumeric', 10),
    )
    @run_only_on('sat')
    def test_update(self, new_name):
        """@Test: Update the environment

        @Feature: Environment - Update

        @Assert: Environment Update is displayed

        """
        name = gen_string('alphanumeric')
        make_environment({'name': name})
        Environment.update({
            'name': name,
            'new-name': new_name,
        })
        env = Environment.info({'name': new_name})
        self.assertEqual(env['name'], new_name)

    @data(*invalid_values_list())
    @run_only_on('sat')
    def test_update_negative(self, new_name):
        """@Test: Update the environment with invalid values

        @Feature: Environment - Update

        @Assert: Environment is not updated

        """
        name = gen_string('alphanumeric')
        env = make_environment({'name': name})
        with self.assertRaises(CLIReturnCodeError):
            Environment.update({
                'name': name,
                'new-name': new_name,
            })
        env = Environment.info({'id': env['id']})
        # Verify that value is not updated and left as it was before update
        # command was executed
        self.assertEqual(env['name'], name)
        self.assertNotEqual(env['name'], new_name)

    @run_only_on('sat')
    def test_update_location(self):
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

    @run_only_on('sat')
    def test_update_organization(self):
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

    @skip_if_bug_open('bugzilla', 1219934)
    @run_only_on('sat')
    def test_sc_params_by_environment_id(self):
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

    @skip_if_bug_open('bugzilla', 1219934)
    @run_only_on('sat')
    def test_sc_params_by_environment_name(self):
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
