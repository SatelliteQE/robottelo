# -*- encoding: utf-8 -*-
"""Test for Roles CLI"""
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_role
from robottelo.cli.role import Role
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import skip_if_bug_open, stubbed, tier1
from robottelo.test import CLITestCase


class RoleTestCase(CLITestCase):
    """Test class for Roles CLI"""

    @skip_if_bug_open('bugzilla', 1138553)
    @tier1
    def test_positive_create_with_name(self):
        """@Test: Create new roles with provided name

        @Feature: Roles

        @Assert: Role is created and has correct name

        @BZ: 1138553
        """
        for name in generate_strings_list(length=10):
            with self.subTest(name):
                role = make_role({'name': name})
                self.assertEqual(role['name'], name)

    @skip_if_bug_open('bugzilla', 1138559)
    @stubbed
    def test_positive_create_with_permission(self):
        """@test: Create new role with a set of permission

        @feature: Roles

        @assert: Role is created and has correct set of permissions

        @status: manual
        """

    @skip_if_bug_open('bugzilla', 1138553)
    @tier1
    def test_positive_delete_by_id(self):
        """@Test: Create a new role and then delete role by its ID

        @Feature: Roles

        @Assert: Role is created and then deleted by its ID
        """
        for name in generate_strings_list(length=10):
            with self.subTest(name):
                role = make_role({'name': name})
                self.assertEqual(role['name'], name)
                Role.delete({'id': role['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Role.info({'id': role['id']})

    @skip_if_bug_open('bugzilla', 1138553)
    @tier1
    def test_positive_update_name(self):
        """@Test: Create new role and update its name

        @Feature: Roles

        @Assert: Role is created and its name is updated
        """
        role = make_role({'name': gen_string('alpha', 15)})
        for new_name in generate_strings_list(length=10):
            with self.subTest(new_name):
                Role.update({
                    'id': role['id'],
                    'new-name': new_name,
                })
                role = Role.info({'id': role['id']})
                self.assertEqual(role['name'], new_name)
