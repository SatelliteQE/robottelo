# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Architecture UI
"""
from ddt import ddt
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.common.helpers import (generate_string,
                                      generate_strings_list)
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_org, make_loc,
                                  make_os, make_arch)
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class Architecture(UITestCase):
    """
    Implements Architecture tests from UI
    """

    org_name = None
    loc_name = None

    def setUp(self):
        super(Architecture, self).setUp()
        #  Make sure to use the Class' org_name instance
        if (Architecture.org_name is None and Architecture.loc_name is None):
            Architecture.org_name = generate_string("alpha", 8)
            Architecture.loc_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=Architecture.org_name)
                make_loc(session, name=Architecture.loc_name)

    @data({u'name': generate_string('alpha', 10),
           u'os_name': generate_string('alpha', 10),
           u'major_version': generate_string('numeric', 1)},
          {u'name': generate_string('html', 10),
           u'os_name': generate_string('html', 10),
           u'major_version': generate_string('numeric', 4)},
          {u'name': generate_string('utf8', 10),
           u'os_name': generate_string('utf8', 10),
           u'major_version': generate_string('numeric', 5)},
          {u'name': generate_string('alphanumeric', 255),
           u'os_name': generate_string('alphanumeric', 255),
           u'major_version': generate_string('numeric', 5)})
    def test_positive_create_arch_1(self, test_data):
        """
        @Test: Create a new Architecture with OS
        @Feature: Architecture - Positive Create
        @Assert: Architecture is created
        """

        with Session(self.browser) as session:
            make_os(session, name=test_data['os_name'],
                    major_version=test_data['major_version'])
            self.assertIsNotNone(self.operatingsys.search
                                 (test_data['os_name']))
            make_arch(session, name=test_data['name'],
                      os_names=[test_data['os_name']])
            self.assertIsNotNone(self.architecture.search(test_data['name']))

    @data(*generate_strings_list(len1=8))
    def test_positive_create_arch_2(self, name):
        """
        @Test: Create a new Architecture with different data
        @Feature: Architecture - Positive Create
        @Assert: Architecture is created
        """
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.search(name))

    @data(*generate_strings_list(len1=256))
    def test_negative_create_arch_1(self, name):
        """
        @Test: Create a new Architecture with 256 characters in name
        @Feature: Architecture - Negative Create
        @Assert: Architecture is not created
        """

        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.wait_until_element
                                 (common_locators["name_haserror"]))
            self.assertIsNone(self.architecture.search(name))

    def test_negative_create_arch_2(self):
        """
        @Test: Create a new Architecture with whitespace in name
        @Feature: Architecture - Negative Create
        @Assert: Architecture is not created
        """
        name = " "
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.wait_until_element
                                 (common_locators["name_haserror"]))

    def test_negative_create_arch_3(self):
        """
        @Test: Create a new Architecture with blank name
        @Feature: Architecture - Negative Create
        @Assert: Architecture is not created
        """
        name = ""
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.wait_until_element
                                 (common_locators["name_haserror"]))

    @data(*generate_strings_list(len1=6))
    def test_negative_create_arch_4(self, name):
        """
        @Test: Create a new Architecture with same name
        @Feature: Architecture - Negative Create
        @Assert: Architecture is not created
        """

        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.search(name))
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.wait_until_element
                                 (common_locators["name_haserror"]))

    @skip_if_bug_open('bugzilla', 1131815)
    @data({u'name': generate_string('alpha', 10),
           u'os_name': generate_string('alpha', 10),
           u'major_version': generate_string('numeric', 1)},
          {u'name': generate_string('html', 10),
           u'os_name': generate_string('html', 10),
           u'major_version': generate_string('numeric', 4)},
          {u'name': generate_string('utf8', 10),
           u'os_name': generate_string('utf8', 10),
           u'major_version': generate_string('numeric', 5)},
          {u'name': generate_string('alphanumeric', 255),
           u'os_name': generate_string('alphanumeric', 255),
           u'major_version': generate_string('numeric', 5)})
    def test_remove_arch(self, test_data):
        """
        @Test: Delete an existing Architecture
        @Feature: Architecture - Delete
        @Assert: Architecture is deleted
        @BZ: 1131815
        """

        with Session(self.browser) as session:
            make_os(session, name=test_data['os_name'],
                    major_version=test_data['major_version'])
            self.assertIsNotNone(self.operatingsys.search
                                 (test_data['os_name']))
            make_arch(session, name=test_data['name'],
                      os_names=[test_data['os_name']])
            self.assertIsNotNone(self.architecture.search(test_data['name']))
            self.architecture.delete(test_data['name'], True)
            self.assertIsNone(self.architecture.search(test_data['name']))

    @skip_if_bug_open('bugzilla', 1123388)
    @data({u'old_name': generate_string('alpha', 10),
           u'new_name': generate_string('alpha', 10),
           u'os_name': generate_string('alpha', 10),
           u'major_version': generate_string('numeric', 1)},
          {u'old_name': generate_string('html', 10),
           u'new_name': generate_string('html', 10),
           u'os_name': generate_string('html', 10),
           u'major_version': generate_string('numeric', 4)},
          {u'old_name': generate_string('utf8', 10),
           u'new_name': generate_string('utf8', 10),
           u'os_name': generate_string('utf8', 10),
           u'major_version': generate_string('numeric', 5)},
          {u'old_name': generate_string('alphanumeric', 255),
           u'new_name': generate_string('alphanumeric', 255),
           u'os_name': generate_string('alphanumeric', 255),
           u'major_version': generate_string('numeric', 5)})
    def test_update_arch(self, test_data):
        """
        @Test: Update Architecture with new name and OS
        @Feature: Architecture - Update
        @Assert: Architecture is updated
        """

        with Session(self.browser) as session:
            make_os(session, name=test_data['os_name'],
                    major_version=test_data['major_version'])
            self.assertIsNotNone(self.operatingsys.search
                                 (test_data['os_name']))
            make_arch(session, name=test_data['old_name'])
            self.assertIsNotNone(self.architecture.search
                                 (test_data['old_name']))
            self.architecture.update(test_data['old_name'],
                                     test_data['new_name'],
                                     new_os_names=[test_data['os_name']])
            self.assertIsNotNone(self.architecture.search
                                 (test_data['new_name']))
