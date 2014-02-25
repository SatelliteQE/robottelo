# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Roles UI
"""

from robottelo.common.helpers import generate_name
from robottelo.ui.locators import common_locators
from tests.ui.baseui import BaseUI


class Role(BaseUI):
    """
    Implements Roles tests from UI
    """

    def test_create_role(self):
        """
        @Feature: Role - Positive Create
        @Test: Create new role
        @Assert: Role is created
        """
        name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_roles()
        self.role.create(name)
        self.assertIsNotNone(self.role.search(name))

    def test_remove_role(self):
        """
        @Feature: Role - Positive Delete
        @Test: Delete an existing role
        @Assert: Role is deleted
        """
        name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_roles()
        self.role.create(name)
        self.role.remove(name, True)
        self.assertTrue(self.role.wait_until_element
                        (common_locators["notif.success"]))
        self.assertIsNone(self.role.search(name))

    def test_update_role(self):
        """
        @Feature: Role - Positive Update
        @Test: Update role with name/permission
        @Assert: Role is updated
        """
        name = generate_name(6)
        new_name = generate_name(4)
        perm_type = "Media"
        permissions = ['create_media', 'edit_media']  # List of permissions
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_roles()
        self.role.create(name)
        self.role.update(name, new_name, perm_type, permissions)
        self.assertIsNotNone(self.role.search(new_name))
