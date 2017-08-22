# -*- encoding: utf-8 -*-
"""Test class for Users UI

:Requirement: Myaccount

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_alpha, gen_email
from nailgun.entities import User

from robottelo.constants import LANGUAGES
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import stubbed, tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.session import Session


def _valid_string_data(min_len=1, max_len=50):
    """Generates valid string data for ui tests

    :param min_len: min len for generated string
    :param max_len: max len for generated string. Default is 50 because of
    ui validation
    :return: list of generated strings
    """
    return generate_strings_list(
        min_length=min_len, max_length=max_len, exclude_types=['html']
    )


class MyAccountTestCase(UITestCase):
    """Implements Users tests in UI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, css,
    javascript, url, shell commands, sql, spaces in name

    [2] Negative Name Variations -  html, Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size
    """

    def setUp(self):
        """Setup of myaccount.

        Once following tests are going to update logged user, the default user
        can not be used once she is used on a bunch of other tests.

        So this method creates a new user for each test for the sake of
        isolation
        """
        super(MyAccountTestCase, self).setUp()
        password = 'password'
        self.account_user = User(password=password).create()
        self.account_password = password

    @tier1
    def test_positive_update_first_name(self):
        """Update Firstname in My Account

        :id: d5e617e6-ff61-451b-9e82-dd14e7348de6

        :Steps: Update current User with all variations of Firstname in [1]

        :expectedresults: Current User is updated

        :CaseImportance: Critical
        """
        valid_names = _valid_string_data()
        valid_names.append('name with space')
        for first_name in valid_names:
            with self.subTest(first_name):
                with Session(self, self.account_user.login,
                             self.account_password):
                    self.my_account.update(first_name=first_name)
                    self.assertEqual(
                        first_name,
                        self.my_account.get_field_value('first_name')
                    )

    @tier1
    def test_positive_update_email(self):
        """Update Email Address in My Account

        :id: 1c535b77-36d8-44d1-aaf0-07e0ca4eeb28

        :Steps: Update current User with with Email

        :expectedresults: Current User is updated

        :CaseImportance: Critical
        """
        with Session(self, self.account_user.login,
                     self.account_password):
            email = gen_email()
            self.my_account.update(email=email)
            self.assertEqual(email, self.my_account.get_field_value('email'))

    @tier1
    def test_positive_update_surname(self):
        """Update Surname in My Account

        :id: 755c1acc-901b-40de-8bdc-1eace9713ed7

        :Steps: Update current User with all variations of Surname in [1]

        :expectedresults: Current User is updated

        :caseautomation: notautomated

        :CaseImportance: Critical
        """
        valid_names = _valid_string_data()
        valid_names.append('name with space')
        for last_name in valid_names:
            with self.subTest(last_name):
                with Session(self, self.account_user.login,
                             self.account_password):
                    self.my_account.update(last_name=last_name)
                    self.assertEqual(
                        last_name,
                        self.my_account.get_field_value('last_name')
                    )

    @tier1
    def test_positive_update_language(self):
        """Update Language in My Account

        :id: 87604475-3a8e-4cb1-ace4-ea874b1d9e72

        :Steps: Update current User with all different Language options

        :expectedresults: Current User is updated

        :CaseImportance: Critical
        """
        for language, locale in LANGUAGES.items():
            with self.subTest(language):
                password = gen_alpha()
                user = User(password=password).create()
                with Session(self, user.login, password):
                    self.my_account.update(language=language)
                    # Cant use directly language because its value changes
                    # after updating current language
                    self.assertEqual(
                        locale, self.my_account.get_field_value('language'))

    @tier1
    @upgrade
    def test_positive_update_password(self):
        """Update Password/Verify fields in My Account

        :id: 3ab5d347-e02a-4d34-aec0-970419525268

        :Steps: Update Password/Verify fields with all variations in [1]

        :expectedresults: User is updated

        :CaseImportance: Critical
        """
        for password in _valid_string_data(max_len=254):
            with self.subTest(password):
                old_password = 'old_password'
                user = User(password=old_password).create()
                with Session(self, user.login, old_password):
                    self.my_account.update(
                        current_password=old_password, password=password,
                        password_confirmation=password)

                with Session(self, user.login, old_password):
                    self.assertFalse(self.login.is_logged())

                with Session(self, user.login, password):
                    self.assertTrue(self.login.is_logged())
                    # Check user can navigate to her own account again
                    self.my_account.navigate_to_entity()

    @stubbed()
    @tier1
    def test_negative_update_firstname(self):
        """Update My Account with invalid FirstName

        :id: 3b6250a5-437c-4540-8e95-32a915776f7f

        :Steps: Update Current user with all variations of FirstName in [2]

        :expectedresults: User is not updated. Appropriate error shown.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_update_surname(self):
        """Update My Account with invalid Surname

        :id: 97c9ae7b-73d8-4896-bff1-f701d2b53776

        :Steps: Update Current user with all variations of Surname in [2]

        :expectedresults: User is not updated. Appropriate error shown.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_update_email(self):
        """Update My Account with invalid Email Address

        :id: 06ace1c7-9a0e-4a0d-9b42-a5b510d697e1

        :Steps: Update Current user with all variations of Email Address in [2]

        :expectedresults: User is not updated. Appropriate error shown.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_update_password(self):
        """Update My Account with invalid Password/Verify fields

        :id: 09739b2e-8717-4104-a9c8-3377227599f0

        :Steps: Update Current user with all variations of Password/Verify
            fields in [2]

        :expectedresults: User is not updated. Appropriate error shown.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_update_password_mismatch(self):
        """Update My Account with non-matching values in Password and
        verify fields

        :id: b729ade7-ee69-4c43-a576-10be38f5c5fa

        :Steps: Update Current user with non-matching values in Password and
            verify fields

        :expectedresults: User is not updated. Appropriate error shown.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_update(self):
        """[UI ONLY] Attempt to update all info in My Accounts page and
        Cancel

        :id: 3867c4c3-b458-4d7b-a6c9-f2e65604e994

        :Steps:
            1. Update Current user with valid Firstname, Surname, Email
                Address, Language, Password/Verify fields
            2. Click Cancel

        :expectedresults: User is not updated.

        :caseautomation: notautomated

        :CaseImportance: Critical
        """
