# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Users CLI
"""

from robottelo.common.constants import NOT_IMPLEMENTED
from tests.foreman.cli.basecli import CLITestCase
import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest


class MyAccount(CLITestCase):
    """
    Implements Users tests in CLI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name
    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size
    """

    def test_positive_update_my_account_1(self):
        """
        @Feature: My Account - Positive Update
        @Test: Update Firstname in My Account
        @Steps:
        1. Update current User with all variations of Firstname in [1]
        @Assert: Current User is updated
        @Status: Manual
        """
        unittest.skip(NOT_IMPLEMENTED)

    def test_positive_update_my_account_2(self):
        """
        @Feature: My Account - Positive Update
        @Test: Update Surname in My Account
        @Steps:
        1. Update current User with all variations of Surname in [1]
        @Assert: Current User is updated
        @Status: Manual
        """
        unittest.skip(NOT_IMPLEMENTED)

    def test_positive_update_my_account_3(self):
        """
        @Feature: My Account - Positive Update
        @Test: Update Email Address in My Account
        @Steps:
        1. Update current User with all variations of Email Address in [1]
        @Assert: Current User is updated
        @Status: Manual
        """
        unittest.skip(NOT_IMPLEMENTED)

    def test_positive_update_my_account_4(self):
        """
        @Feature: My Account - Positive Update
        @Test: Update Language in My Account
        @Steps:
        1. Update current User with all different Language options
        @Assert: Current User is updated
        @Status: Manual
        """
        unittest.skip(NOT_IMPLEMENTED)

    def test_positive_update_my_account_5(self):
        """
        @Feature: My Account - Positive Update
        @Test: Update Password/Verify fields in My Account
        @Steps:
        1. Update Password/Verify fields with all variations in [1]
        @Assert: User is updated
        @Status: Manual
        """
        unittest.skip(NOT_IMPLEMENTED)

    def test_negative_update_my_account_1(self):
        """
        @Feature: My Account - Negative Update
        @Test: Update My Account with invalid FirstName
        @Steps:
        1. Update Current user with all variations of FirstName in [2]
        @Assert: User is not updated. Appropriate error shown.
        @Status: Manual
        """
        unittest.skip(NOT_IMPLEMENTED)

    def test_negative_update_my_account_2(self):
        """
        @Feature: My Account - Negative Update
        @Test: Update My Account with invalid Surname
        @Steps:
        1. Update Current user with all variations of Surname in [2]
        @Assert: User is not updated. Appropriate error shown.
        @Status: Manual
        """
        unittest.skip(NOT_IMPLEMENTED)

    def test_negative_update_my_account_3(self):
        """
        @Feature: My Account - Negative Update
        @Test: Update My Account with invalid Email Address
        @Steps:
        1. Update Current user with all variations of Email Address in [2]
        @Assert: User is not updated. Appropriate error shown.
        @Status: Manual
        """
        unittest.skip(NOT_IMPLEMENTED)

    def test_negative_update_my_account_4(self):
        """
        @Feature: My Account - Negative Update
        @Test: Update My Account with invalid Password/Verify fields
        @Steps:
        1. Update Current user with all variations of Password/Verify fields
        in [2]
        @Assert: User is not updated. Appropriate error shown.
        @Status: Manual
        """
        unittest.skip(NOT_IMPLEMENTED)

    def test_negative_update_my_account_5(self):
        """
        @Feature: My Account - Negative Update
        @Test: Update My Account with non-matching values in Password and
        verify fields
        @Steps:
        1. Update Current user with non-matching values in Password and verify
        fields
        @Assert: User is not updated. Appropriate error shown.
        @Status: Manual
        """
        unittest.skip(NOT_IMPLEMENTED)

    def test_negative_update_my_account_6(self):
        """
        @Feature: My Account - Negative Update
        @Test: [UI ONLY] Attempt to update all info in My Accounts page and
        Cancel
        @Steps:
        1. Update Current user with valid Firstname, Surname, Email Address,
        Language, Password/Verify fields
        2. Click Cancel
        @Assert: User is not updated.
        @Status: Manual
        """
        unittest.skip(NOT_IMPLEMENTED)
