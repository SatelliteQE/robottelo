# -*- encoding: utf-8 -*-
"""Test class for Users CLI"""

from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_user
from robottelo.cli.user import User
from robottelo.datafactory import invalid_emails_list
from robottelo.decorators import stubbed, tier1
from robottelo.test import CLITestCase


class MyAccountTestCase(CLITestCase):
    """Implements My Account functionality tests in CLI"""

    @classmethod
    def setUpClass(cls):
        """Create a new user for all myaccount tests to not impact the default
        user
        """
        super(MyAccountTestCase, cls).setUpClass()

        login = gen_string('alphanumeric', 30)
        password = gen_string('alphanumeric', 30)
        cls.user = make_user({
            'login': login,
            'password': password,
            'admin': '1',
        })
        User.foreman_admin_username = login
        User.foreman_admin_password = password

    @classmethod
    def tearDownClass(cls):
        """Restore User object to previous state"""
        del User.foreman_admin_username
        del User.foreman_admin_password

        super(MyAccountTestCase, cls).tearDownClass()

    @tier1
    def test_positive_update_first_name(self):
        """Update Firstname in My Account

        @Feature: My Account - Positive Update

        @Assert: Current User is updated
        """
        new_firstname = gen_string('alphanumeric')
        User.update({'id': self.user['id'], 'firstname': new_firstname})
        result = User.info({'id': self.user['id']})
        updated_first_name = result['name'].split(' ')
        self.assertEqual(updated_first_name[0], new_firstname)

    @tier1
    def test_positive_update_surname(self):
        """Update Surname in My Account

        @Feature: My Account - Positive Update

        @Assert: Current User is updated
        """
        new_lastname = gen_string('alphanumeric')
        User.update({'id': self.user['id'], 'lastname': new_lastname})
        result = User.info({'id': self.user['id']})
        updated_last_name = result['name'].split(' ')
        self.assertEqual(updated_last_name[1], new_lastname)

    @tier1
    def test_positive_update_email(self):
        """Update Email Address in My Account

        @Feature: My Account - Positive Update

        @Assert: Current User is updated
        """
        email = u'{0}@example.com'.format(gen_string('alphanumeric'))
        User.update({'id': self.user['id'], 'mail': email})
        result = User.info({'id': self.user['id']})
        self.assertEqual(result['email'], email)

    @stubbed()
    @tier1
    def test_positive_update_language(self):
        """@Test: Update Language in My Account

        @Feature: My Account - Positive Update

        @Steps:
        1. Update current User with all different Language options

        @Assert: Current User is updated

        @Status: Manual
        """

    @tier1
    def test_positive_update_password(self):
        """Update Password in My Account

        @Feature: My Account - Positive Update

        @Assert: User is updated
        """
        password = gen_string('alphanumeric')
        User.update({
            'id': self.user['id'],
            'password': password,
        })
        User.foreman_admin_password = password
        result = User.info({'id': self.user['id']})
        self.assertTrue(result)

    @tier1
    def test_negative_update_first_name(self):
        """Update My Account with invalid FirstName

        @Feature: My Account - Negative Update

        @Assert: User is not updated. Appropriate error shown.
        """
        with self.assertRaises(CLIReturnCodeError):
            User.update({
                'id': self.user['id'],
                'firstname': gen_string('alphanumeric', 300),
            })

    @tier1
    def test_negative_update_surname(self):
        """Update My Account with invalid Surname

        @Feature: My Account - Negative Update

        @Assert: User is not updated. Appropriate error shown.
        """
        with self.assertRaises(CLIReturnCodeError):
            User.update({
                'id': self.user['id'],
                'lastname': gen_string('alphanumeric', 300),
            })

    @tier1
    def test_negative_update_email(self):
        """@Test: Update My Account with invalid Email Address

        @Feature: My Account - Negative Update

        @Assert: User is not updated. Appropriate error shown.
        """
        for email in invalid_emails_list():
            with self.subTest(email):
                with self.assertRaises(CLIReturnCodeError):
                    User.update({
                        'login': self.user['login'],
                        'mail': email,
                    })

    @stubbed()
    @tier1
    def test_negative_update_password_invalid(self):
        """@Test: Update My Account with invalid Password/Verify fields

        @Feature: My Account - Negative Update

        @Steps:
        1. Update Current user with all variations of Password/Verify fields
        in [2]

        @Assert: User is not updated. Appropriate error shown.

        @Status: Manual
        """
