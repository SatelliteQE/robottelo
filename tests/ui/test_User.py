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
        user = self.user.find_user(name)
        self.assertEqual(user.text, name)

        return user

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
        self.assertTrue(self.browser.is_element_present_by_css(locators["notif.error"]))

    def test_edit_user_1(self):
        "Create then edit new user's password"
        self.users_page()

        password = generate_name(6)
        self._create_user(None, None, password, password)

        new_password = generate_name()
        self.browser.find_by_id(locators["users.password1"]).fill(new_password)
        self.browser.find_by_id(locators["users.password2"]).fill(new_password)
        self.browser.find_by_id(locators["users.save"]).click()
        self.assertTrue(self.browser.is_element_present_by_css(locators["notif.success"]))

    def test_edit_user_2(self):
        "Create then edit new user's locale"
        self.users_page()

        password = generate_name(6)
        self._create_user(None, None, password, password)
        # Change locale to pt_BR (default)
        self.user.update_locale()
        self.assertTrue(self.browser.is_element_present_by_css(locators["notif.success"]))
        # Change locale to ja
        self.user.update_locale('ja')
        self.assertTrue(self.browser.is_element_present_by_css(locators["notif.success"]))

    def test_delete_user_1(self):
        "Creates and immediately deletes a user"
        self.users_page()

        name = generate_name()
        password = generate_name(6)
        self._create_user(name, None, password, password)

        # Attempt to remove a user but change mind
        self.user.remove_user(name, False)
        user = self.user.find_user(name)
        self.assertEqual(user.text, name)

        # Now delete it for real
        # Revisit Users page
        self.navigator.go_to_users()
        self.user.remove_user(name, True)
        self.navigator.go_to_users()
        user = self.user.find_user(name)
        self.assertEqual(user, [])

