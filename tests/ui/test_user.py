# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Users UI
"""

from robottelo.common.constants import NOT_IMPLEMENTED
from tests.ui.baseui import BaseUI


class User(BaseUI):
    """
    Implements Users tests in UI

    [1] Positive Name variations - Alpha, Numeric, Alphanumeric, Symbols,
    Latin1, Multibyte, Max length,  Min length, Max_db_size, html, css,
    javascript, url, shell commands, sql, spaces in name
    [2] Negative Name Variations -  Blank, Greater than Max Length,
    Lesser than Min Length, Greater than Max DB size
    """

    def test_positive_create_user_1(self):
        """
        @Feature: User - Positive Create
        @Test: Create User for all variations of Username
        @Steps:
        1. Create User for all valid Username variation in [1] using
        valid First Name, Surname, Email Address, Language, authorized by
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_2(self):
        """
        @Feature: User - Positive Create
        @Test: Create User for all variations of First Name
        @Steps:
        1. Create User for all valid First Name variation in [1] using
        valid Username, Surname, Email Address, Language, authorized by
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_3(self):
        """
        @Feature: User - Positive Create
        @Test: Create User for all variations of Surname
        @Steps:
        1. Create User for all valid Surname variation in [1] using
        valid Username, First Name, Email Address, Language, authorized by
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_4(self):
        """
        @Feature: User - Positive Create
        @Test: Create User for all variations of Email Address
        @Steps:
        1. Create User for all valid Email Address variation in [1] using
        valid Username, First Name, Surname, Language, authorized by
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_5(self):
        """
        @Feature: User - Positive Create
        @Test: Create User for all variations of Language
        @Steps:
        1. Create User for all valid Language variations using
        valid Username, First Name, Surname, Email Address, authorized by
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_6(self):
        """
        @Feature: User - Positive Create
        @Test: Create User by choosing Authorized by - INTERNAL
        @Steps:
        1. Create User by choosing Authorized by - INTERNAL using
        valid Password/Verify fields
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_7(self):
        """
        @Feature: User - Positive Create
        @Test: Create User for all variations of Password
        @Steps:
        1. Create User for all valid Password variation in [1] using valid
        Username, First Name, Surname, Email Address, Language, authorized by
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_8(self):
        """
        @Feature: User - Positive Create
        @Test: Create an Admin user
        @Assert: Admin User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_9(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with one role
        @Steps:
        1. Create User with one role assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_10(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with multiple roles
        @Steps:
        1. Create User with multiple roles assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_11(self):
        """
        @Feature: User - Positive Create
        @Test: Create User and assign all available roles to it
        @Steps:
        1. Create User with all available roles assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_12(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with one owned host
        @Steps:
        1. Create User with one owned host assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_13(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with mutiple owned hosts
        @Steps:
        1. Create User with multiple owned hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_14(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with all owned hosts
        @Steps:
        1. Create User with all owned hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_15(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with one Domain host
        @Steps:
        1. Create User with one Domain host assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_16(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with mutiple Domain hosts
        @Steps:
        1. Create User with multiple Domain hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_17(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with all Domain hosts
        @Steps:
        1. Create User with all Domain hosts assigned to it
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_18(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with one Compute Resource
        @Steps:
        1. Create User associated with one Compute Resource
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_19(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with mutiple Compute Resources
        @Steps:
        1. Create User associated with multiple Compute Resources
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_20(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with all Compute Resources
        @Steps:
        1. Create User associated with all Compute Resources
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_21(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with one Host group
        @Steps:
        1. Create User associated with one Host group
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_22(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with multiple Host groups
        @Steps:
        1. Create User associated with multiple Host groups
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_23(self):
        """
        @Feature: User - Positive Create
        @Test: Create User with all Host groups
        @Steps:
        1. Create User associated with all available Host groups
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_24(self):
        """
        @Feature: User - Positive Create
        @Test: Create User associated to one Org
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_25(self):
        """
        @Feature: User - Positive Create
        @Test: Create User associated to multiple Orgs
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)

    def test_positive_create_user_26(self):
        """
        @Feature: User - Positive Create
        @Test: Create User associated to all available Orgs
        @Assert: User is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)