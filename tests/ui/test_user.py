# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for User UI
"""

from tests.ui.baseui import BaseUI
from robottelo.ui.locators import common_locators
from robottelo.common.helpers import generate_name
from robottelo.common.helpers import generate_email_address


class User(BaseUI):
    """
    Implements User tests from UI
    """

    def create_user(self, name=None, password=None,
                    email=None, search_key=None):
        """
        Function to create a new User
        """

        name = name or generate_name(8)
        password = password or generate_name(8)
        email = email or generate_email_address()
        self.navigator.go_to_users()
        self.user.create(name, email, password, password)
        self.assertIsNotNone(self.user.search(name, search_key))

    def test_create_user(self):
        """
        Create a new User
        """

        name = generate_name(6)
        password = generate_name(8)
        email = generate_email_address()
        search_key = "login"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_user(name, password, email, search_key)

    def test_delete_user(self):
        """
        Create and Delete a User
        """

        name = generate_name(6)
        password = generate_name(8)
        email = generate_email_address()
        search_key = "login"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_user(name, password, email, search_key)
        self.user.delete(name, search_key, really=True)
        self.assertTrue(self.user.wait_until_element(common_locators
                                                     ["notif.success"]))

    def test_update_password(self):
        """
        Creates a User and updates the password
        """

        name = generate_name(6)
        password = generate_name(8)
        new_password = generate_name(8)
        email = generate_email_address()
        search_key = "login"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_user(name, password, email, search_key)
        self.user.update(search_key, name, None, None, new_password)
        self.login.logout()
        self.login.login(name, new_password)
        self.assertTrue(self.login.is_logged())

    def test_update_role(self):
        """
        Creates a User and updates the password
        """

        name = generate_name(6)
        password = generate_name(8)
        email = generate_email_address()
        role = generate_name(6)
        search_key = "login"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_roles()
        self.role.create(role)
        self.assertIsNotNone(self, self.role.search(role))
        self.create_user(name, password, email, search_key)
        self.user.update(search_key, name, None, None, None,
                         None, None, None, role)
        #TODO assert newly added role/permissions for user
