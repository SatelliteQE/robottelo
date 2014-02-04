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
        1. Create User for all valid Username variation
        in [1] using valid First Name, Surname, Email Address, Language, authorized by
        @Assert: Activation key is created
        @Status: Manual
        """
        self.fail(NOT_IMPLEMENTED)
