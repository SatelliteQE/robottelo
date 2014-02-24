# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Login UI
"""

from tests.ui.baseui import BaseUI


class Login(BaseUI):
    """
    Implements the login tests rom UI
    """

    def test_successful_login(self):
        """
        @Feature: Login - Positive
        @Test: Login as an admin user
        @Assert: Successfully logged in as an admin user
        """
        self.login.login(self.katello_user, self.katello_passwd)
        self.assertTrue(self.login.is_logged())

    def test_failed_login_1(self):
        """
        @Feature: Login - Negative
        @Test: Login as an admin user with an invalid credentials
        @Assert: Fails to login
        """
        self.login.login("admin", "")
        self.assertFalse(self.login.is_logged())

    def test_failed_login_2(self):
        """
        @Feature: Login - Negative
        @Test: Login as an admin user without entering credentails
        @Assert: Fails to login
        """
        self.login.login("", "")
        self.assertFalse(self.login.is_logged())
