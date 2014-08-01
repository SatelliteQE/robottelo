# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Medium  CLI
"""

from robottelo.cli.factory import CLIFactoryError
from robottelo.test import CLITestCase
from robottelo.common.decorators import data
from ddt import ddt
from robottelo.common.helpers import generate_name, generate_string
from robottelo.cli.factory import make_medium, make_os
from robottelo.cli.medium import Medium
from robottelo.cli.operatingsys import OperatingSys


URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"
OSES = [
    'Archlinux',
    'Debian',
    'Gentoo',
    'Redhat',
    'Solaris',
    'Suse',
    'Windows',
]


@ddt
class TestMedium(CLITestCase):

    factory = make_medium
    factory_obj = Medium

    @data({'name': generate_string("latin1", 10)},
          {'name': generate_string("utf8", 10)},
          {'name': generate_string("alpha", 10)},
          {'name': generate_string("alphanumeric", 10)},
          {'name': generate_string("numeric", 10)},
          {'name': generate_string("html", 10)})
    def test_positive_create_1(self, test_data):
        """
        @Feature: Medium - Positive Create
        @Test: Check if Medium can be created
        @Assert: Medium is created
        """

        new_obj = make_medium(test_data)

        # Can we find the new object?
        result = Medium.info({'id': new_obj['id']})

        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")
        self.assertGreater(
            len(result.stdout), 0, "Failed to fetch medium")
        self.assertEqual(new_obj['name'],
                         result.stdout['name'])

    @data({'name': generate_string("latin1", 10)},
          {'name': generate_string("utf8", 10)},
          {'name': generate_string("alpha", 10)},
          {'name': generate_string("alphanumeric", 10)},
          {'name': generate_string("numeric", 10)},
          {'name': generate_string("html", 10)})
    def test_positive_delete_1(self, test_data):
        """
        @Feature: Medium - Positive Delete
        @Test: Check if Medium can be deleted
        @Assert: Medium is deleted
        """

        new_obj = make_medium(test_data)

        # Can we find the new object?
        result = Medium.info({'id': new_obj['id']})

        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(new_obj['name'], result.stdout['name'])

        return_value = Medium.delete({'id': new_obj['id']})
        self.assertEqual(return_value.return_code, 0, "Deletion failed")
        self.assertEqual(
            len(return_value.stderr), 0, "There should not be an error here")

        # Can we find the object?
        result = Medium.info({'id': new_obj['id']})
        self.assertNotEqual(
            result.return_code, 0, "Medium should be deleted")
        self.assertGreater(len(result.stderr), 0,
                           "There should be an exception here")
        self.assertEqual(
            len(result.stdout), 0, "Output should be blank.")

    def test_addoperatingsystem_medium(self):
        """
        @Test: Check if Medium can be associated with operating system
        @Feature: Medium - Add operating system
        @Assert: Operating system added
        """

        name = generate_name(6)
        try:
            medium = make_medium({'name': name})
        except CLIFactoryError as e:
            self.fail(e)

        try:
            os = make_os()
        except CLIFactoryError as e:
            self.fail(e)

        args = {'id': medium['id'],
                'operatingsystem-id': os['id']}

        result = Medium().add_operating_system(args)
        self.assertEqual(result.return_code, 0,
                         "Could not associate the operating system to media")
        self.assertEqual(len(result.stderr), 0,
                         "There should not be an exception here")
