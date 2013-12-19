#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.ui.locators import locators
from robottelo.common.helpers import generate_name
from robottelo.common.helpers import generate_string
from tests.ui.baseui import BaseUI

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"


class OperatingSys(BaseUI):

    def create_arch(self, arch_name, os_name=None):
        arch_name = arch_name or generate_name(4)
        os_name = os_name or generate_name(6)
        self.navigator.go_to_architectures()  # go to architecture page
        self.architecture.create(arch_name, os_name)

    def test_create_os(self):
        "create new OS"
        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Redhat"
        arch = generate_name(4)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_architectures()  # go to architecture page
        self.architecture.create(arch)
        self.navigator.go_to_operating_systems()  # go to operating system page
        self.operatingsys.create(name, major_version,
                                 minor_version, os_family, arch)
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

    def test_update_os(self):
        "Update OS name, major_version, minor_version, os_family, arch, medium"
        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Redhat"
        new_name = generate_name(4)
        new_major_version = generate_string('numeric', 1)
        new_minor_version = generate_string('numeric', 1)
        new_os_family = "Debian"
        new_arch = generate_name(4)
        medium = generate_name(4)
        path = URL % generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_arch(new_arch, None)
        self.navigator.go_to_installation_media()
        self.medium.create(medium, path, None)
        self.navigator.go_to_operating_systems()
        self.operatingsys.create(name, major_version,
                                 minor_version, os_family)
        self.operatingsys.update(name, new_name, new_major_version,
                                 new_minor_version, new_os_family,
                                 new_arch, None, medium)

    def test_set_parameter(self):
        "Set OS parameter"
        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        param_name = generate_name(4)
        param_value = generate_name(3)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_operating_systems()  # go to operating system page
        self.operatingsys.create(name, major_version)
        self.operatingsys.set_os_parameter(name, param_name, param_value)

    def test_remove_parameter(self):
        "Remove selected OS parameter"
        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        param_name = generate_name(4)
        param_value = generate_name(3)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_operating_systems()  # go to operating system page
        self.operatingsys.create(name, major_version)
        self.operatingsys.set_os_parameter(name, param_name, param_value)
        self.operatingsys.remove_os_parameter(name, param_name)
