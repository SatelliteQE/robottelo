# -*- encoding: utf-8 -*-
"""Test for Roles CLI"""
from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_role
from robottelo.cli.role import Role
from robottelo.constants import NOT_IMPLEMENTED
from robottelo.decorators import data, skip_if_bug_open
from robottelo.test import CLITestCase


@ddt
class TestRole(CLITestCase):
    """Test class for Roles CLI"""

    @skip_if_bug_open('bugzilla', 1138553)
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
    )
    def test_positive_create_role_1(self, name):
        """@Test: Create new roles and assign to the custom user

        @Feature: Roles

        @Assert: Assert creation of roles

        @BZ: 1138553

        """
        role = make_role({'name': name})
        self.assertEqual(role['name'], name)

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
    def test_positive_delete_role_1(self, name):
        """@Test: Delete roles after creating them

        @Feature: Roles

        @Assert: Assert deletion of roles

        """
        role = make_role({'name': name})
        self.assertEqual(role['name'], name)
        # Delete it
        Role.delete({'id': role['id']})
        # Fetch it
        with self.assertRaises(CLIReturnCodeError):
            Role.info({'id': role['id']})

    @skip_if_bug_open('bugzilla', 1138553)
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
    )
    def test_positive_update_role_1(self, new_name):
        """@Test: Update roles after creating them

        @Feature: Roles

        @Assert: Assert updating of roles

        """
        role = make_role({'name': gen_string('alpha', 15)})
        self.assertEqual(role['name'], new_name)
        # Update it
        Role.update({
            'id': role['id'],
            'new-name': new_name,
        })
        # Fetch it
        role = Role.info({'id': role['id']})
        # Assert that name was updated
        self.assertEqual(role['name'], new_name)
