# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Environment UI
"""

from tests.ui.baseui import BaseUI
from robottelo.ui.locators import common_locators
from robottelo.common.helpers import generate_name


class Environment(BaseUI):
    """
    Implements all Environment tests
    """

    def create_org(self, org_name=None):
        """Creates Org"""
        org_name = org_name or generate_name(8, 8)
        self.navigator.go_to_org()  # go to org page
        self.org.create(org_name)

    def test_create_env(self):
        """
        @Feature: Environment - Positive Create
        @Test: Create new environment
        @Assert: Environment is created
        """
        name = generate_name(6)
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.navigator.go_to_environments()
        self.environment.create(name, [org_name])
        search = self.environment.search(name)
        self.assertIsNotNone(search)

    def test_update_env(self):
        """
        @Feature: Environment - Positive Update
        @Test: Update an environment and associated OS
        @Assert: Environment is updated
        """
        name = generate_name(6)
        new_name = generate_name(6)
        org_name = generate_name(8, 8)
        new_org = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.navigator.go_to_environments()
        self.environment.create(name, [org_name])
        self.create_org(new_org)
        self.navigator.go_to_environments()
        self.environment.update(name, [org_name], [new_org],
                                new_name=new_name)
        search = self.environment.search(new_name)
        self.assertIsNotNone(search)

    def test_remove_env(self):
        """
        @Feature: Environment - Positive Delete
        @Test: Delete an environment
        @Assert: Environment is deleted
        """
        name = generate_name(6)
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.navigator.go_to_environments()
        self.environment.create(name, [org_name])
        self.environment.delete(name, really=True)
        notif = self.user.wait_until_element(common_locators["notif.success"])
        self.assertTrue(notif)
