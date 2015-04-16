# -*- encoding: utf-8 -*-
"""Test class for Architecture UI"""
from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.helpers import generate_strings_list
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
    def test_positive_create_arch_1(self, test_data):
        """@Test: Create a new Architecture with OS

        @Feature: Architecture - Positive Create

        @Assert: Architecture is created

        """
        entities.OperatingSystem(name=test_data['os_name']).create_json()
        with Session(self.browser) as session:
            make_arch(session, name=test_data['name'],
                      os_names=[test_data['os_name']])
            self.assertIsNotNone(self.architecture.search(test_data['name']))

    @data(*generate_strings_list(len1=8))
    def test_positive_create_arch_2(self, name):
        """@Test: Create a new Architecture with different data

        @Feature: Architecture - Positive Create

        @Assert: Architecture is created

        """
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.search(name))

    @data(*generate_strings_list(len1=256))
    def test_negative_create_arch_1(self, name):
        """@Test: Create a new Architecture with 256 characters in name

        @Feature: Architecture - Negative Create

        @Assert: Architecture is not created

        """
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.wait_until_element
                                 (common_locators["name_haserror"]))

    @data("", "  ")
    def test_negative_create_arch_2(self, name):
        """@Test: Create a new Architecture with whitespace in name

        @Feature: Architecture - Negative Create

        @Assert: Architecture is not created

        """
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.wait_until_element
                                 (common_locators["name_haserror"]))

    @data(*generate_strings_list(len1=6))
    def test_negative_create_arch_4(self, name):
        """@Test: Create a new Architecture with same name

        @Feature: Architecture - Negative Create

        @Assert: Architecture is not created

        """
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.search(name))
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.wait_until_element
                                 (common_locators["name_haserror"]))

    @skip_if_bug_open('bugzilla', 1123388)
    @data({u'name': gen_string('alpha'),
           u'os_name': gen_string('alpha')},
          {u'name': gen_string('html'),
           u'os_name': gen_string('html')},
          {u'name': gen_string('utf8'),
           u'os_name': gen_string('utf8')},
          {u'name': gen_string('alphanumeric'),
           u'os_name': gen_string('alphanumeric')})
    def test_remove_arch(self, test_data):
        """@Test: Delete an existing Architecture

        @Feature: Architecture - Delete

        @Assert: Architecture is deleted

        @BZ: 1131815

        """
        entities.OperatingSystem(name=test_data['os_name']).create_json()
        with Session(self.browser) as session:
            make_arch(session, name=test_data['name'],
                      os_names=[test_data['os_name']])
            self.assertIsNotNone(self.architecture.search(test_data['name']))
            self.architecture.delete(test_data['name'], True)
            self.assertIsNone(self.architecture.search(test_data['name']))

    @skip_if_bug_open('bugzilla', 1123388)
    @data({u'old_name': gen_string('alpha'),
           u'new_name': gen_string('alpha'),
           u'os_name': gen_string('alpha')},
          {u'old_name': gen_string('html'),
           u'new_name': gen_string('html'),
           u'os_name': gen_string('html')},
          {u'old_name': gen_string('utf8'),
           u'new_name': gen_string('utf8'),
           u'os_name': gen_string('utf8')},
          {u'old_name': gen_string('alphanumeric'),
           u'new_name': gen_string('alphanumeric'),
           u'os_name': gen_string('alphanumeric')})
    def test_update_arch(self, test_data):
        """@Test: Update Architecture with new name and OS

        @Feature: Architecture - Update

        @Assert: Architecture is updated

        """
        entities.OperatingSystem(name=test_data['os_name']).create_json()
        with Session(self.browser) as session:
            make_arch(session, name=test_data['old_name'])
            self.assertIsNotNone(self.architecture.search
                                 (test_data['old_name']))
            self.architecture.update(test_data['old_name'],
                                     test_data['new_name'],
                                     new_os_names=[test_data['os_name']])
            self.assertIsNotNone(self.architecture.search
                                 (test_data['new_name']))
