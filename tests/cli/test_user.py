# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for User CLI
"""

from robottelo.cli.user import User
from robottelo.cli.factory import make_user
from robottelo.common.helpers import generate_name
from robottelo.common.helpers import generate_string
from tests.cli.basecli import MetaCLI


class TestUser(MetaCLI):

    factory = make_user
    factory_obj = User
    search_key = 'id'

    POSITIVE_CREATE_DATA = (
        {'login': generate_string("latin1", 10).encode("utf-8")},
        {'login': generate_string("utf8", 10).encode("utf-8")},
        {'login': generate_string("alpha", 10)},
        {'login': generate_string("alphanumeric", 10)},
        {'login': generate_string("numeric", 10)},
        {'login': generate_string("html", 10)},
    )

    NEGATIVE_CREATE_DATA = (
        {'login': generate_string("latin1", 300).encode("utf-8")},
        {'login': " "},
        {'': generate_string("alpha", 10)},
        {generate_string("alphanumeric", 10): " "},
    )

    POSITIVE_UPDATE_DATA = (
        ({'login': generate_string("latin1", 10).encode("utf-8")},
         {'lastname': generate_string("latin1", 10).encode("utf-8")}),
        ({'login': generate_string("utf8", 10).encode("utf-8")},
         {'lastname': generate_string("utf8", 10).encode("utf-8")}),
        ({'login': generate_string("alpha", 10)},
         {'lastname': generate_string("alpha", 10)}),
        ({'login': generate_string("alphanumeric", 10)},
         {'lastname': generate_string("alphanumeric", 10)}),
        ({'login': generate_string("numeric", 10)},
         {'lastname': generate_string("numeric", 10)}),
        ({'login': generate_string("utf8", 10).encode("utf-8")},
         {'lastname': generate_string("html", 6)}),
    )

    NEGATIVE_UPDATE_DATA = (
        ({'login': generate_string("utf8", 10).encode("utf-8")},
         {'lastname': generate_string("utf8", 300).encode("utf-8")}),
        ({'login': generate_string("utf8", 10).encode("utf-8")},
         {'lastname': ""}),
    )

    POSITIVE_DELETE_DATA = (
        {'login': generate_string("latin1", 10).encode("utf-8")},
        {'login': generate_string("utf8", 10).encode("utf-8")},
        {'login': generate_string("alpha", 10)},
        {'login': generate_string("alphanumeric", 10)},
        {'login': generate_string("numeric", 10)},
    )

    NEGATIVE_DELETE_DATA = (
        {'id': generate_string("alpha", 10)},
        {'id': None},
        {'id': ""},
        {},
        {'id': -1},
    )

    def test_create_user_1(self):
        "Successfully creates a new user"

        password = generate_name(6)
        return_code = self.make_user({'password': password})
        self.assertEqual(return_code, 0)

    def test_delete_user_1(self):
        "Creates and immediately deletes user."

        password = generate_name(6)
        login = generate_name(6)
        self.make_user({'login': login, 'password': password})

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
        self.make_user({'login': login, 'email': email, 'password': password})
        self.assertFalse(User().exists(('login', login)))

    def test_create_user_latin1(self):
        "Create latin1 user"

        password = generate_string('alpha', 6)
        email_name = generate_string('alpha', 6)
        email = "%s@example.com" % email_name
        login = generate_string('latin1', 6).encode('utf-8')
        self.make_user({'login': login, 'email': email, 'password': password})
        self.assertFalse(User().exists(('login', login)))
