# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Organization UI
"""

from robottelo.common.helpers import generate_name
from tests.ui.baseui import BaseUI


class Org(BaseUI):
    """
    Implements Organization tests in UI
    """

    def create_org(self, org_name=None):
        """Creates Org"""
        org_name = org_name or generate_name(8, 8)
        self.navigator.go_to_org()  # go to org page
        self.org.create(org_name)
        self.navigator.go_to_org()

    def test_create_org(self):
        """Create new org - given a valid org name"""
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.assertIsNotNone(
            self.org.search(org_name))

    def test_update_org(self):
        """Update org name - given a valid new org name"""
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.org.search(org_name)
        new_name = generate_name(8, 8)
        self.org.update(org_name, new_name)
        self.assertIsNotNone(
            self.org.search(new_name))

    def test_remove_org(self):
        """Remove org name - given a valid existing org name"""
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.org.remove(org_name, really=True)
        self.assertIsNone(
            self.org.search(org_name))
