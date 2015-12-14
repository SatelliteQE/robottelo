# -*- encoding: utf-8 -*-
"""Test class for Users CLI"""

from robottelo.decorators import stubbed
from robottelo.test import CLITestCase


class MyAccountTestCase(CLITestCase):
    """Implements Users tests in CLI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name

    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size
    """

    @stubbed()
    def test_positive_update_first_name(self):
        """@Test: Update Firstname in My Account

        @Feature: My Account - Positive Update

        @Steps:
        1. Update current User with all variations of Firstname in [1]

        @Assert: Current User is updated

        @Status: Manual
        """

    @stubbed()
    def test_positive_update_surname(self):
        """@Test: Update Surname in My Account

        @Feature: My Account - Positive Update

        @Steps:
        1. Update current User with all variations of Surname in [1]

        @Assert: Current User is updated

        @Status: Manual
        """

    @stubbed()
    def test_positive_update_email(self):
        """@Test: Update Email Address in My Account

        @Feature: My Account - Positive Update

        @Steps:
        1. Update current User with all variations of Email Address in [1]

        @Assert: Current User is updated

        @Status: Manual
        """

    @stubbed()
    def test_positive_update_language(self):
        """@Test: Update Language in My Account

        @Feature: My Account - Positive Update

        @Steps:
        1. Update current User with all different Language options

        @Assert: Current User is updated

        @Status: Manual
        """

    @stubbed()
    def test_positive_update_password(self):
        """@Test: Update Password/Verify fields in My Account

        @Feature: My Account - Positive Update

        @Steps:
        1. Update Password/Verify fields with all variations in [1]

        @Assert: User is updated

        @Status: Manual
        """

    @stubbed()
    def test_negative_update_first_name(self):
        """@Test: Update My Account with invalid FirstName

        @Feature: My Account - Negative Update

        @Steps:
        1. Update Current user with all variations of FirstName in [2]

        @Assert: User is not updated. Appropriate error shown.

        @Status: Manual
        """

    @stubbed()
    def test_negative_update_surname(self):
        """@Test: Update My Account with invalid Surname

        @Feature: My Account - Negative Update

        @Steps:
        1. Update Current user with all variations of Surname in [2]

        @Assert: User is not updated. Appropriate error shown.

        @Status: Manual
        """

    @stubbed()
    def test_negative_update_email(self):
        """@Test: Update My Account with invalid Email Address

        @Feature: My Account - Negative Update

        @Steps:
        1. Update Current user with all variations of Email Address in [2]

        @Assert: User is not updated. Appropriate error shown.

        @Status: Manual
        """

    @stubbed()
    def test_negative_update_password_invalid(self):
        """@Test: Update My Account with invalid Password/Verify fields

        @Feature: My Account - Negative Update

        @Steps:
        1. Update Current user with all variations of Password/Verify fields
        in [2]

        @Assert: User is not updated. Appropriate error shown.

        @Status: Manual
        """

    @stubbed()
    def test_negative_update_password_mismatch(self):
        """@Test: Update My Account with non-matching values in Password and

        @Feature: My Account - Negative Update

        verify fields
        @Steps:
        1. Update Current user with non-matching values in Password and verify
        fields

        @Assert: User is not updated. Appropriate error shown.

        @Status: Manual
        """
