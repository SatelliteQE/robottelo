# -*- encoding: utf-8 -*-
"""Test class for Login UI"""

from robottelo.test import UITestCase


class Login(UITestCase):
    """Implements the login tests rom UI"""

    def test_successful_login(self):
        """@Test: Login as an admin user

        @Feature: Login - Positive

        @Assert: Successfully logged in as an admin user

        """
        self.login.login(self.katello_user, self.katello_passwd)
        self.assertTrue(self.login.is_logged())

    def test_failed_login_1(self):
        """@Test: Login as an admin user with an invalid credentials

        @Feature: Login - Negative

        @Assert: Fails to login

        """
        self.login.login("admin", "")
        self.assertFalse(self.login.is_logged())

    def test_failed_login_2(self):
        """@Test: Login as an admin user without entering credentails

        @Feature: Login - Negative

        @Assert: Fails to login

        """
        self.login.login("", "")
        self.assertFalse(self.login.is_logged())
