#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from baseui import BaseUI
from lib.ui.locators import *

class OperatingSys(BaseUI):
    
    def test_create_os(self):
        "create new OS"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_operating_systems() #go to operating system page
        self.operatingsys.create("testOS", "6", "2", "Redhat")
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))
        