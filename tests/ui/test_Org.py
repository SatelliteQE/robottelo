#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from baseui import BaseUI
from robottelo.lib.common.helpers import generate_name
from robottelo.lib.ui.locators import *
from robottelo.lib.common.decorators import runIf

class Org(BaseUI):

    def org_page(self):
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_organizations()

    def _create_org(self, org_name=None, org_label=None, org_desc=None):
        self.org.create_org(org_name, org_label, org_desc)
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))
        self.user.find_element(locators["notif.close"]).click()

    def test_successful_create_org(self):
        "Successfully create a new org"
        self.org_page()
        self._create_org(generate_name(), generate_name(), generate_name())

