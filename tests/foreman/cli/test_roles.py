# -*- encoding: utf-8 -*-
"""Test for Roles CLI"""
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_role
from robottelo.cli.role import Role
from robottelo.decorators import skip_if_bug_open, stubbed
from robottelo.test import CLITestCase


def valid_names():
    """Returns a tuple of valid role names"""
    return(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
    )


class TestRole(CLITestCase):
    """Test class for Roles CLI"""

    @skip_if_bug_open('bugzilla', 1138553)
    def test_positive_create_role_1(self):
        """@Test: Create new roles and assign to the custom user

        @Feature: Roles

        @Assert: Assert creation of roles

        @BZ: 1138553

        """
        for name in valid_names():
            with self.subTest(name):
                role = make_role({'name': name})
                self.assertEqual(role['name'], name)

    @skip_if_bug_open('bugzilla', 1138559)
    @stubbed
    def test_create_role_permission_1(self):
        """@test: Create new roles Use different set of permission

           @feature: Roles

           @assert: Assert creation of roles with set of permission

           @status: manual

        """
        pass

    @skip_if_bug_open('bugzilla', 1138553)
    def test_positive_delete_role_1(self):
        """@Test: Delete roles after creating them

        @Feature: Roles

        @Assert: Assert deletion of roles

        """
        for name in valid_names():
            with self.subTest(name):
                role = make_role({'name': name})
                self.assertEqual(role['name'], name)
                Role.delete({'id': role['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Role.info({'id': role['id']})

    @skip_if_bug_open('bugzilla', 1138553)
    def test_positive_update_role_1(self):
        """@Test: Update roles after creating them

        @Feature: Roles

        @Assert: Assert updating of roles

        """
        role = make_role({'name': gen_string('alpha', 15)})
        for new_name in valid_names():
            with self.subTest(new_name):
                Role.update({
                    'id': role['id'],
                    'new-name': new_name,
                })
                role = Role.info({'id': role['id']})
                self.assertEqual(role['name'], new_name)
