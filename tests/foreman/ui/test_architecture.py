# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Architecture UI"""
from ddt import ddt
from fauxfactory import FauxFactory
from robottelo import entities
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

    org_name = None
    loc_name = None
    org_id = None
    loc_id = None

    def setUp(self):
        super(Architecture, self).setUp()
        #  Make sure to use the Class' org_name instance
        if Architecture.org_name is None and Architecture.loc_name is None:
            org_name = FauxFactory.generate_string("alpha", 8)
            loc_name = FauxFactory.generate_string("alpha", 8)
            org_attrs = entities.Organization(name=org_name).create()
            loc_attrs = entities.Location(name=loc_name).create()
            Architecture.org_name = org_attrs['name']
            Architecture.org_id = org_attrs['id']
            Architecture.loc_name = loc_attrs['name']
            Architecture.loc_id = loc_attrs['id']

    @data({u'name': FauxFactory.generate_string('alpha', 10),
           u'os_name': FauxFactory.generate_string('alpha', 10)},
          {u'name': FauxFactory.generate_string('html', 10),
           u'os_name': FauxFactory.generate_string('html', 10)},
          {u'name': FauxFactory.generate_string('utf8', 10),
           u'os_name': FauxFactory.generate_string('utf8', 10)},
          {u'name': FauxFactory.generate_string('alphanumeric', 255),
           u'os_name': FauxFactory.generate_string('alphanumeric', 255)})
    def test_positive_create_arch_1(self, test_data):
        """@Test: Create a new Architecture with OS

        @Feature: Architecture - Positive Create

        @Assert: Architecture is created

        """
        entities.OperatingSystem(name=test_data['os_name']).create()
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
            self.assertIsNone(self.architecture.search(name))

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
    @data({u'name': FauxFactory.generate_string('alpha', 10),
           u'os_name': FauxFactory.generate_string('alpha', 10)},
          {u'name': FauxFactory.generate_string('html', 10),
           u'os_name': FauxFactory.generate_string('html', 10)},
          {u'name': FauxFactory.generate_string('utf8', 10),
           u'os_name': FauxFactory.generate_string('utf8', 10)},
          {u'name': FauxFactory.generate_string('alphanumeric', 255),
           u'os_name': FauxFactory.generate_string('alphanumeric', 255)})
    def test_remove_arch(self, test_data):
        """@Test: Delete an existing Architecture

        @Feature: Architecture - Delete

        @Assert: Architecture is deleted

        @BZ: 1131815

        """

        entities.OperatingSystem(name=test_data['os_name']).create()
        with Session(self.browser) as session:
            make_arch(session, name=test_data['name'],
                      os_names=[test_data['os_name']])
            self.assertIsNotNone(self.architecture.search(test_data['name']))
            self.architecture.delete(test_data['name'], True)
            self.assertIsNone(self.architecture.search(test_data['name']))

    @skip_if_bug_open('bugzilla', 1123388)
    @data({u'old_name': FauxFactory.generate_string('alpha', 10),
           u'new_name': FauxFactory.generate_string('alpha', 10),
           u'os_name': FauxFactory.generate_string('alpha', 10)},
          {u'old_name': FauxFactory.generate_string('html', 10),
           u'new_name': FauxFactory.generate_string('html', 10),
           u'os_name': FauxFactory.generate_string('html', 10)},
          {u'old_name': FauxFactory.generate_string('utf8', 10),
           u'new_name': FauxFactory.generate_string('utf8', 10),
           u'os_name': FauxFactory.generate_string('utf8', 10)},
          {u'old_name': FauxFactory.generate_string('alphanumeric', 255),
           u'new_name': FauxFactory.generate_string('alphanumeric', 255),
           u'os_name': FauxFactory.generate_string('alphanumeric', 255)})
    def test_update_arch(self, test_data):
        """@Test: Update Architecture with new name and OS

        @Feature: Architecture - Update

        @Assert: Architecture is updated

        """
        entities.OperatingSystem(name=test_data['os_name']).create()
        with Session(self.browser) as session:
            make_arch(session, name=test_data['old_name'])
            self.assertIsNotNone(self.architecture.search
                                 (test_data['old_name']))
            self.architecture.update(test_data['old_name'],
                                     test_data['new_name'],
                                     new_os_names=[test_data['os_name']])
            self.assertIsNotNone(self.architecture.search
                                 (test_data['new_name']))
