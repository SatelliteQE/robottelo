# -*- encoding: utf-8 -*-
"""Test class for Users UI"""

from robottelo.decorators import stubbed, tier1
from robottelo.test import UITestCase


class MyAccountTestCase(UITestCase):
    """Implements Users tests in UI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name

    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size

    """

    @stubbed()
    @tier1
    def test_positive_update_firstname(self):
        """Update Firstname in My Account

        @Feature: My Account - Positive Update

        @Steps:
        1. Update current User with all variations of Firstname in [1]

        @Assert: Current User is updated

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_update_surname(self):
        """Update Surname in My Account

        @Feature: My Account - Positive Update

        @Steps:
        1. Update current User with all variations of Surname in [1]

        @Assert: Current User is updated

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_update_email(self):
        """Update Email Address in My Account

        @Feature: My Account - Positive Update

        @Steps:
        1. Update current User with all variations of Email Address in [1]

        @Assert: Current User is updated

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_update_language(self):
        """Update Language in My Account

        @Feature: My Account - Positive Update

        @Steps:
        1. Update current User with all different Language options

        @Assert: Current User is updated

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_update_password(self):
        """Update Password/Verify fields in My Account

        @Feature: My Account - Positive Update

        @Steps:
        1. Update Password/Verify fields with all variations in [1]

        @Assert: User is updated

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_negative_update_firstname(self):
        """Update My Account with invalid FirstName

        @Feature: My Account - Negative Update

        @Steps:
        1. Update Current user with all variations of FirstName in [2]

        @Assert: User is not updated. Appropriate error shown.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_negative_update_surname(self):
        """Update My Account with invalid Surname

        @Feature: My Account - Negative Update

        @Steps:
        1. Update Current user with all variations of Surname in [2]

        @Assert: User is not updated. Appropriate error shown.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_negative_update_email(self):
        """Update My Account with invalid Email Address

        @Feature: My Account - Negative Update

        @Steps:
        1. Update Current user with all variations of Email Address in [2]

        @Assert: User is not updated. Appropriate error shown.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_negative_update_password(self):
        """Update My Account with invalid Password/Verify fields

        @Feature: My Account - Negative Update

        @Steps:
        1. Update Current user with all variations of Password/Verify fields
        in [2]

        @Assert: User is not updated. Appropriate error shown.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_negative_update_password_mismatch(self):
        """Update My Account with non-matching values in Password and
        verify fields

        @Feature: My Account - Negative Update

        @Steps:
        1. Update Current user with non-matching values in Password and verify
        fields

        @Assert: User is not updated. Appropriate error shown.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_negative_update(self):
        """[UI ONLY] Attempt to update all info in My Accounts page and
        Cancel

        @Feature: My Account - Negative Update

        @Steps:
        1. Update Current user with valid Firstname, Surname, Email Address,
        Language, Password/Verify fields
        2. Click Cancel

        @Assert: User is not updated.

        @Status: Manual
        """
