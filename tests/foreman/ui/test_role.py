# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Roles UI
"""

from robottelo.common.decorators import skip_if_bug_open
from robottelo.common.helpers import generate_name
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators


class Role(UITestCase):
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

    def test_update_role_name(self):
        """
        @Feature: Role - Positive Update
        @Test: Update role name
        @Assert: Role is updated
        """
        name = generate_name(6)
        new_name = generate_name(4)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_roles()
        self.role.create(name)
        self.role.update(name, new_name)
        self.assertIsNotNone(self.role.search(new_name))

    def test_update_role_permission(self):
        """
        @Feature: Role - Positive Update
        @Test: Update role permissions
        @Assert: Role is updated
        """
        name = generate_name(6)
        resource_type = 'Architecture'
        permission_list = ['access_dashboard', 'access_settings']
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_roles()
        self.role.create(name)
        self.role.update(name, add_permission=True,
                         resource_type=resource_type,
                         permission_list=permission_list)

    @skip_if_bug_open('bugzilla', 1122898)
    def test_update_role_org(self):
        """
        @Feature: Role - Positive Update
        @Test: Update organization under selected role
        @Assert: Role is updated
        """
        name = generate_name(6)
        org_name = generate_name(6)
        resource_type = 'Activation Keys'
        permission_list = ['view_activation_keys']
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_roles()
        self.role.create(name)
        self.role.update(name, add_permission=True,
                         resource_type=resource_type,
                         permission_list=permission_list,
                         organization=[org_name])
