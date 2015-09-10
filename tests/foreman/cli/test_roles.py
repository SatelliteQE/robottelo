# -*- encoding: utf-8 -*-
"""Test class for Roles CLI"""
from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.factory import CLIFactoryError, make_role
from robottelo.cli.role import Role
from robottelo.constants import NOT_IMPLEMENTED
from robottelo.decorators import data, skip_if_bug_open
from robottelo.test import CLITestCase


@ddt
class TestRole(CLITestCase):

    @skip_if_bug_open('bugzilla', 1138553)
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
    )
    def test_positive_create_role_1(self, data):
        """@Test: Create new roles and assign to the custom user

        @Feature: Roles

        @Assert: Assert creation of roles

        """
        try:
            role = make_role({'name': data})
        except CLIFactoryError as err:
            self.fail(err)
        self.assertEqual(
            role['name'],
            data, "Input and output name should be consistent")

    @skip_if_bug_open('bugzilla', 1138559)
    def test_create_role_permission_1(self):
        """@test: Create new roles Use different set of permission

           @feature: Roles

           @assert: Assert creation of roles with set of permission

           @status: manual

        """

        self.fail(NOT_IMPLEMENTED)

    @skip_if_bug_open('bugzilla', 1138553)
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
    )
    def test_positive_delete_role_1(self, data):
        """@Test: Delete roles after creating them

        @Feature: Roles

        @Assert: Assert deletion of roles

        """
        try:
            role = make_role({'name': data})
        except CLIFactoryError as err:
            self.fail(err)
        self.assertEqual(
            role['name'],
            data, "Input and output name should be consistent")

        # Delete it
        result = Role.delete({'id': role['id']})
        self.assertEqual(result.return_code, 0,
                         "Role was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = Role.info({'id': role['id']})
        self.assertNotEqual(result.return_code, 0,
                            "Role should not be found")
        self.assertGreater(len(result.stderr), 0,
                           "Expected an error here")

    @skip_if_bug_open('bugzilla', 1138553)
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
    )
    def test_positive_update_role_1(self, data):
        """@Test: Update roles after creating them

        @Feature: Roles

        @Assert: Assert updation of roles

        """
        name = gen_string('alpha', 15)
        try:
            role = make_role({'name': name})
        except CLIFactoryError as err:
            self.fail(err)
        self.assertEqual(
            role['name'],
            data, "Input and output name should be consistent")

        # Update it
        result = Role.update({'id': role['id'],
                              'new-name': data})
        self.assertEqual(result.return_code, 0,
                         "Role was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = Role.info({'id': role['id']})
        self.assertEqual(result.return_code, 0,
                         "Role was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # Assert that name was updated
        self.assertEqual(result.stdout['name'],
                         data,
                         "Names do not match")
