# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for System CLI
"""

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.cli.factory import make_org, make_system
from robottelo.cli.system import System
from robottelo.common.decorators import data, bzbug
from robottelo.common.helpers import generate_string
from tests.foreman.cli.basecli import BaseCLI


@bzbug('1084722')
@ddt
class TestSystem(BaseCLI):
    """
    System CLI tests.
    """

    org = None

    def setUp(self):
        """
        Tests for Systems via Hammer CLI
        """

        super(TestSystem, self).setUp()

        if TestSystem.org is None:
            TestSystem.org = make_org()

    def _new_system(self, options=None):
        """
        Make a system group and asserts its success
        """

        if options is None:
            options = {}

        if not options.get('organization-id', None):
            options['organization-id'] = self.org['label']

        system = make_system(options)

        # Fetch it
        result = System.info(
            {
                'id': system['id']
            }
        )

        self.assertEqual(
            result.return_code,
            0,
            "System was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Return the system dictionary
        return system

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'system')
    def test_positive_create_1(self, test_data):
        """
        @Test: Check if system can be created with random names
        @Feature: Systems
        @Assert: System is created and has random name
        """

        new_system = self._new_system({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_system['name'],
            test_data['name'],
            "Names don't match"
        )

    @data(
        {'description': generate_string('alpha', 15)},
        {'description': generate_string('alphanumeric', 15)},
        {'description': generate_string('numeric', 15)},
        {'description': generate_string('latin1', 15)},
        {'description': generate_string('utf8', 15)},
        {'description': generate_string('html', 15)},
    )
    @attr('cli', 'system')
    def test_positive_create_2(self, test_data):
        """
        @Test: Check if system can be created with random description
        @Feature: Systems
        @Assert: System is created and has random description
        """

        new_system = self._new_system(
            {'description': test_data['description']})
        # Assert that description matches data passed
        self.assertEqual(
            new_system['description'],
            test_data['description'],
            "Descriptions don't match"
        )

    @data(
        {'name': generate_string('alpha', 300)},
        {'name': generate_string('alphanumeric', 300)},
        {'name': generate_string('numeric', 300)},
        {'name': generate_string('latin1', 300)},
        {'name': generate_string('utf8', 300)},
        {'name': generate_string('html', 300)},
    )
    @attr('cli', 'system')
    def test_negative_create_1(self, test_data):
        """
        @Test: Check if system can be created with random names
        @Feature: Systems
        @Assert: System is created and has random name
        """

        with self.assertRaises(Exception):
            self._new_system({'name': test_data['name']})

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'system')
    def test_positive_update_1(self, test_data):
        """
        @Test: Check if system name can be updated
        @Feature: Systems
        @Assert: System is created and name is updated
        @BZ: 1082157
        """

        new_system = self._new_system()
        # Assert that name does not matches data passed
        self.assertNotEqual(
            new_system['name'],
            test_data['name'],
            "Names should not match"
        )

        # Update system group
        result = System.update(
            {
                'id': new_system['id'],
                'organization-id': self.org['label'],
                'name': test_data['name']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "System was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = System.info(
            {
                'id': new_system['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "System was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # Assert that name matches new value
        self.assertIsNotNone(
            result.stdout.get('name', None),
            "The name field was not returned"
        )
        self.assertEqual(
            result.stdout['name'],
            test_data['name'],
            "Names should match"
        )
        # Assert that name does not match original value
        self.assertNotEqual(
            new_system['name'],
            result.stdout['name'],
            "Names should not match"
        )

    @data(
        {'description': generate_string('alpha', 15)},
        {'description': generate_string('alphanumeric', 15)},
        {'description': generate_string('numeric', 15)},
        {'description': generate_string('latin1', 15)},
        {'description': generate_string('utf8', 15)},
        {'description': generate_string('html', 15)},
    )
    @attr('cli', 'system')
    def test_positive_update_2(self, test_data):
        """
        @Test: Check if system description can be updated
        @Feature: Systems
        @Assert: System is created and description is updated
        @BZ: 1082157
        """

        new_system = self._new_system()
        # Assert that description does not match data passed
        self.assertNotEqual(
            new_system['description'],
            test_data['description'],
            "Descriptions should not match"
        )

        # Update sync plan
        result = System.update(
            {
                'id': new_system['id'],
                'organization-id': self.org['label'],
                'description': test_data['description']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "System was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = System.info(
            {
                'id': new_system['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "System was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # Assert that description matches new value
        self.assertIsNotNone(
            result.stdout.get('description', None),
            "The description field was not returned"
        )
        self.assertEqual(
            result.stdout['description'],
            test_data['description'],
            "Descriptions should match"
        )
        # Assert that description does not matches original value
        self.assertNotEqual(
            new_system['description'],
            result.stdout['description'],
            "Descriptions should not match"
        )

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'system')
    def test_positive_delete_1(self, test_data):
        """
        @Test: Check if system can be created and deleted
        @Feature: Systems
        @Assert: System is created and then deleted
        @BZ: 1082169
        """

        new_system = self._new_system({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_system['name'],
            test_data['name'],
            "Names don't match"
        )

        # Delete it
        result = System.delete({'id': new_system['id']})
        self.assertEqual(
            result.return_code,
            0,
            "System was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = System.info(
            {
                'id': new_system['id'],
            }
        )
        self.assertNotEqual(
            result.return_code,
            0,
            "System should not be found"
        )
        self.assertGreater(
            len(result.stderr),
            0,
            "Expected an error here"
        )
