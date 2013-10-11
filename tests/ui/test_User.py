#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from baseui import BaseUI
from robottelo.lib.common.helpers import generate_name

class User(BaseUI):

    def users_page(self):
        self.login.login("admin", "admin")
        self.navigator.go_to_users()

    def test_create_user_1(self):
        "Successfully creates a new user"
        self.users_page()

        name = generate_name()
        email = "%s@example.com" % name
        password = generate_name()

        self.user.new_user(name, email, password, password)
        user = self.user.find_user(name)
        self.assertEqual(user.text, name)
