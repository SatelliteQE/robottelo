# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for UserGroup UI
"""

from robottelo.common.helpers import generate_name
from robottelo.common.helpers import generate_email_address
from robottelo.ui.locators import common_locators
from tests.ui.baseui import BaseUI


class UserGroup(BaseUI):
    """
    Implements UserGroup tests from UI
    """

    def create_usergroup(self, name, user=None):
        """
        Function to create a new user group with navigation
        """

        self.navigator.go_to_user_groups()
        self.usergroup.create(name, user)
        #TODO: assertion is pending, Foreman issue:3953

    def test_create_usergroup(self):
        """
        @Feature: Usergroup - Positive Create
        @Test: Create new Usergroup
        @Assert: Usergroup is created
        """

        user_name = generate_name(6)
        group_name = generate_name(6)
        password = generate_name(8)
        email = generate_email_address()
        search_key = "login"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_users()
        self.user.create(user_name, email, password, password)
        self.assertIsNotNone(self.user.search(user_name, search_key))
        self.create_usergroup(group_name, [user_name])

    def test_remove_usergroup(self):
        """
        @Feature: Usergroup - Positive Delete
        @Test: Delete an existing Usergroup
        @Assert: Usergroup is delete
        """

        name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_usergroup(name)
        self.usergroup.remove(name, True)
        self.assertTrue(self.usergroup.wait_until_element
                        (common_locators["notif.success"]))
        #TODO: asserIsNone pending due to issue:3953

    def test_update_usergroup(self):
        """
        @Feature: Usergroup - Positive Update
        @Test: Update usergroup with name or users
        @Assert: Usergroup is updated
        """

        name = generate_name(6)
        new_name = generate_name(4)
        user_name = generate_name(6)
        password = generate_name(8)
        email = generate_email_address()
        search_key = "login"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_users()
        self.user.create(user_name, email, password, password)
        self.assertIsNotNone(self.user.search(user_name, search_key))
        self.create_usergroup(name)
        self.usergroup.update(name, new_name, new_users=[user_name])
        #TODO: assertion is pending, Foreman issue:3953
