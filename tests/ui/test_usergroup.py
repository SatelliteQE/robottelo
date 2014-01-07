# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for UserGroup UI
"""

from robottelo.common.helpers import generate_name
from robottelo.common.helpers import generate_email_address
from robottelo.ui.locators import locators
from tests.ui.baseui import BaseUI


class UserGroup(BaseUI):
    """
    Implements UserGroup tests from UI
    """

    def create_user(self, name):
        "Function to create a new User"
        password = generate_name(8)
        email = generate_email_address()
        search_key = "login"
        self.navigator.go_to_users()
        self.user.create(name, email, password, password)
        self.assertIsNotNone(self.user.search
                             (name, locators['users.user'], search_key))

    def create_usergroup(self, name, user=None):
        "Function to create a new user group with navigation"
        self.navigator.go_to_user_groups()
        self.usergroup.create(name, user)
        #TODO: assertion is pending, Foreman issue:3953

    def test_create_usergroup(self):
        "Create new usergroup"
        user_name = generate_name(6)
        group_name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_user(user_name)
        self.create_usergroup(group_name, user_name)

    def test_remove_usergroup(self):
        "Delete existing usergroup"
        name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_usergroup(name, None)
        self.usergroup.remove(name, True)
        self.assertTrue(self.medium.wait_until_element
                        (locators["notif.success"]))

    def test_update_usergroup(self):
        "Create new usergroup and update its name or users"
        name = generate_name(6)
        new_name = generate_name(4)
        user_name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_user(user_name)
        self.create_usergroup(name, None)
        self.usergroup.update(name, new_name, user_name)
        #TODO: assertion is pending, Foreman issue:3953
