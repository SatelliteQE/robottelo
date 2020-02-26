# -*- encoding: utf-8 -*-
"""Test class for Users CLI

:Requirement: Myaccount

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_user
from robottelo.cli.user import User
from robottelo.constants import LOCALES
from robottelo.datafactory import invalid_emails_list
from robottelo.decorators import tier1
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


def _create_test_user(class_or_instance):
    """Helper function which creates test user and stores it on a class or
    instance.
    """
    class_or_instance.login = gen_string('alphanumeric', 30)
    class_or_instance.password = gen_string('alphanumeric', 30)
    class_or_instance.user = make_user(
        {'login': class_or_instance.login, 'password': class_or_instance.password, 'admin': '1'}
    )


def _delete_test_user(cls_or_instance):
    """Helper function which deletes test user stored on a class or
    instance.
    """
    User.delete({'id': cls_or_instance.user['id']})


def _update_test_user(cls_or_instance, options=None):
    """Helper function which updates test user stored on a class or
    instance.
    """
    options = options or {}
    options['id'] = cls_or_instance.user['id']
    user_cmd = User.with_user(cls_or_instance.login, cls_or_instance.password)
    return user_cmd.update(options)


def _test_user_info(cls_or_instance):
    """Helper function which fetch test user data stored on a class or
    instance.
    """
    user_cmd = User.with_user(cls_or_instance.login, cls_or_instance.password)
    return user_cmd.info({'id': cls_or_instance.user['id']})


class MyAccountTestCase(CLITestCase):
    """Implements My Account functionality tests in CLI.
    User is shared between all tests.
    So they must not change user's login nor password once these credentials
    are used on hammer authentication
    """

    @classmethod
    def setUpClass(cls):
        """Create a new user for all myaccount tests to not impact the default
        user.
        """
        super(MyAccountTestCase, cls).setUpClass()
        _create_test_user(cls)

    @classmethod
    def tearDownClass(cls):
        """Delete user created for tests"""
        super(MyAccountTestCase, cls).tearDownClass()
        _delete_test_user(cls)

    @classmethod
    def update_user(cls, options=None):
        """Update test user using cls.user credentials"""
        return _update_test_user(cls, options)

    @classmethod
    def user_info(cls):
        """Returns test user info"""
        return _test_user_info(cls)

    @tier1
    def test_positive_update_first_name(self):
        """Update Firstname in My Account

        :id: f8de3843-f2dc-4121-ab75-625c8f542627

        :expectedresults: Current User is updated

        :CaseImportance: Critical
        """
        new_firstname = gen_string('alphanumeric')
        self.update_user({'firstname': new_firstname})
        result = self.user_info()
        updated_first_name = result['name'].split(' ')
        self.assertEqual(updated_first_name[0], new_firstname)

    @tier1
    def test_positive_update_surname(self):
        """Update Surname in My Account

        :id: 40ad2e78-a2af-45ca-bbd8-e9ca5178dc41

        :expectedresults: Current User is updated

        :CaseImportance: Critical
        """
        new_lastname = gen_string('alphanumeric')
        self.update_user({'lastname': new_lastname})
        result = self.user_info()
        updated_last_name = result['name'].split(' ')
        self.assertEqual(updated_last_name[1], new_lastname)

    @tier1
    def test_positive_update_email(self):
        """Update Email Address in My Account

        :id: 70bab43b-0842-45a1-81fb-e47ff8646c8e

        :expectedresults: Current User is updated

        :CaseImportance: Critical
        """
        email = u'{0}@example.com'.format(gen_string('alphanumeric'))
        self.update_user({'mail': email})
        result = self.user_info()
        self.assertEqual(result['email'], email)

    @tier1
    def test_positive_update_all_locales(self):
        """Update Language in My Account

        :id: f0993495-5117-461d-a116-44867b820139

        :Steps: Update current User with all different Language options

        :expectedresults: Current User is updated

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

        for locale in LOCALES:
            with self.subTest(locale):
                self.update_user({'locale': locale})
                user = self.user_info()
                self.assertEqual(locale, user['locale'])

    @tier1
    def test_negative_update_first_name(self):
        """Update My Account with invalid FirstName

        :id: 1e0e1a94-4cef-4110-b65c-8cd35df254e0

        :expectedresults: User is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIReturnCodeError):
            self.update_user({'firstname': gen_string('alphanumeric', 300)})

    @tier1
    def test_negative_update_surname(self):
        """Update My Account with invalid Surname

        :id: 4d31ba71-2dcc-47ee-94d2-adc168ba89d7

        :expectedresults: User is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIReturnCodeError):
            self.update_user({'lastname': gen_string('alphanumeric', 300)})

    @tier1
    def test_negative_update_email(self):
        """Update My Account with invalid Email Address

        :id: 619f6285-8d50-47d4-b074-d8854c7567a6

        :expectedresults: User is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        for email in invalid_emails_list():
            with self.subTest(email):
                with self.assertRaises(CLIReturnCodeError):
                    self.update_user({'login': self.user['login'], 'mail': email})

    @tier1
    def test_negative_update_locale(self):
        """Update My Account with invalid Locale

        :id: 6f63c9b4-80e6-11e6-8ea1-68f72889dc7f

        :expectedresults: User is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIReturnCodeError):
            self.update_user({'locale': 'invalid'})


class MyAccountEphemeralUserTestCase(CLITestCase):
    """Implements My Account functionality tests in CLI for test that need
    to use ephemeral user. E.g. one user is created for each test so it can
    have whatever field updated"""

    login = None
    password = None
    user = None

    def setUp(self):
        """Create a new user for each test to not impact the default
        user.
        """
        super(MyAccountEphemeralUserTestCase, self).setUp()
        _create_test_user(self)

    def tearDown(self):
        """Delete user created on each test"""
        super(MyAccountEphemeralUserTestCase, self).tearDown()
        _delete_test_user(self)

    def update_user(self, options=None):
        """Update user using self.user credentials"""
        return _update_test_user(self, options)

    def user_info(self):
        """Returns test user info"""
        return _test_user_info(self)

    @tier1
    @upgrade
    def test_positive_update_password(self):
        """Update Password in My Account

        :id: e7e9b212-f0aa-4f7e-8433-b4639da89495

        :expectedresults: User is updated

        :CaseImportance: Critical
        """
        new_password = gen_string('alphanumeric')
        self.update_user({'password': new_password, 'current-password': self.password})
        # If password is updated, hammer authentication must fail because old
        # password stored on self is used
        self.assertRaises(CLIReturnCodeError, self.user_info)
