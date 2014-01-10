# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Roles UI
"""

from robottelo.common.helpers import generate_name
from robottelo.ui.locators import locators, common_locators
from tests.ui.baseui import BaseUI


class Role(BaseUI):
    """
    Implements Roles tests from UI
    """

    def test_create_role(self):
        """Create new Role"""
        name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_roles()
        self.role.create(name)
        self.assertIsNotNone(self, self.role.search
                            (name, locators['roles.role']))

    def test_remove_role(self):
        """Delete existing role"""
        name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_roles()
        self.role.create(name)
        self.role.remove(name, True)
        self.assertTrue(self, self.role.wait_until_element
                        (common_locators["notif.success"]))
        self.assertIsNone(self, self.role.search(name, locators
                                                 ['roles.role']))

    def test_update_role(self):
        """Create new role and update its name or permission"""
        name = generate_name(6)
        new_name = generate_name(4)
        perm_type = "Media"
        permissions = ['create_media', 'edit_media']  # List of permissions
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_roles()
        self.role.create(name)
        self.role.update(name, new_name, perm_type, permissions)
        self.assertIsNotNone(self, self.role.search
                             (new_name, locators['roles.role']))
