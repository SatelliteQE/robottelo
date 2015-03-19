"""Unit tests for the ``users`` paths.

Each ``APITestCase`` subclass tests a single URL. A full list of URLs to be
tested can be found here: http://theforeman.org/api/apidoc/v2/users.html

"""
import ddt
from fauxfactory import gen_string
from random import randint
from requests.exceptions import HTTPError
from robottelo import entities
from robottelo.common import decorators
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


def _user_attrs():
    """Return an iterable of dicts. Each dict contains user attributes."""
    return (
        {u'admin': False},
        {u'admin': True},
        {u'firstname': gen_string('alphanumeric', randint(1, 50))},
        {u'firstname': gen_string('alpha', randint(1, 50))},
        {u'firstname': gen_string('cjk', randint(1, 50))},
        {u'firstname': gen_string('latin1', randint(1, 50))},
        {u'firstname': gen_string('numeric', randint(1, 50))},
        {u'firstname': gen_string('utf8', randint(1, 16))},
        {u'lastname': gen_string('alphanumeric', randint(1, 50))},
        {u'lastname': gen_string('alpha', randint(1, 50))},
        {u'lastname': gen_string('cjk', randint(1, 50))},
        {u'lastname': gen_string('latin1', randint(1, 50))},
        {u'lastname': gen_string('numeric', randint(1, 50))},
        {u'lastname': gen_string('utf8', randint(1, 16))},
        {u'login': gen_string('alphanumeric', randint(1, 100))},
        {u'login': gen_string('alpha', randint(1, 100))},
        {u'login': gen_string('cjk', randint(1, 100))},
        {u'login': gen_string('latin1', randint(1, 100))},
        {u'login': gen_string('numeric', randint(1, 100))},
        {u'login': gen_string('utf8', randint(1, 33))},
    )


@ddt.ddt
class UsersTestCase(APITestCase):
    """Tests for the ``users`` path."""

    @decorators.data(*_user_attrs())
    def test_create(self, attrs):
        """@Test: Create a user with attributes ``attrs`` and delete it.

        @Assert: The created user has the given attributes.

        @Feature: User

        """
        # Create a user and validate its attributes.
        user_id = entities.User(**attrs).create()['id']
        real_attrs = entities.User(id=user_id).read_json()
        for name, value in attrs.items():
            self.assertIn(name, real_attrs.keys())
            self.assertEqual(value, real_attrs[name])

    @decorators.data(*_user_attrs())
    def test_delete(self, attrs):
        """@Test: Create a user with attributes ``attrs`` and delete it.

        @Assert: The user cannot be fetched after deletion.

        @Feature: User

        """
        # Create a user and delete it immediately afterward.
        user_id = entities.User(**attrs).create()['id']
        entities.User(id=user_id).delete()
        with self.assertRaises(HTTPError):
            entities.User(id=user_id).read_json()
