#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from lib.common.helpers import generate_name


class User(BaseCLI):

    def _create_user(self, login=None, fname=None, lname=None,
                     email=None, admin=None, passwd1=None):

        login = login or generate_name(6)
        fname = fname or generate_name()
        lname = lname or generate_name()
        email = email or "%s@example.com" % login
        admin = admin
        passwd1 = passwd1 or generate_name()

        self.user.create(
            login, fname, lname, email, admin, passwd1)

        self.assertTrue(self.user.exists(login))

    def test_create_user_1(self):
        "Successfully creates a new user"

        password = generate_name(6)
        self._create_user(None, None, password)

    def test_delete_user_1(self):
        "Creates and immediately deletes user."

        password = generate_name(6)
        login = generate_name(6)
        self._create_user(login=login, passwd1=password)

        user = self.user.user(login)
        self.user.delete(user['Id'])
        self.assertFalse(self.user.exists(login))
