# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Domain UI"""
from ddt import ddt
from fauxfactory import gen_string
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_domain
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session

DOMAIN = "lab.dom.%s.com"


@run_only_on('sat')
@ddt
class Domain(UITestCase):
    """Implements Domain tests in UI"""

    @data(*generate_strings_list(len1=4))
    def test_create_domain_1(self, name):
        """@Test: Create a new domain

        @Feature: Domain - Positive Create domain

        @Assert: Domain is created

        """
        domain_name = description = DOMAIN % name
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)

    # The length of chars is in accordance with DOMAIN global variable.
    @data(
        gen_string('alphanumeric', 243),
        gen_string('alpha', 243),
        gen_string('numeric', 243),
        gen_string('latin1', 243),
        gen_string('utf8', 243),
    )
    def test_create_domain_2(self, name):
        """@Test: Create a new domain

        @Feature: Domain - Positive Create domain with 255 chars

        @Assert: Domain is created

        """
        domain_name = description = DOMAIN % name
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)

    @data(*generate_strings_list(len1=4))
    def test_remove_domain(self, name):
        """@Test: Delete a domain

        @Feature: Domain - Delete

        @Assert: Domain is deleted

        """
        name = gen_string("alpha", 4)
        domain_name = description = DOMAIN % name
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            self.domain.delete(description, really=True,)
            self.assertIsNotNone(self.user.wait_until_element(
                common_locators["notif.success"]))
            self.assertIsNone(self.domain.search(description, timeout=5))

    @data({'name': gen_string('alpha', 10),
           'newname': gen_string('alpha', 10)},
          {'name': gen_string('numeric', 10),
           'newname': gen_string('numeric', 10)},
          {'name': gen_string('alphanumeric', 10),
           'newname': gen_string('alphanumeric', 10)},
          {'name': gen_string('utf8', 10),
           'newname': gen_string('utf8', 10)},
          {'name': gen_string('latin1', 10),
           'newname': gen_string('latin1', 10)},
          {'name': gen_string('html', 10),
           'newname': gen_string('html', 10)})
    def test_update_domain(self, testdata):
        """@Test: Update a domain with name and description\

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

    # The length of chars is in accordance with DOMAIN global variable.
    @data(*generate_strings_list(len1=244))
    def test_negative_create_domain_1(self, name):
        """@Test: Negative create a domain with name and description\

        @Feature: Domain - Negative Create

        @Assert: Domain is not created

        """
        domain_name = description = DOMAIN % name
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description, timeout=5)
            self.assertIsNone(element)

    @data("", "  ")
    def test_negative_create_domain_2(self, name):
        """@Test: Create domain with whitespace and blank in name

        @Feature: Domain - Negative Create

        @Assert: Domain is not created

        """
        domain_name = description = name
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    @data(*generate_strings_list(len1=4))
    def test_positive_set_domain_parameter_1(self, name):
        """@Test: Set parameter name and value for domain

        @Feature: Domain - Misc

        @Assert: Domain is updated

        """
        domain_name = description = DOMAIN % name
        param_name = gen_string("alpha", 4)
        param_value = gen_string("alpha", 3)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(description, param_name,
                                                 param_value)
            except Exception as e:
                self.fail(e)

    def test_positive_set_domain_parameter_2(self):
        """@Test: Set a parameter in a domain with 255 chars in name and value.

        @Feature: Domain - Misc.

        @Assert: Domain parameter is created.

        """
        name = gen_string("alpha", 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string("alpha", 255)
        param_value = gen_string("alpha", 255)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(description, param_name,
                                                 param_value)
            except Exception as e:
                self.fail(e)

    def test_positive_set_domain_parameter_3(self):
        """@Test: Set a parameter in a domain with blank value.

        @Feature: Domain - Misc.

        @Assert: Domain parameter is created with blank value.

        """
        name = gen_string("alpha", 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string("alpha", 4)
        param_value = ""
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(description, param_name,
                                                 param_value)
            except Exception as e:
                self.fail(e)

    def test_set_domain_parameter_negative_1(self):
        """@Test: Set a parameter in a domain with 256 chars in name and value.

        @Feature: Domain - Misc.

        @Assert: Domain parameter is not updated.

        """
        name = gen_string("alpha", 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string("alpha", 256)
        param_value = gen_string("alpha", 256)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(description, param_name,
                                                 param_value)
            except Exception as e:
                self.fail(e)
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators["common_param_error"]))

    @skip_if_bug_open('bugzilla', 1123360)
    def test_set_domain_parameter_negative_2(self):
        """@Test: Again set the same parameter for domain with name and value.

        @Feature: Domain - Misc.

        @Assert: Domain parameter is not updated.

        @BZ: 1123360

        """
        name = gen_string("alpha", 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string("alpha", 8)
        param_value = gen_string("alpha", 8)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(description, param_name,
                                                 param_value)
                self.domain.set_domain_parameter(description, param_name,
                                                 param_value)
            except Exception as e:
                self.fail(e)
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators["common_param_error"]))

    @data(*generate_strings_list(len1=4))
    def test_remove_domain_parameter(self, name):
        """@Test: Remove a selected domain paramter

        @Feature: Domain - Misc

        @Assert: Domain parameter is removed

        """
        domain_name = description = DOMAIN % name
        param_name = gen_string("alpha", 3)
        param_value = gen_string("alpha", 3)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(description, param_name,
                                                 param_value)
                self.domain.remove_domain_parameter(description, param_name)
            except Exception as e:
                self.fail(e)
