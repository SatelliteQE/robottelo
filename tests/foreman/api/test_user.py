"""Unit tests for the ``users`` paths.

Each ``APITestCase`` subclass tests a single URL. A full list of URLs to be
tested can be found here: http://theforeman.org/api/apidoc/v2/users.html

"""
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.datafactory import (
    generate_strings_list,
    valid_usernames_list,
    valid_emails_list,
    invalid_emails_list,
    invalid_usernames_list,
    invalid_names_list
)
from robottelo.decorators import tier1
from robottelo.test import APITestCase


class UserTestCase(APITestCase):
    """Tests for the ``users`` path."""

    @tier1
    def test_positive_create_with_username(self):
        """Create User for all variations of Username

        @Feature: User - Positive Create

        @Assert: User is created
        """
        for username in valid_usernames_list():
            with self.subTest(username):
                user = entities.User(login=username).create()
                self.assertEqual(user.login, username)

    @tier1
    def test_positive_create_with_firstname(self):
        """Create User for all variations of First Name

        @Feature: User - Positive Create

        @Assert: User is created
        """
        for firstname in generate_strings_list(
                exclude_types=['html'], max_length=50):
            with self.subTest(firstname):
                user = entities.User(firstname=firstname).create()
                self.assertEqual(user.firstname, firstname)

    @tier1
    def test_positive_create_with_lastname(self):
        """Create User for all variations of Last Name

        @Feature: User - Positive Create

        @Assert: User is created
        """
        for lastname in generate_strings_list(
                exclude_types=['html'], max_length=50):
            with self.subTest(lastname):
                user = entities.User(lastname=lastname).create()
                self.assertEqual(user.lastname, lastname)

    @tier1
    def test_positive_create_with_email(self):
        """Create User for all variations of Email

        @Feature: User - Positive Create

        @Assert: User is created
        """
        for mail in valid_emails_list():
            with self.subTest(mail):
                user = entities.User(mail=mail).create()
                self.assertEqual(user.mail, mail)

    @tier1
    def test_positive_create_with_password(self):
        """Create User for all variations of Password

        @Feature: User - Positive Create

        @Assert: User is created
        """
        for password in generate_strings_list(
                exclude_types=['html'], max_length=50):
            with self.subTest(password):
                user = entities.User(password=password).create()
                self.assertIsNotNone(user)

    @tier1
    def test_positive_delete(self):
        """Create random users and then delete it.

        @Assert: The user cannot be fetched after deletion.

        @Feature: User
        """
        for mail in valid_emails_list():
            with self.subTest(mail):
                user = entities.User(mail=mail).create()
                user.delete()
                with self.assertRaises(HTTPError):
                    user.read()

    @tier1
    def test_positive_update_admin(self):
        """Update a user and provide the ``admin`` attribute.

        @Assert: The user's ``admin`` attribute is updated.

        @Feature: User
        """
        for admin_enable in (True, False):
            with self.subTest(admin_enable):
                user = entities.User(admin=admin_enable).create()
                user.admin = not admin_enable
                self.assertEqual(user.update().admin, not admin_enable)

    @tier1
    def test_negative_create_with_invalid_email(self):
        """Create User with invalid Email Address

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.
        """
        for mail in invalid_emails_list():
            with self.subTest(mail):
                with self.assertRaises(HTTPError):
                    entities.User(mail=mail).create()

    @tier1
    def test_negative_create_with_invalid_username(self):
        """Create User with invalid Username

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.
        """
        for invalid_name in invalid_usernames_list():
            with self.subTest(invalid_name):
                with self.assertRaises(HTTPError):
                    entities.User(login=invalid_name).create()

    @tier1
    def test_negative_create_with_invalid_firstname(self):
        """Create User with invalid Firstname

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.
        """
        for invalid_name in invalid_names_list():
            with self.subTest(invalid_name):
                with self.assertRaises(HTTPError):
                    entities.User(firstname=invalid_name).create()

    @tier1
    def test_negative_create_with_invalid_lastname(self):
        """Create User with invalid Lastname

        @Feature: User - Negative Create

        @Assert: User is not created. Appropriate error shown.
        """
        for invalid_name in invalid_names_list():
            with self.subTest(invalid_name):
                with self.assertRaises(HTTPError):
                    entities.User(lastname=invalid_name).create()


class UserRoleTestCase(APITestCase):
    """Test associations between users and roles."""

    @classmethod
    def setUpClass(cls):
        """Create two roles and fetch the 'Anonymous' role."""
        super(UserRoleTestCase, cls).setUpClass()
        cls.roles = [entities.Role().create() for _ in range(2)]
        roles = entities.Role().search(query={'search': 'name="Anonymous"'})
        cls.anon_role = roles[0]

    @tier1
    def test_positive_create_with_role(self):
        """Create a user with the ``role`` attribute.

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

    @tier1
    def test_positive_update(self):
        """Update an existing user and give it roles.

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
