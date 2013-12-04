#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from baseui import BaseUI
from lib.ui.locators import *
from lib.common.helpers import generate_name
from lib.common.helpers import generate_email_address

class User(BaseUI):

    def test_create_user(self):
        "Create a new User"
        name = generate_name(6)
        password = generate_name(8)
        email = generate_email_address()
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_users()
        self.user.create(name, email, password, password)
        self.assertIsNotNone(self.user.search(name)) #confirm the User appears in the UI

    def test_delete_user(self):
        "Create and Delete a User"
        name = generate_name(6)
        password = generate_name(8)
        email = generate_email_address()
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_users()
        self.user.create(name, email, password, password)
        self.assertIsNotNone(self.user.search(name)) #confirm the User appears in the UI
        self.user.delete(name, really=True)
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))

    def test_update_password(self):
        "Creates a User and updates the password"
        name = generate_name(6)
        password = generate_name(8)
        new_password = generate_name(8)
        email = generate_email_address()
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_users()
        self.user.create(name, email, password, password)
        self.assertIsNotNone(self.user.search(name)) #confirm the User appears in the UI
        self.user.update(name, password = new_password)
        self.login.logout()
        self.login.login(name, new_password)
        self.assertTrue(self.login.is_logged()) #confirm user can login with new password
