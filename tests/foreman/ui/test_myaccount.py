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

from fauxfactory import gen_string, gen_alpha
from nailgun.entities import User
from robottelo.constants import LANGUAGES
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import stubbed, tier1
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators
from robottelo.ui.locators import locators
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
        """Setup of myaccount"""
        super(MyAccountTestCase, self).setUp()
        # Creating user for each test to not mess with default user
        user = User(login=gen_alpha(), password='password')
        # copying missing id because create returns only password's hash once
        # it is not stored in plain text for security reason
        user.id = user.create().id
        self.account_user = user

    def tearDown(self):
        """Deleting test user after each test"""
        super(MyAccountTestCase, self).tearDown()
        self.account_user.delete()

    def logged_test_user(self):
        """Create session with test user"""
        return Session(
            self.browser,
            self.account_user.login,
            self.account_user.password)

    def assert_text_field_update(self, locator_name, *new_values):
        """Check user account text property is updated

        :param locator_name: My Account form input locator
        :param new_values: new values to be checked for locator_name proper
        """
        locator = locators[locator_name]
        for new_value in new_values:
            with self.subTest(new_value):
                with self.logged_test_user():
                    self.my_account.navigate_to_entity()
                    self.my_account.wait_until_element(locator)
                    self.my_account.assign_value(locator, new_value)
                    self.my_account.click(common_locators['submit'])
                    self.my_account.wait_until_element_is_not_visible(
                        common_locators["notif.success"])
                    self.my_account.navigate_to_entity()

                    self.assertEqual(
                        new_value,
                        self.my_account.wait_until_element(
                            locator
                        ).get_attribute('value')
                    )

    @tier1
    def test_positive_update_firstname(self):
        """Update Firstname in My Account

        :id: d5e617e6-ff61-451b-9e82-dd14e7348de6

        :Steps: Update current User with all variations of Firstname in [1]

        :expectedresults: Current User is updated

        :CaseImportance: Critical
        """
        valid_strs = _valid_string_data()
        valid_strs.append('name with space')
        self.assert_text_field_update('users.firstname', *valid_strs)

    @tier1
    def test_positive_update_email(self):
        """Update Email Address in My Account

        :id: 1c535b77-36d8-44d1-aaf0-07e0ca4eeb28

        :Steps: Update current User with with Email

        :expectedresults: Current User is updated

        :CaseImportance: Critical
        """
        email = u'{0}@example.com'.format(gen_string('alpha'))
        self.assert_text_field_update('users.email', email)

    @tier1
    def test_positive_update_surname(self):
        """Update Surname in My Account

        :id: 755c1acc-901b-40de-8bdc-1eace9713ed7

        :Steps: Update current User with all variations of Surname in [1]

        :expectedresults: Current User is updated

        :caseautomation: notautomated

        :CaseImportance: Critical
        """
        valid_strs = _valid_string_data()
        valid_strs.append('name with space')
        self.assert_text_field_update('users.lastname', *valid_strs)

    @tier1
    def test_positive_update_language(self):
        """Update Language in My Account

        :id: 87604475-3a8e-4cb1-ace4-ea874b1d9e72

        :Steps: Update current User with all different Language options

        :expectedresults: Current User is updated

        :CaseImportance: Critical
        """

        for lang, locale in LANGUAGES.items():
            with self.subTest(lang):
                user = User(login=gen_alpha(), password='password')
                user.id = user.create().id
                with Session(self.browser, user.login, user.password):
                    self.my_account.navigate_to_entity()
                    self.my_account.select(
                        locators['users.language_dropdown'],
                        lang
                    )
                    self.my_account.click(common_locators['submit'])
                    self.my_account.wait_until_element_is_not_visible(
                        common_locators["notif.success"])
                    self.my_account.navigate_to_entity()
                    option = self.my_account.wait_until_element_exists(
                        locators['users.selected_lang'])
                    # Cant use directly lang because its value changes
                    # after updating current language
                    self.assertEqual(
                        locale,
                        option.get_attribute('value')
                    )
                user.delete()

    @tier1
    def test_positive_update_password(self):
        """Update Password/Verify fields in My Account

        :id: 3ab5d347-e02a-4d34-aec0-970419525268

        :Steps: Update Password/Verify fields with all variations in [1]

        :expectedresults: User is updated

        :CaseImportance: Critical
        """
        for password in _valid_string_data(max_len=254):
            with self.subTest(password):
                with self.logged_test_user():
                    self.my_account.navigate_to_entity()
                    self.my_account.wait_until_element(
                        locators['users.password'])
                    self.my_account.assign_value(
                        locators['users.password'], password)
                    self.my_account.assign_value(
                        locators['users.password_confirmation'], password)
                    self.my_account.click(common_locators['submit'])
                    self.my_account.wait_until_element_is_not_visible(
                        common_locators["notif.success"])
                    self.login.logout()
                    self.login.login(self.account_user.login, password)
                    self.assertTrue(self.login.is_logged())
                    # Updating test user password for next login
                    self.account_user.password = password

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
