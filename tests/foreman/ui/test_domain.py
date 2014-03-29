# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Domain UI
"""

from robottelo.ui.locators import common_locators
from robottelo.common.helpers import generate_name
from tests.ui.baseui import BaseUI

DOMAIN = "lab.dom.%s.com"


class Domain(BaseUI):
    """
    Implements domain tests from UI
    """
    def create_domain(self, name=None, description=None):
        """Function to create new domain"""
        name = name or DOMAIN % generate_name(4)
        description = description or name
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_domains()  # go to domain page
        self.domain.create(name, description)
        # UI throwing 'PGError' while performing search
        self.assertTrue(self,
                        self.domain.search(description))

    def test_create_domain(self):
        """
        @Feature: Domain - Create
        @Test: Create a new domain
        @Assert: Domain is created
        """
        name = DOMAIN % generate_name(4)
        description = name
        self.create_domain(name, description)

    def test_remove_domain(self):
        """
        @Feature: Domain - Delete
        @Test: Delete a domain
        @Assert: Domain is deleted
        """
        name = DOMAIN % generate_name(4)
        description = name
        self.create_domain(name, description)
        self.domain.delete(name, really=True)
        self.assertTrue(self.user.wait_until_element(common_locators
                                                     ["notif.success"]))
        self.assertIsNone(self.domain.search(name))

    def test_update_domain(self):
        """
        @Feature: Domain - Update
        @Test: Update a domain with name and description
        @Assert: Domain is updated
        """
        name = DOMAIN % generate_name(4)
        description = name
        new_name = DOMAIN % generate_name(4)
        new_description = new_name
        self.create_domain(name, description)
        self.domain.update(name, new_name, new_description)
        self.assertIsNotNone(self,
                             self.domain.search(new_description))

    def test_set_parameter(self):
        """
        @Feature: Domain - Misc
        @Test: Set a paramter in a domain
        @Assert: Domain is updated
        """
        name = DOMAIN % generate_name(4)
        description = name
        param_name = generate_name(4)
        param_value = generate_name(3)
        self.create_domain(name, description)
        self.domain.set_domain_parameter(description, param_name, param_value)

    def test_remove_parameter(self):
        """
        @Feature: Domain - Misc
        @Test: Remove a selected domain paramter
        @Assert: Domain parameter is removed
        """
        name = DOMAIN % generate_name(4)
        description = name
        param_name = generate_name(4)
        param_value = generate_name(3)
        self.create_domain(name, description)
        self.domain.set_domain_parameter(description, param_name, param_value)
        self.domain.remove_domain_parameter(description, param_name)
