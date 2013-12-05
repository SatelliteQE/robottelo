#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from baseui import BaseUI
from lib.ui.locators import *
from lib.common.helpers import generate_name
from lib.common.helpers import generate_email_address

class Hostgroup(BaseUI):

    def test_create_hostgroup(self):
        name = generate_name(8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_host_groups()
        self.hostgroup.create(name)
        self.assertIsNotNone(self.hostgroup.search(name)) #confirm the Hostgroup appears in the UI

    def test_delete_hostgroup(self):
        name = generate_name(8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_host_groups()
        self.hostgroup.create(name)
        self.assertIsNotNone(self.hostgroup.search(name)) #confirm the Hostgroup appears in the UI
        self.hostgroup.delete(name, really = True)
        self.assertIsNone(self.hostgroup.search(name))

    def test_update_hostgroup(self):
        name = generate_name(7)
        updated_name = generate_name(7)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_host_groups()
        self.hostgroup.create(name)
        self.assertIsNotNone(self.hostgroup.search(name)) #confirm the Hostgroup appears in the UI
        self.hostgroup.update(name,new_name = updated_name)
        self.assertIsNotNone(self.hostgroup.search(updated_name))