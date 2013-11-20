#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from baseui import BaseUI
from lib.common.helpers import generate_name
from lib.common.decorators import runIf
from lib.ui.locators import *


class Login(BaseUI):

    def test_successful_login(self):
        "Successfully logs in as admin user"
        self.login.login(self.katello_user, self.katello_passwd)
        self.assertTrue(self.login.is_logged(self.katello_user))

    def test_failed_login_1(self):
        "Fails to log in as admin user with incorrect credentials"
        self.login.login("admin", "")
        self.assertFalse(self.login.is_logged("admin"))

    def test_failed_login_2(self):
        "Fails to log in when no credentials are entered"
        self.login.login("", "")
        self.assertFalse(self.login.is_logged("admin"))

    @runIf('sam')
    def test_successful_forgot_username_1(self):
        """
        Forgot Username - Successfully sends out the username after
        entering a valid email
        """

        #TODO: Enhance to check the email in future
        user_name = generate_name(4, 8)
        user_email = "%s@test.com" % user_name  # generate random email
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_users()  # go to users page
        self.user.new_user(user_name, user_email, "password", "password")
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))
        self.user.find_element(locators["notif.close"]).click()
        self.login.logout()
        self.login.forgot_username(user_email)
        self.assertTrue(self.login.wait_until_element(locators["notif.success"]))

    @runIf('sam')
    def test_failed_forgot_username_1(self):
        "Forgot Username - Errors out when given an invalid email"
        user_name = generate_name(4, 8)
        user_email = "%s@test.com" % user_name  # generate invalid email
        self.login.forgot_username(user_email)
        #TODO: For now there is no email validation
        self.assertTrue(self.login.wait_until_element(locators["notif.success"]))

    @runIf('sam')
    def test_failed_forgot_username_2(self):
        "Forgot Username - Errors out when given an empty email"
        self.login.forgot_username("")
        #TODO: For now there is no email validation
        self.assertTrue(self.login.wait_until_element(locators["notif.success"]))

    @runIf('sam')
    def test_successful_forgot_password_1(self):
        """
        Forgot Password - Successfully sends out the username after
        entering a valid email
        """
        #TODO: Enhance to check the email in future
        user_name = generate_name(4, 8)
        user_email = "%s@test.com" % user_name  # generate random email
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_users()  # go to users page
        self.user.new_user(user_name, user_email, "password", "password")
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))
        self.user.find_element(locators["notif.close"]).click()
        self.login.logout()
        self.login.forgot_password(user_name, user_email)
        self.assertTrue(self.login.wait_until_element(locators["notif.success"]))

    @runIf('sam')
    def test_failed_forgot_password_1(self):
        "Forgot Password - Errors out when given an invalid username and invalid email"
        user_name = generate_name(4, 8)
        user_email = "%s@test.com" % user_name  # generate invalid email
        self.login.forgot_password(user_name, user_email)
        #TODO: For now there is no username/email validation
        self.assertTrue(self.login.wait_until_element(locators["notif.success"]))

    @runIf('sam')
    def test_failed_forgot_password_2(self):
        "Forgot Password - Errors out when given an empty email and empty password"
        self.login.forgot_password("", "")
        #TODO: For now there is no username/email validation
        self.assertTrue(self.login.wait_until_element(locators["notif.success"]))

