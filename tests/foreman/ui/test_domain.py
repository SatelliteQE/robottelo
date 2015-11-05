# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for Domain UI"""
from fauxfactory import gen_string
from robottelo.constants import DOMAIN
from robottelo.decorators import (
    bz_bug_is_open, run_only_on, skip_if_bug_open)
from robottelo.helpers import generate_strings_list, invalid_values_list
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_domain
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


def valid_long_domain_names():
    """Returns a list of valid long domain names

    The length of chars is in accordance with DOMAIN global variable.

    """
    return[
        gen_string('alphanumeric', 243),
        gen_string('alpha', 243),
        gen_string('numeric', 243),
        gen_string('latin1', 243),
        gen_string('utf8', 243),
    ]


def valid_domain_update_data():
    """Returns a list of valid test data for domain update tests"""
    return [
        {'name': gen_string('alpha', 10)},
        {'name': gen_string('numeric', 10)},
        {'name': gen_string('alphanumeric', 10)},
        {'name': gen_string('utf8', 10)},
        {'name': gen_string('latin1', 10)},
        {'name': gen_string('html', 10), 'bugzilla': 1220104}
    ]


class Domain(UITestCase):
    """Implements Domain tests in UI"""

    @run_only_on('sat')
    def test_create_domain_1(self):
        """@Test: Create a new domain

        @Feature: Domain - Positive Create domain

        @Assert: Domain is created

        """
        with Session(self.browser) as session:
            for name in generate_strings_list(len1=4):
                with self.subTest(name):
                    domain_name = description = DOMAIN % name
                    make_domain(
                        session, name=domain_name, description=description)
                    element = self.domain.search(description)
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    def test_create_domain_2(self):
        """@Test: Create a new domain

        @Feature: Domain - Positive Create domain with 255 chars

        @Assert: Domain is created

        """
        with Session(self.browser) as session:
            for name in valid_long_domain_names():
                with self.subTest(name):
                    domain_name = description = DOMAIN % name
                    make_domain(
                        session, name=domain_name, description=description)
                    element = self.domain.search(description)
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    def test_delete_domain(self):
        """@Test: Delete a domain

        @Feature: Domain - Delete

        @Assert: Domain is deleted

        """
        domain_name = description = DOMAIN % gen_string('alpha')
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            self.domain.delete(domain_name)

    @run_only_on('sat')
    def test_update_domain(self):
        """@Test: Update a domain with name and description

        @Feature: Domain - Update

        @Assert: Domain is updated

        """
        domain_name = description = DOMAIN % gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            self.assertIsNotNone(self.domain.search(domain_name))
            for testdata in valid_domain_update_data():
                with self.subTest(testdata):
                    bug_id = testdata.pop('bugzilla', None)
                    if bug_id is not None and bz_bug_is_open(bug_id):
                        self.skipTest('Bugzilla bug {0} is open.'.format(
                            bug_id))
                    new_name = new_description = DOMAIN % testdata['name']
                    self.domain.update(domain_name, new_name, new_description)
                    self.assertIsNotNone(self.domain.search(new_name))
                    domain_name = new_name  # for next iteration

    @run_only_on('sat')
    def test_negative_create_domain(self):
        """@Test: Try to create domain and use whitespace, blank, tab symbol or
        too long string of different types as its name value

        @Feature: Domain - Negative Create

        @Assert: Domain is not created

        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_domain(session, name=name, description=name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @run_only_on('sat')
    def test_positive_set_domain_parameter_1(self):
        """@Test: Set parameter name and value for domain

        @Feature: Domain - Misc

        @Assert: Domain is updated

        """
        with Session(self.browser) as session:
            for name in generate_strings_list(len1=4):
                with self.subTest(name):
                    domain_name = description = DOMAIN % name
                    param_name = gen_string('alpha', 4)
                    param_value = gen_string('alpha', 3)
                    make_domain(
                        session, name=domain_name, description=description)
                    self.assertIsNotNone(self.domain.search(domain_name))
                    try:
                        self.domain.set_domain_parameter(
                            description, param_name, param_value)
                    except UIError as err:
                        self.fail(err)

    @run_only_on('sat')
    def test_positive_set_domain_parameter_2(self):
        """@Test: Set a parameter in a domain with 255 chars in name and value.

        @Feature: Domain - Misc.

        @Assert: Domain parameter is created.

        """
        name = gen_string('alpha', 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string('alpha', 255)
        param_value = gen_string('alpha', 255)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(
                    description, param_name, param_value)
            except UIError as err:
                self.fail(err)

    @run_only_on('sat')
    def test_positive_set_domain_parameter_3(self):
        """@Test: Set a parameter in a domain with blank value.

        @Feature: Domain - Misc.

        @Assert: Domain parameter is created with blank value.

        """
        name = gen_string('alpha', 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string('alpha', 4)
        param_value = ''
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(
                    description, param_name, param_value)
            except UIError as err:
                self.fail(err)

    @run_only_on('sat')
    def test_set_domain_parameter_negative_1(self):
        """@Test: Set a parameter in a domain with 256 chars in name and value.

        @Feature: Domain - Misc.

        @Assert: Domain parameter is not updated.

        """
        name = gen_string('alpha', 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string('alpha', 256)
        param_value = gen_string('alpha', 256)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(
                    description, param_name, param_value)
            except UIError as err:
                self.fail(err)
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators['common_param_error']))

    @skip_if_bug_open('bugzilla', 1123360)
    @run_only_on('sat')
    def test_set_domain_parameter_negative_2(self):
        """@Test: Again set the same parameter for domain with name and value.

        @Feature: Domain - Misc.

        @Assert: Domain parameter is not updated.

        @BZ: 1123360

        """
        name = gen_string('alpha', 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string('alpha', 8)
        param_value = gen_string('alpha', 8)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(
                    description, param_name, param_value)
                self.domain.set_domain_parameter(
                    description, param_name, param_value)
            except UIError as err:
                self.fail(err)
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators['common_param_error']))

    @run_only_on('sat')
    def test_remove_domain_parameter(self):
        """@Test: Remove a selected domain parameter

        @Feature: Domain - Misc

        @Assert: Domain parameter is removed

        """
        with Session(self.browser) as session:
            for name in generate_strings_list(len1=4):
                with self.subTest(name):
                    domain_name = description = DOMAIN % name
                    param_name = gen_string('alpha', 3)
                    param_value = gen_string('alpha', 3)
                    make_domain(
                        session, name=domain_name, description=description)
                    element = self.domain.search(domain_name)
                    self.assertIsNotNone(element)
                    try:
                        self.domain.set_domain_parameter(
                            description, param_name, param_value)
                        self.domain.remove_domain_parameter(
                            description, param_name)
                    except UIError as err:
                        self.fail(err)
