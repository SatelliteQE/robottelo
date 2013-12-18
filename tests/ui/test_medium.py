#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Medium UI
"""

from robottelo.common.helpers import generate_name
from robottelo.ui.locators import locators
from tests.ui.baseui import BaseUI

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"


class Medium(BaseUI):

    def create_medium(self, name=None, path=None, os_family=None):
        name = name or generate_name(6)
        path = path or URL % generate_name(6)
        self.navigator.go_to_installation_media()  # go to media page
        self.medium.create(name, path, os_family)

    def test_create_medium(self):
        "Create new Media"
        name = generate_name(6)
        path = URL % generate_name(6)
        os_family = "Redhat"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_medium(name, path, os_family)
        self.assertTrue(self, self.medium.search(name))

    def test_remove_medium(self):
        "Delete Media"
        name = generate_name(6)
        path = URL % generate_name(6)
        os_family = "Redhat"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_medium(name, path, os_family)
        self.medium.remove(name, True)
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))

    def test_update_medium(self):
        "Create new Media and update its name, path and OS family"
        name = generate_name(6)
        newname = generate_name(4)
        path = URL % generate_name(6)
        newpath = URL % generate_name(6)
        os_family = "Redhat"
        new_os_family = "Debian"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_medium(name, path, os_family)
        self.medium.update(name, newname, newpath, new_os_family)
        self.assertTrue(self, self.medium.search(newname))
