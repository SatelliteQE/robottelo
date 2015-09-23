# -*- encoding: utf-8 -*-
"""Test class for Architecture UI"""
from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from robottelo.decorators import data, run_only_on
from robottelo.helpers import generate_strings_list, invalid_values_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_arch
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class Architecture(UITestCase):
    """Implements Architecture tests from UI"""

    @data({u'name': gen_string('alpha'),
           u'os_name': gen_string('alpha')},
          {u'name': gen_string('html'),
           u'os_name': gen_string('html')},
          {u'name': gen_string('utf8'),
           u'os_name': gen_string('utf8')},
          {u'name': gen_string('alphanumeric'),
           u'os_name': gen_string('alphanumeric')})
    def test_positive_create_arch_with_os(self, test_data):
        """@Test: Create a new Architecture with OS

        @Feature: Architecture - Positive Create

        @Assert: Architecture is created

        """
        entities.OperatingSystem(name=test_data['os_name']).create()
        with Session(self.browser) as session:
            make_arch(session, name=test_data['name'],
                      os_names=[test_data['os_name']])
            self.assertIsNotNone(self.architecture.search(test_data['name']))

    @data(*generate_strings_list())
    def test_positive_create_arch_with_different_names(self, name):
        """@Test: Create a new Architecture with different data

        @Feature: Architecture - Positive Create

        @Assert: Architecture is created

        """
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.search(name))

    @data(*invalid_values_list())
    def test_negative_create_arch(self, name):
        """@Test: Try to create architecture and use whitespace, blank, tab
        symbol or too long string of different types as its name value

        @Feature: Architecture - Negative Create

        @Assert: Architecture is not created

        """
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.wait_until_element
                                 (common_locators['name_haserror']))

    @data(*generate_strings_list())
    def test_negative_create_arch_with_same_name(self, name):
        """@Test: Create a new Architecture with same name

        @Feature: Architecture - Negative Create

        @Assert: Architecture is not created

        """
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.search(name))
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.wait_until_element
                                 (common_locators['name_haserror']))

    @data(*generate_strings_list())
    def test_remove_architecture(self, name):
        """@Test: Delete an existing Architecture

        @Feature: Architecture - Delete

        @Assert: Architecture is deleted

        """
        os = entities.OperatingSystem(name=gen_string('alpha')).create()
        entities.Architecture(name=name, operatingsystem=[os]).create()
        with Session(self.browser) as session:
            session.nav.go_to_architectures()
            self.architecture.delete(name)

    @data(*generate_strings_list())
    def test_update_arch(self, name):
        """@Test: Update Architecture with new name and OS

        @Feature: Architecture - Update

        @Assert: Architecture is updated

        """
        old_name = gen_string('alpha')
        os_name = gen_string('alpha')
        entities.OperatingSystem(name=os_name).create()
        with Session(self.browser) as session:
            make_arch(session, name=old_name)
            self.assertIsNotNone(self.architecture.search(old_name))
            self.architecture.update(old_name, name, new_os_names=[os_name])
            self.assertIsNotNone(self.architecture.search(name))
