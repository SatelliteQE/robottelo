# -*- encoding: utf-8 -*-
"""Test class for Environment  CLI"""

from fauxfactory import gen_string
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.environment import Environment
from robottelo.cli.factory import make_environment, make_location, make_org
from robottelo.decorators import data, run_only_on, skip_if_bug_open
from robottelo.helpers import bz_bug_is_open
from robottelo.test import MetaCLITestCase


@run_only_on('sat')
class TestEnvironment(MetaCLITestCase):

    factory = make_environment
    factory_obj = Environment

    POSITIVE_CREATE_DATA = (
        {'name': gen_string("alpha", 10)},
        {'name': gen_string("alphanumeric", 10)},
        {'name': gen_string("numeric", 10)},
    )

    POSITIVE_UPDATE_DATA = (
        ({'name': gen_string("alpha", 10)},
         {'new-name': gen_string("alpha", 10)}),
        ({'name': gen_string("alphanumeric", 10)},
         {'new-name': gen_string("alphanumeric", 10)}),
        ({'name': gen_string("numeric", 10)},
         {'new-name': gen_string("numeric", 10)}),
    )

    NEGATIVE_UPDATE_DATA = (
        ({'name': gen_string("alphanumeric", 10)},
         {'new-name': gen_string("alphanumeric", 300)}),
        ({'name': gen_string("alphanumeric", 10)},
         {'new-name': gen_string("latin1", 10)}),
        ({'name': gen_string("alphanumeric", 10)},
         {'new-name': gen_string("utf8", 10)}),
        ({'name': gen_string("alphanumeric", 10)},
         {'new-name': gen_string("html", 6)}),
        ({'name': gen_string("alphanumeric", 10)},
         {'new-name': ""}),
    )

    POSITIVE_DELETE_DATA = (
        {'name': gen_string("alpha", 10)},
        {'name': gen_string("alphanumeric", 10)},
        {'name': gen_string("numeric", 10)},
    )

    def test_info(self):
        """@Test: Test Environment Info

        @Feature: Environment - Info

        @Assert: Environment Info is displayed

        """
        name = gen_string("alpha", 10)
        Environment().create({'name': name})
        result = Environment().info({'name': name})

        self.assertTrue(result.return_code == 0,
                        "Environment info - retcode")

        self.assertEquals(result.stdout['name'], name,
                          "Environment info - stdout contains 'Name'")

    def test_list(self):
        """@Test: Test Environment List

        @Feature: Environment - List

        @Assert: Environment List is displayed

        """
        name = gen_string("alpha", 10)
        Environment().create({'name': name})
        result = Environment().list({'search': name})
        self.assertTrue(len(result.stdout) == 1,
                        "Environment list - stdout contains 'Name'")

    def test_create_environment_with_location(self):
        """@Test: Check if Environment with Location can be created

        @Feature: Environment - Create

        @Assert: Environment is created and has new Location assigned

        """
        name = gen_string("alpha", 10)
        try:
            new_loc = make_location()
            new_environment = make_environment({
                'name': name,
                'location-ids': new_loc["id"],
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertIn(new_loc['name'], new_environment['locations'])

    def test_create_environment_with_organization(self):
        """@Test: Check if Environment with Organization can be created

        @Feature: Environment - Create

        @Assert: Environment is created and has new Organization assigned

        """
        name = gen_string("alpha", 10)
        try:
            new_org = make_org()
            new_environment = make_environment({
                'name': name,
                'organization-ids': new_org["id"],
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertIn(new_org['name'], new_environment['organizations'])

    def test_delete(self):
        """@Test: Delete the environment

        @Feature: Environment - Delete

        @Assert: Environment Delete is displayed

        """

        name = gen_string("alphanumeric", 10)
        try:
            make_environment({'name': name})
        except CLIFactoryError as err:
            self.fail(err)

        result = Environment().delete({'name': name})
        self.assertEqual(result.return_code, 0, "Deletion failed")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an error here")

        result = Environment().info({'name': name})
        self.assertNotEqual(
            result.return_code, 0, "Environment should be deleted")
        self.assertGreater(len(result.stderr), 0,
                           "There should be an exception here")

    @data(*POSITIVE_UPDATE_DATA)
    def test_update(self, test_data):
        """@Test: Update the environment

        @Feature: Environment - Update

        @Assert: Environment Update is displayed

        """
        orig_dict, updates_dict = test_data
        try:
            make_environment({'name': orig_dict['name']})
        except CLIFactoryError as err:
            self.fail(err)

        result = Environment.update({
            'name': orig_dict['name'],
            'new-name': updates_dict['new-name']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = Environment.info({'name': updates_dict['new-name']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(result.stdout['name'], updates_dict['new-name'])

    @data(*NEGATIVE_UPDATE_DATA)
    def test_update_negative(self, test_data):
        """@Test: Update the environment with invalid values

        @Feature: Environment - Update

        @Assert: Environment is not updated

        """
        orig_dict, updates_dict = test_data
        try:
            env = make_environment({'name': orig_dict['name']})
        except CLIFactoryError as err:
            self.fail(err)

        result = Environment.update({
            'name': orig_dict['name'],
            'new-name': updates_dict['new-name']
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

        result = Environment.info({'id': env['id']})
        # Verify that value is not updated and left as it was before update
        # command was executed
        self.assertEqual(result.stdout['name'], orig_dict['name'])
        self.assertNotEqual(result.stdout['name'], updates_dict['new-name'])

    def test_update_location(self):
        """@Test: Update environment location with new value

        @Feature: Environment - Update

        @Assert: Environment Update finished and new location is assigned

        """
        try:
            old_loc = make_location()
            new_loc = make_location()
            env_name = gen_string('alphanumeric', 10)
            make_environment({
                'name': env_name,
                'location-ids': old_loc['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)
        result = Environment.info({'name': env_name})
        self.assertIn(old_loc['name'], result.stdout['locations'])

        result = Environment.update({
            'name': env_name,
            'location-ids': new_loc['id']
        })
        self.assertEqual(result.return_code, 0)

        result = Environment.info({'name': env_name})
        self.assertIn(new_loc['name'], result.stdout['locations'])
        self.assertNotIn(old_loc['name'], result.stdout['locations'])

    def test_update_organization(self):
        """@Test: Update environment organization with new value

        @Feature: Environment - Update

        @Assert: Environment Update finished and new organization is assigned

        """
        try:
            old_org = make_org()
            new_org = make_org()
            env_name = gen_string('alphanumeric', 10)
            make_environment({
                'name': env_name,
                'organization-ids': old_org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)
        result = Environment.info({'name': env_name})
        self.assertIn(old_org['name'], result.stdout['organizations'])

        result = Environment.update({
            'name': env_name,
            'organization-ids': new_org['id']
        })
        self.assertEqual(result.return_code, 0)

        result = Environment.info({'name': env_name})
        self.assertIn(new_org['name'], result.stdout['organizations'])
        self.assertNotIn(old_org['name'], result.stdout['organizations'])

    @skip_if_bug_open('bugzilla', 1219934)
    def test_sc_params_by_environment_id(self):
        """@Test: Check if environment sc-param subcommand works passing
        an environment id

        @Feature: Environment

        @Assert: The command runs without raising an error

        @BZ: 1219934

        """
        environment = make_environment()
        result = Environment.sc_params({
            'environment-id': environment['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        if not bz_bug_is_open(1219934):
            self.fail('BZ #1219934 is closed, should assert the content')

    @skip_if_bug_open('bugzilla', 1219934)
    def test_sc_params_by_environment_name(self):
        """@Test: Check if environment sc-param subcommand works passing
        an environment name

        @Feature: Environment

        @Assert: The command runs without raising an error

        @BZ: 1219934

        """
        environment = make_environment()
        result = Environment.sc_params({
            'environment': environment['name'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        if not bz_bug_is_open(1219934):
            self.fail('BZ #1219934 is closed, should assert the content')
