#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.ui.locators import locators
from robottelo.common.helpers import generate_name
from robottelo.common.helpers import generate_string
from tests.ui.baseui import BaseUI


class OperatingSys(BaseUI):

    def test_create_os(self):
        "create new OS"
        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Redhat"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_operating_systems()  # go to operating system page
        self.operatingsys.create(name, major_version, minor_version, os_family)
        # UI doesn't raise notification - Raise Bug
        # self.assertTrue(self.user.wait_until_element(locators["notif.success"]))

    def test_remove_os(self):
        "Delete OS "
        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Redhat"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_operating_systems()  # go to operating system page
        self.operatingsys.create(name, major_version, minor_version, os_family)
        self.operatingsys.delete(name, really=True)
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))
