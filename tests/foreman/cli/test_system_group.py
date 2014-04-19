# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Product CLI
"""

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.cli.factory import make_org, make_system_group
from robottelo.cli.systemgroup import SystemGroup
from robottelo.common.decorators import data, bzbug
from robottelo.common.helpers import generate_string
from tests.foreman.cli.basecli import BaseCLI


@bzbug('1084240')
@ddt
class TestSystemGroup(BaseCLI):
    """
    System Group CLI tests.
    """

    org = None

    def setUp(self):
        """
        Tests for System Groups via Hammer CLI
        """

        super(TestSystemGroup, self).setUp()

        if TestSystemGroup.org is None:
            TestSystemGroup.org = make_org()

    def _new_system_group(self, options=None):
        """
        Make a system group and asserts its success
        """

        if options is None:
            options = {}

        if not options.get('organization-id', None):
            options['organization-id'] = self.org['label']

        group = make_system_group(options)

        # Fetch it
        result = SystemGroup.info(
            {
                'id': group['id']
            }
        )

        self.assertEqual(
            result.return_code,
            0,
            "System group was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Return the system group dictionary
        return group

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'systemgroup')
    def test_positive_create_1(self, test_data):
        """
        @Test: Check if systemgroup can be created with random names
        @Feature: Sync Plan
        @Assert: System group is created and has random name
        """

        new_system_group = self._new_system_group({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_system_group['name'],
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
    @attr('cli', 'systemgroup')
    def test_positive_create_2(self, test_data):
        """
        @Test: Check if systemgroup can be created with random description
        @Feature: Sync Plan
        @Assert: System group is created and has random description
        """

        new_system_group = self._new_system_group(
            {'description': test_data['description']})
        # Assert that description matches data passed
        self.assertEqual(
            new_system_group['description'],
            test_data['description'],
            "Descriptions don't match"
        )

    @data([-1, 0, 1, 5, 10, 20])
    @attr('cli', 'systemgroup')
    def test_positive_create_3(self, test_data):
        """
        @Test: Check if systemgroup can be created with random limits
        @Feature: Sync Plan
        @Assert: System group is created and has random limits
        """

        new_system_group = self._new_system_group(
            {'limit': test_data})
        # Assert that limit matches data passed
        self.assertEqual(
            new_system_group['limit'],
            test_data['limit'],
            "Limits don't match"
        )

    @data(
        {'name': generate_string('alpha', 300)},
        {'name': generate_string('alphanumeric', 300)},
        {'name': generate_string('numeric', 300)},
        {'name': generate_string('latin1', 300)},
        {'name': generate_string('utf8', 300)},
        {'name': generate_string('html', 300)},
    )
    @attr('cli', 'systemgroup')
    def test_negative_create_1(self, test_data):
        """
        @Test: Check if systemgroup can be created with random names
        @Feature: Sync Plan
        @Assert: System group is created and has random name
        """

        with self.assertRaises(Exception):
            self._new_system_group({'name': test_data['name']})

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'systemgroup')
    def test_positive_update_1(self, test_data):
        """
        @Test: Check if systemgroup name can be updated
        @Feature: Sync Plan
        @Assert: System group is created and name is updated
        @BZ: 1082157
        """

        new_system_group = self._new_system_group()
        # Assert that name does not matches data passed
        self.assertNotEqual(
            new_system_group['name'],
            test_data['name'],
            "Names should not match"
        )

        # Update system group
        result = SystemGroup.update(
            {
                'id': new_system_group['id'],
                'organization-id': self.org['label'],
                'name': test_data['name']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "System group was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = SystemGroup.info(
            {
                'id': new_system_group['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "System group was not updated")
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
            new_system_group['name'],
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
    @attr('cli', 'systemgroup')
    def test_positive_update_2(self, test_data):
        """
        @Test: Check if systemgroup description can be updated
        @Feature: Sync Plan
        @Assert: System group is created and description is updated
        @BZ: 1082157
        """

        new_system_group = self._new_system_group()
        # Assert that description does not match data passed
        self.assertNotEqual(
            new_system_group['description'],
            test_data['description'],
            "Descriptions should not match"
        )

        # Update sync plan
        result = SystemGroup.update(
            {
                'id': new_system_group['id'],
                'organization-id': self.org['label'],
                'description': test_data['description']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "System group was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = SystemGroup.info(
            {
                'id': new_system_group['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "System group was not updated")
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
            new_system_group['description'],
            result.stdout['description'],
            "Descriptions should not match"
        )

    @data([3, 6, 9, 12, 15, 17, 19])
    @attr('cli', 'systemgroup')
    def test_positive_update_3(self, test_data):
        """
        @Test: Check if systemgroup limits be updated
        @Feature: Sync Plan
        @Assert: System group limits is updated
        """

        new_system_group = self._new_system_group()

        # Update sync interval
        result = SystemGroup.update(
            {
                'id': new_system_group['id'],
                'organization-id': self.org['label'],
                'limit': test_data
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "System group was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = SystemGroup.info(
            {
                'id': new_system_group['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "System group was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # Assert that limit was updated
        self.assertEqual(
            result.stdout['limit'],
            test_data,
            "Limits don't match"
        )
        self.assertNotEqual(
            new_system_group['limit'],
            result.stdout['limit'],
            "Limits don't match"
        )

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'systemgroup')
    def test_positive_delete_1(self, test_data):
        """
        @Test: Check if systemgroup can be created and deleted
        @Feature: Sync Plan
        @Assert: System group is created and then deleted
        @BZ: 1082169
        """

        new_system_group = self._new_system_group({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_system_group['name'],
            test_data['name'],
            "Names don't match"
        )

        # Delete it
        result = SystemGroup.delete(
            {'id': new_system_group['id'],
             'organization-id': self.org['label']})
        self.assertEqual(
            result.return_code,
            0,
            "System group was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = SystemGroup.info(
            {
                'id': new_system_group['id'],
            }
        )
        self.assertNotEqual(
            result.return_code,
            0,
            "System group should not be found"
        )
        self.assertGreater(
            len(result.stderr),
            0,
            "Expected an error here"
        )
