"""Unit tests for the ``users`` paths.

Each ``APITestCase`` subclass tests a single URL. A full list of URLs to be
tested can be found here: http://theforeman.org/api/apidoc/v2/users.html

"""
import ddt

from fauxfactory import gen_string
from nailgun import entities
from random import randint
from requests.exceptions import HTTPError
from robottelo import decorators
from robottelo.test import APITestCase


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
        user = entities.User(**attrs).create()
        for name, value in attrs.items():
            self.assertEqual(getattr(user, name), value)

    @decorators.data(*_user_attrs())
    def test_delete(self, attrs):
        """@Test: Create a user with attributes ``attrs`` and delete it.

        @Assert: The user cannot be fetched after deletion.

        @Feature: User

        """
        user = entities.User(**attrs).create()
        user.delete()
        with self.assertRaises(HTTPError):
            user.read()

    @decorators.data(True, False)
    def test_update_admin(self, admin):
        """@Test: Update a user and provide the ``admin`` attribute.

        @Assert: The user's ``admin`` attribute is updated.

        @Feature: User

        """
        user = entities.User(admin=admin).create()
        user.admin = not admin
        self.assertEqual(user.update().admin, not admin)


class UserRoleTestCase(APITestCase):
    """Test associations between users and roles."""

    @classmethod
    def setUpClass(cls):
        """Create two roles and fetch the 'Anonymous' role."""
        cls.roles = [entities.Role().create() for _ in range(2)]
        roles = entities.Role().search(query={'search': 'name="Anonymous"'})
        cls.anon_role = roles[0]

    def test_create_with_role(self):
        """@Test: Create a user with the ``role`` attribute.

        @Assert: A user is created with the given role(s) and the default
        'Anonymous' role.

        @Feature: User

        This test targets BZ 1216239.

        """
        for i in range(2):
            chosen_roles = self.roles[0:i]
            user = entities.User(role=chosen_roles).create()
            self.assertEqual(len(user.role), i + 1)
            self.assertEqual(
                set([role.id for role in user.role]),
                # pylint:disable=no-member
                set([role.id for role in chosen_roles] + [self.anon_role.id]),
            )

    def test_update_with_role(self):
        """@Test: Update an existing user and give it roles.

        @Assert: The user has whatever roles are given, plus the 'Anonymous'
        role.

        @Feature: User

        This test targets BZ 1216239.

        """
        user = entities.User().create()
        self.assertEqual(len(user.role), 1)  # the 'Anonymous' role
        self.assertEqual(
            user.role[0].id,
            self.anon_role.id  # pylint:disable=no-member
        )
        for i in range(2):
            chosen_roles = self.roles[0:i]
            user.role = chosen_roles
            user = user.update(['role'])
            self.assertEqual(
                set([role.id for role in user.role]),
                # pylint:disable=no-member
                set([role.id for role in chosen_roles] + [self.anon_role.id]),
            )
