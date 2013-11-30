#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from baseui import BaseUI
from lib.common.helpers import generate_name
from lib.ui.locators import *
from time import sleep

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"


class Medium(BaseUI):
    
    def create_medium(self, name=None, path=None, os_family=None):
        name = name or generate_name(6)
        path = path or URL % generate_name(6)
        self.navigator.go_to_installation_media()  # go to media page
        sleep(5)
        self.medium.create(name, path, os_family)
       
    def test_create_medium(self):
        "Create new Media"
        name = generate_name(6)
        path = URL % generate_name(6)
        os_family = "Redhat"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_medium(name, path, os_family)
        sleep(5)
        self.assertTrue(self, self.medium.search(name))
                      
    def test_remove_medium(self):
        "Delete Media"
        name = generate_name(6)
        path = URL % generate_name(6)
        os_family = "Fedora"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_medium(name, path, os_family)
        self.medium.remove(name, True)
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))
        
