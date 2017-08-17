"""Unit tests for the ``users`` paths.

Each ``APITestCase`` subclass tests a single URL. A full list of URLs to be
tested can be found here: http://theforeman.org/api/apidoc/v2/users.html


@Requirement: User

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
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
from robottelo.decorators import tier1, upgrade
from robottelo.test import APITestCase


class UserTestCase(APITestCase):
    """Tests for the ``users`` path."""

    @tier1
    def test_positive_create_with_username(self):
        """Create User for all variations of Username

        @id: a9827cda-7f6d-4785-86ff-3b6969c9c00a

        @expectedresults: User is created
        """
        for username in valid_usernames_list():
            with self.subTest(username):
                user = entities.User(login=username).create()
                self.assertEqual(user.login, username)

    @tier1
    def test_positive_create_with_firstname(self):
        """Create User for all variations of First Name

        @id: 036bb958-227c-420c-8f2b-c607136f12e0

        @expectedresults: User is created
        """
        for firstname in generate_strings_list(
                exclude_types=['html'], max_length=50):
            with self.subTest(firstname):
                user = entities.User(firstname=firstname).create()
                self.assertEqual(user.firstname, firstname)

    @tier1
    def test_positive_create_with_lastname(self):
        """Create User for all variations of Last Name

        @id: 95d3b571-77e7-42a1-9c48-21f242e8cdc2

        @expectedresults: User is created
        """
        for lastname in generate_strings_list(
                exclude_types=['html'], max_length=50):
            with self.subTest(lastname):
                user = entities.User(lastname=lastname).create()
                self.assertEqual(user.lastname, lastname)

    @tier1
    def test_positive_create_with_email(self):
        """Create User for all variations of Email

        @id: e68caf51-44ba-4d32-b79b-9ab9b67b9590

        @expectedresults: User is created
        """
        for mail in valid_emails_list():
            with self.subTest(mail):
                user = entities.User(mail=mail).create()
                self.assertEqual(user.mail, mail)

    @tier1
    def test_positive_create_with_password(self):
        """Create User for all variations of Password

        @id: 53d0a419-0730-4f7d-9170-d855adfc5070

        @expectedresults: User is created
        """
        for password in generate_strings_list(
                exclude_types=['html'], max_length=50):
            with self.subTest(password):
                user = entities.User(password=password).create()
                self.assertIsNotNone(user)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create random users and then delete it.

        @id: df6059e7-85c5-42fa-99b5-b7f1ef809f52

        @expectedresults: The user cannot be fetched after deletion.
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

        @id: b5fedf65-37f5-43ca-806a-ac9a7979b19d

        @expectedresults: The user's ``admin`` attribute is updated.
        """
        for admin_enable in (True, False):
            with self.subTest(admin_enable):
                user = entities.User(admin=admin_enable).create()
                user.admin = not admin_enable
                self.assertEqual(user.update().admin, not admin_enable)

    @tier1
    def test_negative_create_with_invalid_email(self):
        """Create User with invalid Email Address

        @id: ebbd1f5f-e71f-41f4-a956-ce0071b0a21c

        @expectedresults: User is not created. Appropriate error shown.
        """
        for mail in invalid_emails_list():
            with self.subTest(mail):
                with self.assertRaises(HTTPError):
                    entities.User(mail=mail).create()

    @tier1
    def test_negative_create_with_invalid_username(self):
        """Create User with invalid Username

        @id: aaf157a9-0375-4405-ad87-b13970e0609b

        @expectedresults: User is not created. Appropriate error shown.
        """
        for invalid_name in invalid_usernames_list():
            with self.subTest(invalid_name):
                with self.assertRaises(HTTPError):
                    entities.User(login=invalid_name).create()

    @tier1
    def test_negative_create_with_invalid_firstname(self):
        """Create User with invalid Firstname

        @id: cb1ca8a9-38b1-4d58-ae32-915b47b91657

        @expectedresults: User is not created. Appropriate error shown.
        """
        for invalid_name in invalid_names_list():
            with self.subTest(invalid_name):
                with self.assertRaises(HTTPError):
                    entities.User(firstname=invalid_name).create()

    @tier1
    def test_negative_create_with_invalid_lastname(self):
        """Create User with invalid Lastname

        @id: 59546d26-2b6b-400b-990f-0b5d1c35004e

        @expectedresults: User is not created. Appropriate error shown.
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

        @id: 32daacf1-eed4-49b1-81e1-ab0a5b0113f2

        @expectedresults: A user is created with the given role(s) and the
        default 'Anonymous' role.

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
    @upgrade
    def test_positive_update(self):
        """Update an existing user and give it roles.

        @id: 7fdca879-d65f-44fa-b9f2-b6bb5df30c2d

        @expectedresults: The user has whatever roles are given, plus the
        'Anonymous' role.

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
