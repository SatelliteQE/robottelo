# -*- encoding: utf-8 -*-
"""Test class for User Group CLI"""

from random import randint
from robottelo.cli.usergroup import UserGroup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_role,
    make_user,
    make_usergroup,
)
from robottelo.datafactory import (
    invalid_values_list,
    valid_data_list,
    valid_usernames_list,
)
from robottelo.decorators import tier1, tier2
from robottelo.test import CLITestCase


class UserGroupTestCase(CLITestCase):
    """User group CLI related tests."""

    @tier1
    def test_positive_create_with_name(self):
        """Create new user group using different valid names

        @Feature: Usergroup

        @Assert: User group is created successfully.
        """
        for name in valid_data_list():
            with self.subTest(name):
                user_group = make_usergroup({'name': name})
                self.assertEqual(user_group['name'], name)

    @tier1
    def test_positive_create_with_user_name(self):
        """Create new user group using valid user attached to that group. Use
        user name as a parameter

        @Feature: Usergroup

        @Assert: User group is created successfully.
        """
        for login in valid_usernames_list():
            with self.subTest(login):
                user = make_user({'login': login})
                user_group = make_usergroup({'users': user['login']})
                self.assertEqual(len(user_group['users']), 1)
                self.assertEqual(user_group['users'][0], login)

    @tier1
    def test_positive_create_with_user_id(self):
        """Create new user group using valid user attached to that group. Use
        user id as a parameter

        @Feature: Usergroup

        @Assert: User group is created successfully.
        """
        user = make_user()
        user_group = make_usergroup({'user-ids': user['id']})
        self.assertEqual(user_group['users'][0], user['login'])

    @tier1
    def test_positive_create_with_users(self):
        """Create new user group using multiple users attached to that group.
        Use users name as a parameter

        @Feature: Usergroup

        @Assert: User group is created successfully and contains all expected
        users.
        """
        users = [make_user()['login'] for _ in range(randint(3, 5))]
        user_group = make_usergroup({'users': users})
        self.assertEqual(sorted(users), sorted(user_group['users']))

    @tier1
    def test_positive_create_with_role_name(self):
        """Create new user group using valid role attached to that group. Use
        role name as a parameter

        @Feature: Usergroup

        @Assert: User group is created successfully.
        """
        for role_name in valid_data_list():
            with self.subTest(role_name):
                role = make_role({'name': role_name})
                user_group = make_usergroup({'roles': role['name']})
                self.assertEqual(len(user_group['roles']), 1)
                self.assertEqual(user_group['roles'][0], role_name)

    @tier1
    def test_positive_create_with_role_id(self):
        """Create new user group using valid role attached to that group. Use
        role id as a parameter

        @Feature: Usergroup

        @Assert: User group is created successfully.
        """
        role = make_role()
        user_group = make_usergroup({'role-ids': role['id']})
        self.assertEqual(user_group['roles'][0], role['name'])

    @tier1
    def test_positive_create_with_roles(self):
        """Create new user group using multiple roles attached to that group.
        Use roles name as a parameter

        @Feature: Usergroup

        @Assert: User group is created successfully and contains all expected
        roles
        """
        roles = [make_role()['name'] for _ in range(randint(3, 5))]
        user_group = make_usergroup({'roles': roles})
        self.assertEqual(sorted(roles), sorted(user_group['roles']))

    @tier1
    def test_positive_create_with_usergroup_name(self):
        """Create new user group using another user group attached to the
        initial group. Use user group name as a parameter

        @Feature: Usergroup

        @Assert: User group is created successfully.
        """
        for name in valid_data_list():
            with self.subTest(name):
                sub_user_group = make_usergroup({'name': name})
                user_group = make_usergroup({
                    'user-groups': sub_user_group['name']})
                self.assertEqual(len(user_group['user-groups']), 1)
                self.assertEqual(user_group['user-groups'][0], name)

    @tier1
    def test_positive_create_with_usergroup_id(self):
        """Create new user group using another user group attached to the
        initial group. Use user group id as a parameter

        @Feature: Usergroup

        @Assert: User group is created successfully.
        """
        sub_user_group = make_usergroup()
        user_group = make_usergroup({
            'user-group-ids': sub_user_group['id']})
        self.assertEqual(user_group['user-groups'][0], sub_user_group['name'])

    @tier1
    def test_positive_create_with_usergroups(self):
        """Create new user group using multiple user groups attached to that
        initial group. Use user groups name as a parameter

        @Feature: Usergroup

        @Assert: User group is created successfully and contains all expected
        user groups
        """
        sub_user_groups = [
            make_usergroup()['name'] for _ in range(randint(3, 5))]
        user_group = make_usergroup({'user-groups': sub_user_groups})
        self.assertEqual(
            sorted(sub_user_groups), sorted(user_group['user-groups']))

    @tier1
    def test_negative_create_with_name(self):
        """Attempt to create user group with invalid name.

        @Feature: Usergroup

        @Assert: User group is not created.
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_usergroup({'name': name})
                with self.assertRaises(CLIReturnCodeError):
                    UserGroup.info({'name': name})

    @tier1
    def test_negative_create_with_same_name(self):
        """Attempt to create user group with a name of already existent entity.

        @Feature: Usergroup

        @Assert: User group is not created.
        """
        user_group = make_usergroup()
        with self.assertRaises(CLIFactoryError):
            make_usergroup({'name': user_group['name']})

    @tier1
    def test_positive_list(self):
        """Test user group list command

        @Feature: Usergroup

        @Assert: User group list command returns valid and expected data

        """
        user_group = make_usergroup()
        result_list = UserGroup.list({
            'search': 'name={0}'.format(user_group['name'])})
        self.assertTrue(len(result_list) > 0)
        self.assertTrue(
            UserGroup.exists(search=('name', user_group['name'])))

    @tier1
    def test_positive_update_by_id(self):
        """Update existing user group with different valid names. Use id of the
        user group as a parameter

        @Feature: Usergroup

        @Assert: User group is update successfully.
        """
        user_group = make_usergroup()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                UserGroup.update({
                    'id': user_group['id'],
                    'new-name': new_name,
                })
                user_group = UserGroup.info({'id': user_group['id']})
                self.assertEqual(user_group['name'], new_name)

    @tier1
    def test_positive_update_by_name(self):
        """Update existing user group with different valid names. Use name of
        the user group as a parameter

        @Feature: Usergroup

        @Assert: User group is update successfully.
        """
        user_group = make_usergroup()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                UserGroup.update({
                    'name': user_group['name'],
                    'new-name': new_name,
                })
                user_group = UserGroup.info({'id': user_group['id']})
                self.assertEqual(user_group['name'], new_name)

    @tier1
    def test_negative_update_by_id(self):
        """Attempt to update existing user group using different invalid names.
        Use id of the user group as a parameter

        @Feature: Usergroup

        @Assert: User group is not updated.
        """
        user_group = make_usergroup()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    UserGroup.update({
                        'id': user_group['id'],
                        'new-name': new_name,
                    })
                user_group = UserGroup.info({'id': user_group['id']})
                self.assertNotEqual(user_group['name'], new_name)

    @tier1
    def test_negative_update_by_name(self):
        """Attempt to update existing user group using different invalid names.
        Use name of the user group as a parameter

        @Feature: Usergroup

        @Assert: User group is not updated.
        """
        user_group = make_usergroup()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    UserGroup.update({
                        'name': user_group['name'],
                        'new-name': new_name,
                    })
                user_group = UserGroup.info({'id': user_group['id']})
                self.assertNotEqual(user_group['name'], new_name)

    @tier1
    def test_positive_delete_by_name(self):
        """Create user group with valid name and then delete it using that name

        @feature: Usergroup

        @assert: User group is deleted successfully
        """
        for name in valid_data_list():
            with self.subTest(name):
                user_group = make_usergroup({'name': name})
                UserGroup.delete({'name': user_group['name']})
                with self.assertRaises(CLIReturnCodeError):
                    UserGroup.info({'name': user_group['name']})

    @tier1
    def test_positive_delete_by_id(self):
        """Create user group with valid data and then delete it using its ID

        @feature: Usergroup

        @assert: User group is deleted successfully
        """
        user_group = make_usergroup()
        UserGroup.delete({'id': user_group['id']})
        with self.assertRaises(CLIReturnCodeError):
            UserGroup.info({'id': user_group['id']})

    @tier1
    def test_positive_delete_with_user_by_id(self):
        """Create new user group using valid user attached to that group. Then
        delete that user group using id of that group as a parameter

        @Feature: Usergroup

        @Assert: User group is deleted successfully.
        """
        user = make_user()
        user_group = make_usergroup({'user-ids': user['id']})
        UserGroup.delete({'id': user_group['id']})
        with self.assertRaises(CLIReturnCodeError):
            UserGroup.info({'id': user_group['id']})

    @tier2
    def test_positive_add_role_by_id(self):
        """Create new user group and new role. Then add created role to user
        group by id

        @Feature: Usergroup

        @Assert: Role is added to user group successfully.
        """
        role = make_role()
        user_group = make_usergroup()
        UserGroup.add_role({
            'id': user_group['id'],
            'role-id': role['id'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(user_group['roles'][0], role['name'])

    @tier2
    def test_positive_add_role_by_name(self):
        """Create new user group and new role. Then add created role to user
        group by name

        @Feature: Usergroup

        @Assert: Role is added to user group successfully.
        """
        role = make_role()
        user_group = make_usergroup()
        UserGroup.add_role({
            'id': user_group['id'],
            'role': role['name'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(user_group['roles'][0], role['name'])

    @tier2
    def test_positive_add_user_by_id(self):
        """Create new user group and new user. Then add created user to user
        group by id

        @Feature: Usergroup

        @Assert: User is added to user group successfully.
        """
        user = make_user()
        user_group = make_usergroup()
        UserGroup.add_user({
            'id': user_group['id'],
            'user-id': user['id'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(user_group['users'][0], user['login'])

    @tier2
    def test_positive_add_user_by_name(self):
        """Create new user group and new user. Then add created user to user
        group by name

        @Feature: Usergroup

        @Assert: User is added to user group successfully.
        """
        user = make_user()
        user_group = make_usergroup()
        UserGroup.add_user({
            'id': user_group['id'],
            'user': user['login'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(user_group['users'][0], user['login'])

    @tier2
    def test_positive_add_user_group_by_id(self):
        """Create two new user groups. Then add one user group to another by id

        @Feature: Usergroup

        @Assert: User group is added to another user group successfully.
        """
        sub_user_group = make_usergroup()
        user_group = make_usergroup()
        UserGroup.add_user_group({
            'id': user_group['id'],
            'user-group-id': sub_user_group['id'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(user_group['user-groups'][0], sub_user_group['name'])

    @tier2
    def test_positive_add_user_group_by_name(self):
        """Create two new user groups. Then add one user group to another by
        name

        @Feature: Usergroup

        @Assert: User group is added to another user group successfully.
        """
        sub_user_group = make_usergroup()
        user_group = make_usergroup()
        UserGroup.add_user_group({
            'id': user_group['id'],
            'user-group': sub_user_group['name'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(user_group['user-groups'][0], sub_user_group['name'])

    @tier2
    def test_positive_remove_role_by_id(self):
        """Create new user group using valid role attached to that group. Then
        remove that role from user group by id

        @Feature: Usergroup

        @Assert: Role is removed from user group successfully.
        """
        role = make_role()
        user_group = make_usergroup({'role-ids': role['id']})
        self.assertEqual(len(user_group['roles']), 1)
        UserGroup.remove_role({
            'id': user_group['id'],
            'role-id': role['id'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(len(user_group['roles']), 0)

    @tier2
    def test_positive_remove_role_by_name(self):
        """Create new user group using valid role attached to that group. Then
        remove that role from user group by name

        @Feature: Usergroup

        @Assert: Role is removed from user group successfully.
        """
        role = make_role()
        user_group = make_usergroup({'role-ids': role['id']})
        self.assertEqual(len(user_group['roles']), 1)
        UserGroup.remove_role({
            'id': user_group['id'],
            'role': role['name'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(len(user_group['roles']), 0)

    @tier2
    def test_positive_remove_user_by_id(self):
        """Create new user group using valid user attached to that group. Then
        remove that user from user group by id

        @Feature: Usergroup

        @Assert: User is removed from user group successfully.
        """
        user = make_user()
        user_group = make_usergroup({'user-ids': user['id']})
        self.assertEqual(len(user_group['users']), 1)
        UserGroup.remove_user({
            'id': user_group['id'],
            'user-id': user['id'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(len(user_group['users']), 0)

    @tier2
    def test_positive_remove_user_by_name(self):
        """Create new user group using valid user attached to that group. Then
        remove that user from user group by name

        @Feature: Usergroup

        @Assert: User is removed from user group successfully.
        """
        user = make_user()
        user_group = make_usergroup({'user-ids': user['id']})
        self.assertEqual(len(user_group['users']), 1)
        UserGroup.remove_user({
            'id': user_group['id'],
            'user': user['login'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(len(user_group['users']), 0)

    @tier2
    def test_positive_remove_usergroup_by_id(self):
        """Create new user group using another user group attached to the
        initial group. Then remove that attached user group by id

        @Feature: Usergroup

        @Assert: User group is removed from initial one successfully.
        """
        sub_user_group = make_usergroup()
        user_group = make_usergroup({'user-group-ids': sub_user_group['id']})
        self.assertEqual(len(user_group['user-groups']), 1)
        UserGroup.remove_user_group({
            'id': user_group['id'],
            'user-group-id': sub_user_group['id'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(len(user_group['user-groups']), 0)

    @tier2
    def test_positive_remove_usergroup_by_name(self):
        """Create new user group using another user group attached to the
        initial group. Then remove that attached user group by name

        @Feature: Usergroup

        @Assert: User group is removed from initial one successfully.
        """
        sub_user_group = make_usergroup()
        user_group = make_usergroup({'user-group-ids': sub_user_group['id']})
        self.assertEqual(len(user_group['user-groups']), 1)
        UserGroup.remove_user_group({
            'id': user_group['id'],
            'user-group': sub_user_group['name'],
        })
        user_group = UserGroup.info({'id': user_group['id']})
        self.assertEqual(len(user_group['user-groups']), 0)
