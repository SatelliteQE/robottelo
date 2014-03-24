# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Subnet CLI
"""

from ddt import data
from ddt import ddt
from robottelo.cli.factory import make_subnet
from robottelo.cli.subnet import Subnet
from robottelo.common.helpers import generate_string
from nose.plugins.attrib import attr
from tests.cli.basecli import BaseCLI


@ddt
class TestSubnet(BaseCLI):
    """
    Subnet CLI tests.
    """

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'subnet')
    def test_positive_create_1(self, test_name):
        """
        @Test: Check if Subnet can be created with random names
        @Feature: Subnet - Create
        @Assert: Subnet is created and has random name
        """

        new_subnet = make_subnet({'name': test_name['name']})

        # Fetch it
        result = Subnet.info({'id': new_subnet['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Subnet was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['name'], new_subnet['name'], "Names don't match")

    @attr('cli', 'subnet')
    def test_list(self):
        """
        @Test: Check if Subnet can be listed
        @Feature: Subnet - List
        @Assert: Subnet is listed
        """

        # Fetch current total
        result = Subnet.list()
        total_subnet = len(result.stdout)

        # Make a new subnet
        make_subnet()

        # Fetch total again
        result = Subnet.list()
        self.assertGreater(
            len(result.stdout),
            total_subnet,
            "Total subnets should have increased")

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'subnet')
    def test_positive_update_1(self, test_name):
        """
        @Test: Check if Subnet name can be updated
        @Feature: Subnet - Update
        @Assert: Subnet name is updated
        """

        new_subnet = make_subnet()

        # Fetch it
        result = Subnet.info({'id': new_subnet['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Subnet was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Update the name
        result = Subnet.update(
            {'id': new_subnet['id'], 'new-name': test_name['name']})
        self.assertEqual(
            result.return_code,
            0,
            "Subnet was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it again
        result = Subnet.info({'id': new_subnet['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Subnet was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['name'], test_name['name'], "Names should match")
        self.assertNotEqual(
            result.stdout['name'], new_subnet['name'], "Names should not match"
        )

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'subnet')
    def test_positive_delete_1(self, test_name):
        """
        @Test: Check if Subnet can be deleted
        @Feature: Subnet - Delete
        @Assert: Subnet is deleted
        """

        new_subnet = make_subnet({'name': test_name['name']})

        # Fetch it
        result = Subnet.info({'id': new_subnet['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Subnet was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Delete it
        result = Subnet.delete({'id': result.stdout['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Subnet was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it again
        result = Subnet.info({'id': new_subnet['id']})
        self.assertGreater(
            result.return_code,
            0,
            "Subnet should not be found")
        self.assertGreater(
            len(result.stderr), 0, "No error was expected")
