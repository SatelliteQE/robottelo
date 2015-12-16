# -*- encoding: utf-8 -*-
"""Test class for Architecture UI"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import run_only_on, tier1
from robottelo.test import UITestCase
from robottelo.ui.factory import make_arch
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


def valid_arch_os_names():
    """Returns a tuple of arch/os names for creation tests"""
    return(
        {u'name': gen_string('alpha'), u'os_name': gen_string('alpha')},
        {u'name': gen_string('html'), u'os_name': gen_string('html')},
        {u'name': gen_string('utf8'), u'os_name': gen_string('utf8')},
        {u'name': gen_string('alphanumeric'),
         u'os_name': gen_string('alphanumeric')}
    )


class ArchitectureTestCase(UITestCase):
    """Implements Architecture tests from UI"""

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_os(self):
        """@Test: Create a new Architecture with OS

        @Feature: Architecture - Positive Create

        @Assert: Architecture is created
        """
        with Session(self.browser) as session:
            for test_data in valid_arch_os_names():
                with self.subTest(test_data):
                    entities.OperatingSystem(
                        name=test_data['os_name']).create()
                    make_arch(session, name=test_data['name'],
                              os_names=[test_data['os_name']])
                    self.assertIsNotNone(
                        self.architecture.search(test_data['name']))

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """@Test: Create a new Architecture with different data

        @Feature: Architecture - Positive Create

        @Assert: Architecture is created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_arch(session, name=name)
                    self.assertIsNotNone(self.architecture.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """@Test: Try to create architecture and use whitespace, blank, tab
        symbol or too long string of different types as its name value

        @Feature: Architecture - Negative Create

        @Assert: Architecture is not created
        """
        with Session(self.browser) as session:
            for invalid_name in invalid_values_list(interface='ui'):
                with self.subTest(invalid_name):
                    make_arch(session, name=invalid_name)
                    self.assertIsNotNone(self.architecture.wait_until_element(
                        common_locators['name_haserror']))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """@Test: Create a new Architecture with same name

        @Feature: Architecture - Negative Create

        @Assert: Architecture is not created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_arch(session, name=name)
                    self.assertIsNotNone(self.architecture.search(name))
                    make_arch(session, name=name)
                    self.assertIsNotNone(self.architecture.wait_until_element(
                        common_locators['name_haserror']))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """@Test: Delete an existing Architecture

        @Feature: Architecture - Delete

        @Assert: Architecture is deleted
        """
        os = entities.OperatingSystem(name=gen_string('alpha')).create()
        with Session(self.browser) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    entities.Architecture(
                        name=name, operatingsystem=[os]).create()
                    session.nav.go_to_architectures()
                    self.architecture.delete(name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_name_and_os(self):
        """@Test: Update Architecture with new name and OS

        @Feature: Architecture - Update

        @Assert: Architecture is updated
        """
        old_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_arch(session, name=old_name)
            self.assertIsNotNone(self.architecture.search(old_name))
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    os_name = gen_string('alpha')
                    entities.OperatingSystem(name=os_name).create()
                    self.architecture.update(
                        old_name, new_name, new_os_names=[os_name])
                    self.assertIsNotNone(self.architecture.search(new_name))
                    old_name = new_name  # for next iteration
