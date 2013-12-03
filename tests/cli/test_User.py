#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from basecli import BaseCLI
from lib.common.helpers import generate_name
from lib.common.helpers import generate_string


class User(BaseCLI):

    def _create_user(self, login=None, fname=None, lname=None,
                     email=None, admin=None, passwd1=None, auth_id=1):

        args = {
            'login': login or generate_name(6),
            'firstname': fname or generate_name(),
            'lastname': lname or generate_name(),
            'mail': email or "%s@example.com" % login,
            'admin': admin,
            'password': passwd1 or generate_name(),
            'auth-source-id': auth_id,
        }

        self.user.create(args)

        self.assertTrue(self.user.exists(args['login']))

    def test_create_user_1(self):
        "Successfully creates a new user"

        password = generate_name(6)
        self._create_user(None, None, password)

    def test_delete_user_1(self):
        "Creates and immediately deletes user."

        password = generate_name(6)
        login = generate_name(6)
        self._create_user(login=login, passwd1=password)

        user = self.user.exists(login)

        args = {
            'id': user['Id'],
        }

        self.user.delete(args)
        self.assertFalse(self.user.exists(login))

    def test_create_user_utf8(self):
        "Create utf8 user"

        password = generate_string('alpha', 6)
        email_name = generate_string('alpha', 6)
        email = "%s@example.com" % email_name
        login = generate_string('utf8', 6).encode('utf-8')
        self._create_user(login=login, email=email, passwd1=password)

    def test_create_user_latin1(self):
        "Create latin1 user"

        password = generate_string('alpha', 6)
        email_name = generate_string('alpha', 6)
        email = "%s@example.com" % email_name
        login = generate_string('latin1', 6).encode('utf-8')
        self._create_user(login=login, email=email, passwd1=password)
