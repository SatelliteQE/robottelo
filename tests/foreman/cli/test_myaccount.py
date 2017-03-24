# -*- encoding: utf-8 -*-
"""Test class for Users CLI

@Requirement: Myaccount

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

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

        @id: f8de3843-f2dc-4121-ab75-625c8f542627

        @expectedresults: Current User is updated
        """
        new_firstname = gen_string('alphanumeric')
        User.update({'id': self.user['id'], 'firstname': new_firstname})
        result = User.info({'id': self.user['id']})
        updated_first_name = result['name'].split(' ')
        self.assertEqual(updated_first_name[0], new_firstname)

    @tier1
    def test_positive_update_surname(self):
        """Update Surname in My Account

        @id: 40ad2e78-a2af-45ca-bbd8-e9ca5178dc41

        @expectedresults: Current User is updated
        """
        new_lastname = gen_string('alphanumeric')
        User.update({'id': self.user['id'], 'lastname': new_lastname})
        result = User.info({'id': self.user['id']})
        updated_last_name = result['name'].split(' ')
        self.assertEqual(updated_last_name[1], new_lastname)

    @tier1
    def test_positive_update_email(self):
        """Update Email Address in My Account

        @id: 70bab43b-0842-45a1-81fb-e47ff8646c8e

        @expectedresults: Current User is updated
        """
        email = u'{0}@example.com'.format(gen_string('alphanumeric'))
        User.update({'id': self.user['id'], 'mail': email})
        result = User.info({'id': self.user['id']})
        self.assertEqual(result['email'], email)

    @stubbed()
    @tier1
    def test_positive_update_language(self):
        """Update Language in My Account

        @id: f0993495-5117-461d-a116-44867b820139

        @Steps:
        1. Update current User with all different Language options

        @expectedresults: Current User is updated

        @caseautomation: notautomated
        """

    @tier1
    def test_positive_update_password(self):
        """Update Password in My Account

        @id: e7e9b212-f0aa-4f7e-8433-b4639da89495

        @expectedresults: User is updated
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

        @id: 1e0e1a94-4cef-4110-b65c-8cd35df254e0

        @expectedresults: User is not updated. Appropriate error shown.
        """
        with self.assertRaises(CLIReturnCodeError):
            User.update({
                'id': self.user['id'],
                'firstname': gen_string('alphanumeric', 300),
            })

    @tier1
    def test_negative_update_surname(self):
        """Update My Account with invalid Surname

        @id: 4d31ba71-2dcc-47ee-94d2-adc168ba89d7

        @expectedresults: User is not updated. Appropriate error shown.
        """
        with self.assertRaises(CLIReturnCodeError):
            User.update({
                'id': self.user['id'],
                'lastname': gen_string('alphanumeric', 300),
            })

    @tier1
    def test_negative_update_email(self):
        """Update My Account with invalid Email Address

        @id: 619f6285-8d50-47d4-b074-d8854c7567a6

        @expectedresults: User is not updated. Appropriate error shown.
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
        """Update My Account with invalid Password/Verify fields

        @id: f9230699-fb8e-45d6-a0c2-abb8b751304d

        @Steps:
        1. Update Current user with all variations of Password/Verify fields
        in [2]

        @expectedresults: User is not updated. Appropriate error shown.

        @caseautomation: notautomated
        """
