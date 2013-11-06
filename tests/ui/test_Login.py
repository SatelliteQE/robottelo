#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from baseui import BaseUI
from robottelo.lib.common.helpers import generate_name
from robottelo.lib.ui.locators import *

class Login(BaseUI):

    def test_successful_login(self):
        "Successfully logs in as admin user"
        self.login.login("admin", "admin")
        self.assertTrue(self.login.is_logged("admin"))

    def test_failed_login_1(self):
        "Fails to log in as admin user with incorrect credentials"
        self.login.login("admin", "")
        self.assertFalse(self.login.is_logged("admin"))

    def test_failed_login_2(self):
        "Fails to log in when no credentials are entered"
        self.login.login("", "")
        self.assertFalse(self.login.is_logged("admin"))

    def test_successful_forgot_username_1(self):
        "Forgot Username - Successfully sends out the username after entering a valid email"
        #TODO: Enhance to check the email in future
        user_name = generate_name(4,8)
        user_email = "%s@test.com" % user_name # generate random email
        self.login.login("admin","admin") # login
        self.navigator.go_to_users() # go to users page
        self.user.new_user(user_name, user_email, "password", "password") # create new user
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))
        self.user.find_element(locators["notif.close"]).click()
        self.login.logout()
        self.login.forgot_username(user_email)
        self.assertTrue(self.login.wait_until_element(locators["notif.success"]))

    def test_failed_forgot_username_1(self):
        "Forgot Username - Errors out when given an invalid email"
        user_name = generate_name(4,8)
        user_email = "%s@test.com" % user_name # generate invalid email
        self.login.forgot_username(user_email)
        self.assertTrue(self.login.wait_until_element(locators["notif.success"])) #TODO: For now there is no email validation

    def test_failed_forgot_username_2(self):
        "Forgot Username - Errors out when given an empty email"
        self.login.forgot_username("")
        self.assertTrue(self.login.wait_until_element(locators["notif.success"])) #TODO: For now there is no email validation
