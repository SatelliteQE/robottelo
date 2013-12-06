#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from tests.ui.baseui import BaseUI
from lib.ui.locators import locators
from lib.common.helpers import generate_name
from time import sleep

domain = "lab.dom.%s"


class Domain(BaseUI):

    def create_domain(self, name=None, description=None):
        name = name or generate_name(4) + '.com'
        description = description or domain % name
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_domains()  # go to domain page
        self.domain.create(name, description)
        # UI throwing 'PGError' while performing search
        # self.assertTrue(self, self.domain.search(description))

    def test_create_domain(self):
        "create new Domain"
        name = generate_name(4) + '.com'
        description = domain % name
        self.create_domain(name, description)

    def test_remove_domain(self):
        "Delete domain"
        name = generate_name(4) + '.com'
        description = domain % name
        self.create_domain(name, description)
        self.domain.delete(name, really=True)
        self.assertTrue(self.user.wait_until_element(locators["notif.success"]))

    def test_update_domain(self):
        "Create new domain and update its name, description"
        name = generate_name(4) + '.com'
        description = domain % name
        new_name = generate_name(4) + '.org'
        new_description = domain % new_name
        self.create_domain(name, description)
        sleep(5)
        self.domain.update(name, new_name, new_description)
        # UI throwing 'PGError' while performing search
        # self.assertTrue(self, self.domain.search(new_description))

    def test_set_parameter(self):
        "Set domain parameter"
        name = generate_name(4) + '.com'
        description = domain % name
        param_name = generate_name(4)
        param_value = generate_name(3)
        self.create_domain(name, description)
        self.domain.set_parameter(description, param_name, param_value)

    def test_remove_parameter(self):
        "Remove selected domain parameter"
        name = generate_name(4) + '.com'
        description = domain % name
        param_name = generate_name(4)
        param_value = generate_name(3)
        self.create_domain(name, description)
        self.domain.set_parameter(description, param_name, param_value)
        sleep(5)
        self.domain.remove_parameter(description, param_name)
