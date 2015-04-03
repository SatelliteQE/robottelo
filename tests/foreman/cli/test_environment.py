# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""Test class for Environment  CLI"""

from fauxfactory import gen_string
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.environment import Environment
from robottelo.cli.factory import make_environment, make_location, make_org
from robottelo.common.decorators import run_only_on, data
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
