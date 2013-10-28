#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from baseui import BaseUI
from robottelo.lib.common.helpers import generate_name
from robottelo.lib.ui.locators import *

class User(BaseUI):

    def users_page(self):
        self.login.login("admin", "admin")
        self.navigator.go_to_users()

    def _create_user(self, name=None, email=None, passwd1=None, passwd2=None):

        name = name or generate_name()
        email = email or "%s@example.com" % name

        self.user.new_user(name, email, passwd1, passwd2)
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))
        self.user.find_element(locators["notif.close"]).click()

    def test_create_user_1(self):
        "Successfully creates a new user"
        self.users_page()

        password = generate_name(6)
        self._create_user(None, None, password, password)

    def test_create_user_2(self):
        "Attempt to create the same user twice"
        self.users_page()

        name = generate_name()
        email = "%s@example.com" % name
        password = generate_name(6)
        self._create_user(name, email, password, password)

        # Revisit Users page
        self.navigator.go_to_users()
        self.user.new_user(name, email, password, password)
        self.assertTrue(self.user.wait_until_element(locators["notif.error"]))

    def test_edit_user_1(self):
        "Create then edit new user's password"
        self.users_page()

        password = generate_name(7)
        self._create_user(None, None, password, password)

        # Wait until the edit form is visible
        self.user.wait_until_element(locators["users.password1"])
        new_password = generate_name()
        self.user.find_element(locators["users.password1"]).send_keys(new_password)
        self.user.find_element(locators["users.password2"]).send_keys(new_password)
        self.user.find_element(locators["users.save_password"]).click()
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))

    def test_edit_user_2(self):
        "Create then edit new user's locale"
        self.users_page()

        password = generate_name(6)
        self._create_user(None, None, password, password)

        # Wait until the edit form is visible
        self.user.wait_until_element(locators["users.password1"])
        # Change locale to pt_BR (default)
        self.user.update_locale()
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))

    def test_delete_user_1(self):
        "Creates and immediately deletes a user"
        self.users_page()

        name = generate_name()
        password = generate_name(6)
        self._create_user(name, None, password, password)

        # Attempt to remove a user but change mind
        self.user.remove_user(name, False)
        # Revisit Users page
        self.navigator.go_to_users()
        user = self.user.find_user(name)
        self.assertIsNotNone(user)
        self.assertEqual(user.text, name)

        # Now delete it for real
        self.user.remove_user(name, True)
        # Revisit Users page
        self.navigator.go_to_users()
        user = self.user.find_user(name)
        self.assertIsNone(user)

