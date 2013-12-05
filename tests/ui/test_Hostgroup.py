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