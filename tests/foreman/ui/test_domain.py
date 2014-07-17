# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Domain UI
"""
from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string, generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_org, make_loc,
                                  make_domain)
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session

DOMAIN = "lab.dom.%s.com"


@ddt
class Domain(UITestCase):
    """
    Implements Domain tests in UI
    """
    org_name = None
    loc_name = None

    def setUp(self):
        super(Domain, self).setUp()
        # Make sure to use the Class' org_name instance
        if Domain.org_name is None and Domain.loc_name is None:
            Domain.org_name = generate_string("alpha", 8)
            Domain.loc_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=Domain.org_name)
                make_loc(session, name=Domain.loc_name)

    @attr('ui', 'domain', 'implemented')
    @data(*generate_strings_list(len1=4))
    def test_create_domain(self, name):
        """
        @Test: Create a new domain
        @Feature: Domain - Create
        @Assert: Domain is created
        """
        domain_name = description = DOMAIN % name
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)

    @attr('ui', 'domain', 'implemented')
    @data(*generate_strings_list(len1=4))
    def test_remove_domain(self, name):
        """
        @Test: Delete a domain
        @Feature: Domain - Delete
        @Assert: Domain is deleted
        """
        name = generate_string("alpha", 4)
        domain_name = description = DOMAIN % name
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            self.domain.delete(description, really=True,)
            self.assertIsNotNone(self.user.wait_until_element(
                common_locators["notif.success"]))
            self.assertIsNone(self.domain.search(description, timeout=5))

    @attr('ui', 'domain', 'implemented')
    @data({'name': generate_string('alpha', 10),
           'newname': generate_string('alpha', 10)},
          {'name': generate_string('numeric', 10),
           'newname': generate_string('numeric', 10)},
          {'name': generate_string('alphanumeric', 10),
           'newname': generate_string('alphanumeric', 10)},
          {'name': generate_string('utf8', 10),
           'newname': generate_string('utf8', 10)},
          {'name': generate_string('latin1', 10),
           'newname': generate_string('latin1', 10)},
          {'name': generate_string('html', 10),
           'newname': generate_string('html', 10)})
    def test_update_domain(self, testdata):
        """
        @Test: Update a domain with name and description\
        @Feature: Domain - Update
        @Assert: Domain is updated
        """
        domain_name = description = DOMAIN % testdata['name']
        new_name = new_description = DOMAIN % testdata['newname']
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            self.domain.update(domain_name, new_name, new_description)
            self.assertIsNotNone(self.domain.search(new_description))

    @attr('ui', 'domain', 'implemented')
    @data(*generate_strings_list(len1=4))
    def test_set_parameter(self, name):
        """
        @Test: Set a paramter in a domain
        @Feature: Domain - Misc
        @Assert: Domain is updated
        """
        domain_name = description = DOMAIN % name
        param_name = generate_string("alpha", 4)
        param_value = generate_string("alpha", 3)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            self.domain.set_domain_parameter(description, param_name,
                                             param_value)

    @attr('ui', 'domain', 'implemented')
    @data(*generate_strings_list(len1=4))
    def test_remove_parameter(self, name):
        """
        @Test: Remove a selected domain paramter
        @Feature: Domain - Misc
        @Assert: Domain parameter is removed
        """
        domain_name = description = DOMAIN % name
        param_name = generate_string("alpha", 3)
        param_value = generate_string("alpha", 3)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            self.domain.set_domain_parameter(description, param_name,
                                             param_value)
            self.domain.remove_domain_parameter(description, param_name)
