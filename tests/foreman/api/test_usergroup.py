"""Unit tests for the ``usergroups`` paths.

Each ``APITestCase`` subclass tests a single URL. A full list of URLs to be
tested can be found here:
http://theforeman.org/api/1.11/apidoc/v2/usergroups.html

:Requirement: Usergroup

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import randint

from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_usernames_list
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import APITestCase


class UserGroupTestCase(APITestCase):
    """Tests for the ``usergroups`` path."""

    @tier1
    def test_positive_create_with_name(self):
        """Create new user group using different valid names

        :id: 3a2255d9-f48d-4f22-a4b9-132361bd9224

        :expectedresults: User group is created successfully.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                user_group = entities.UserGroup(name=name).create()
                self.assertEqual(user_group.name, name)

    @tier1
    def test_positive_create_with_user(self):
        """Create new user group using valid user attached to that group.

        :id: ab127e09-31d2-4c5b-ae6c-726e4b11a21e

        :expectedresults: User group is created successfully.

        :CaseImportance: Critical
        """
        for login in valid_usernames_list():
            with self.subTest(login):
                user = entities.User(login=login).create()
                user_group = entities.UserGroup(user=[user]).create()
                self.assertEqual(len(user_group.user), 1)
                self.assertEqual(user_group.user[0].read().login, login)

    @tier1
    def test_positive_create_with_users(self):
        """Create new user group using multiple users attached to that group.

        :id: b8dbbacd-b5cb-49b1-985d-96df21440652

        :expectedresults: User group is created successfully and contains all
            expected users.

        :CaseImportance: Critical
        """
        users = [entities.User().create() for _ in range(randint(3, 5))]
        user_group = entities.UserGroup(user=users).create()
        self.assertEqual(
            sorted([user.login for user in users]),
            sorted([user.read().login for user in user_group.user])
        )

    @tier1
    def test_positive_create_with_role(self):
        """Create new user group using valid role attached to that group.

        :id: c4fac71a-9dda-4e5f-a5df-be362d3cbd52

        :expectedresults: User group is created successfully.

        :CaseImportance: Critical
        """
        for role_name in valid_data_list():
            with self.subTest(role_name):
                role = entities.Role(name=role_name).create()
                user_group = entities.UserGroup(role=[role]).create()
                self.assertEqual(len(user_group.role), 1)
                self.assertEqual(user_group.role[0].read().name, role_name)

    @tier1
    def test_positive_create_with_roles(self):
        """Create new user group using multiple roles attached to that group.

        :id: 5838fcfd-e256-49cf-aef8-b2bf215b3586

        :expectedresults: User group is created successfully and contains all
            expected roles

        :CaseImportance: Critical
        """
        roles = [entities.Role().create() for _ in range(randint(3, 5))]
        user_group = entities.UserGroup(role=roles).create()
        self.assertEqual(
            sorted([role.name for role in roles]),
            sorted([role.read().name for role in user_group.role])
        )

    @tier1
    def test_positive_create_with_usergroup(self):
        """Create new user group using another user group attached to the
        initial group.

        :id: 2a3f7b1a-7411-4c12-abaf-9a3ca1dfae31

        :expectedresults: User group is created successfully.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                sub_user_group = entities.UserGroup(name=name).create()
                user_group = entities.UserGroup(
                    usergroup=[sub_user_group],
                ).create()
                self.assertEqual(len(user_group.usergroup), 1)
                self.assertEqual(user_group.usergroup[0].read().name, name)

    @tier2
    def test_positive_create_with_usergroups(self):
        """Create new user group using multiple user groups attached to that
        initial group.

        :id: 9ba71288-af8b-4957-8413-442a47057634

        :expectedresults: User group is created successfully and contains all
            expected user groups

        :CaseLevel: Integration
        """
        sub_user_groups = [
            entities.UserGroup().create() for _ in range(randint(3, 5))]
        user_group = entities.UserGroup(usergroup=sub_user_groups).create()
        self.assertEqual(
            sorted([usergroup.name for usergroup in sub_user_groups]),
            sorted(
                [usergroup.read().name for usergroup in user_group.usergroup])
        )

    @tier1
    def test_negative_create_with_name(self):
        """Attempt to create user group with invalid name.

        :id: 1a3384dc-5d52-442c-87c8-e38048a61dfa

        :expectedresults: User group is not created.

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.UserGroup(name=name).create()

    @tier1
    def test_negative_create_with_same_name(self):
        """Attempt to create user group with a name of already existent entity.

        :id: aba0925a-d5ec-4e90-86c6-404b9b6f0179

        :expectedresults: User group is not created.

        :CaseImportance: Critical
        """
        user_group = entities.UserGroup().create()
        with self.assertRaises(HTTPError):
            entities.UserGroup(name=user_group.name).create()

    @tier1
    def test_positive_update(self):
        """Update existing user group with different valid names.

        :id: b4f0a19b-9059-4e8b-b245-5a30ec06f9f3

        :expectedresults: User group is updated successfully.

        :CaseImportance: Critical
        """
        user_group = entities.UserGroup().create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                user_group.name = new_name
                user_group = user_group.update(['name'])
                self.assertEqual(new_name, user_group.name)

    @tier1
    def test_positive_update_with_new_user(self):
        """Add new user to user group

        :id: e11b57c3-5f86-4963-9cc6-e10e2f02468b

        :expectedresults: User is added to user group successfully.

        :CaseImportance: Critical
        """
        user = entities.User().create()
        user_group = entities.UserGroup().create()
        user_group.user = [user]
        user_group = user_group.update(['user'])
        self.assertEqual(user.login, user_group.user[0].read().login)

    @tier2
    def test_positive_update_with_existing_user(self):
        """Update user that assigned to user group with another one

        :id: 71b78f64-867d-4bf5-9b1e-02698a17fb38

        :expectedresults: User group is updated successfully.

        :CaseLevel: Integration
        """
        users = [entities.User().create() for _ in range(2)]
        user_group = entities.UserGroup(user=[users[0]]).create()
        user_group.user[0] = users[1]
        user_group = user_group.update(['user'])
        self.assertEqual(users[1].login, user_group.user[0].read().login)

    @tier1
    def test_positive_update_with_new_role(self):
        """Add new role to user group

        :id: 8e0872c1-ae88-4971-a6fc-cd60127d6663

        :expectedresults: Role is added to user group successfully.

        :CaseImportance: Critical
        """
        new_role = entities.Role().create()
        user_group = entities.UserGroup().create()
        user_group.role = [new_role]
        user_group = user_group.update(['role'])
        self.assertEqual(new_role.name, user_group.role[0].read().name)

    @tier1
    @upgrade
    def test_positive_update_with_new_usergroup(self):
        """Add new user group to existing one

        :id: 3cb29d07-5789-4f94-9fd9-a7e494b3c110

        :expectedresults: User group is added to existing group successfully.

        :CaseImportance: Critical
        """
        new_usergroup = entities.UserGroup().create()
        user_group = entities.UserGroup().create()
        user_group.usergroup = [new_usergroup]
        user_group = user_group.update(['usergroup'])
        self.assertEqual(
            new_usergroup.name, user_group.usergroup[0].read().name)

    @tier1
    def test_negative_update(self):
        """Attempt to update existing user group using different invalid names.

        :id: 03772bd0-0d52-498d-8259-5c8a87e08344

        :expectedresults: User group is not updated.

        :CaseImportance: Critical
        """
        user_group = entities.UserGroup().create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                user_group.name = new_name
                with self.assertRaises(HTTPError):
                    user_group.update(['name'])
                self.assertNotEqual(user_group.read().name, new_name)

    @tier1
    def test_negative_update_with_same_name(self):
        """Attempt to update user group with a name of already existent entity.

        :id: 14888998-9282-4d81-9e99-234d19706783

        :expectedresults: User group is not updated.

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        entities.UserGroup(name=name).create()
        new_user_group = entities.UserGroup().create()
        new_user_group.name = name
        with self.assertRaises(HTTPError):
            new_user_group.update(['name'])
        self.assertNotEqual(new_user_group.read().name, name)

    @tier1
    def test_positive_delete(self):
        """Create user group with valid name and then delete it

        :id: c5cfcc4a-9177-47bb-8f19-7a8930eb7ca3

        :expectedresults: User group is deleted successfully

        :CaseImportance: Critical
        """
        user_group = entities.UserGroup().create()
        user_group.delete()
        with self.assertRaises(HTTPError):
            user_group.read()
