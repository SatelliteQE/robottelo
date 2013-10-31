#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from robottelo.lib.common.helpers import generate_name

class User(BaseCLI):

    def _create_user(self, name=None, email=None, passwd1=None):

        name = name or generate_name()
        email = email or "%s@example.com" % name

        self.user.create(name, passwd1, email)

        user = self.user.info(name)
        self.assertEqual(name, user['username'])

    def test_create_user_1(self):
        "Successfully creates a new user"

        password = generate_name(6)
        self._create_user(None, None, password)

    def test_delete_user_1(self):
        "Creates and immediately deletes user."

        password = generate_name(6)
        name = generate_name()
        self._create_user(name, None, password)

        self.user.delete(name)
        self.assertEqual({}, self.user.info(name))
