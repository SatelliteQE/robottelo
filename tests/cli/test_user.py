# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for User CLI
"""

from basecli import BaseCLI
from robottelo.cli.user import User
from robottelo.common.helpers import generate_name
from robottelo.common.helpers import generate_string


class TestUser(BaseCLI):

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

        ret = User().create(args)
        self.assertTrue(ret.return_code == 0, "User was not created")
        self.assertTrue(User().exists(('login', args['login'])))

        return ret.return_code

    def test_create_user_1(self):
        "Successfully creates a new user"

        password = generate_name(6)
        return_code = self._create_user(None, None, password)
        self.assertEqual(return_code, 0)

    def test_delete_user_1(self):
        "Creates and immediately deletes user."

        password = generate_name(6)
        login = generate_name(6)
        self._create_user(login=login, passwd1=password)

        user = User().exists(('login', login))

        args = {
            'id': user['id'],
        }

        ret = User().delete(args)
        self.assertFalse(User().exists(('login', login)))
        self.assertEqual(ret.return_code, 0)

    def test_create_user_utf8(self):
        "Create utf8 user"

        password = generate_string('alpha', 6)
        email_name = generate_string('alpha', 6)
        email = "%s@example.com" % email_name
        login = generate_string('utf8', 6).encode('utf-8')
        return_code = self._create_user(
            login=login, email=email, passwd1=password)
        self.assertEqual(return_code, 0)

    def test_create_user_latin1(self):
        "Create latin1 user"

        password = generate_string('alpha', 6)
        email_name = generate_string('alpha', 6)
        email = "%s@example.com" % email_name
        login = generate_string('latin1', 6).encode('utf-8')
        return_code = self._create_user(
            login=login, email=email, passwd1=password)
        self.assertEqual(return_code, 0)
