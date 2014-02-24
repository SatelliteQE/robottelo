# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai


"""
Test class for Host Group UI
"""

from tests.ui.baseui import BaseUI
from robottelo.common.helpers import generate_name


class Hostgroup(BaseUI):

    def test_create_hostgroup(self):
        """
        @Feature: Hostgroup - Positive Create
        @Test: Create new hostgroup
        @Assert: Hostgroup is created
        """
        name = generate_name(8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_host_groups()
        self.hostgroup.create(name)
        #confirm the Hostgroup appears in the UI
        self.assertIsNotNone(self.hostgroup.search(name))

    def test_delete_hostgroup(self):
        """
        @Feature: Hostgroup - Positive Delete
        @Test: Delete a hostgroup
        @Assert: Hostgroup is deleted
        """
        name = generate_name(8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_host_groups()
        self.hostgroup.create(name)
        #confirm the Hostgroup appears in the UI
        self.assertIsNotNone(self.hostgroup.search(name))
        self.hostgroup.delete(name, really=True)
        self.assertIsNone(self.hostgroup.search(name))

    def test_update_hostgroup(self):
        """
        @Feature: Hostgroup - Positive Update
        @Test: Update hostgroup with a new name
        @Assert: Hostgroup is updated
        """
        name = generate_name(7)
        updated_name = generate_name(7)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_host_groups()
        self.hostgroup.create(name)
        #confirm the Hostgroup appears in the UI
        self.assertIsNotNone(self.hostgroup.search(name))
        self.hostgroup.update(name, new_name=updated_name)
        self.assertIsNotNone(self.hostgroup.search(updated_name))
