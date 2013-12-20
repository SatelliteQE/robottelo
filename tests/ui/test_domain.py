#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Domain UI
"""

from robottelo.ui.locators import locators
from robottelo.common.helpers import generate_name
from tests.ui.baseui import BaseUI

DOMAIN = "lab.dom.%s"


class Domain(BaseUI):
    """
    Implements domain tests from UI
    """
    def create_domain(self, name=None, description=None):
        """Function to create new domain"""
        name = name or generate_name(4) + '.com'
        description = description or DOMAIN % name
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_domains()  # go to domain page
        self.domain.create(name, description)
        # UI throwing 'PGError' while performing search
        # self.assertTrue(self, self.domain.search(description))

    def test_create_domain(self):
        """create new Domain"""
        name = generate_name(4) + '.com'
        description = DOMAIN % name
        self.create_domain(name, description)

    def test_remove_domain(self):
        """Creates new domain and delete it"""
        name = generate_name(4) + '.com'
        description = DOMAIN % name
        self.create_domain(name, description)
        self.domain.delete(name, really=True)
        self.assertTrue(self.user.wait_until_element(locators
                                                     ["notif.success"]))

    def test_update_domain(self):
        """Create new domain and update its name, description"""
        name = generate_name(4) + '.com'
        description = DOMAIN % name
        new_name = generate_name(4) + '.org'
        new_description = DOMAIN % new_name
        self.create_domain(name, description)
        self.domain.update(name, new_name, new_description)
        # UI throwing 'PGError' while performing search
        # self.assertTrue(self, self.domain.search(new_description))

    def test_set_parameter(self):
        """Set domain parameter"""
        name = generate_name(4) + '.com'
        description = DOMAIN % name
        param_name = generate_name(4)
        param_value = generate_name(3)
        self.create_domain(name, description)
        self.domain.set_domain_parameter(description, param_name, param_value)

    def test_remove_parameter(self):
        """Remove selected domain parameter"""
        name = generate_name(4) + '.com'
        description = DOMAIN % name
        param_name = generate_name(4)
        param_value = generate_name(3)
        self.create_domain(name, description)
        self.domain.set_domain_parameter(description, param_name, param_value)
        self.domain.remove_domain_parameter(description, param_name)
