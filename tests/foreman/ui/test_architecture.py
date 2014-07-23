# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Architecture UI
"""
from ddt import ddt
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string, valid_names_list
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

    def test_positive_create_arch_1(self):
        """
        @Test: Create a new Architecture with OS
        @Feature: Architecture - Positive Create
        @Assert: Architecture is created
        """
        name = generate_string("alpha", 4)
        os_name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        with Session(self.browser) as session:
            make_os(session, name=os_name,
                    major_version=major_version)
            self.assertIsNotNone(self.operatingsys.search(os_name))
            make_arch(session, name=name, os_names=[os_name])
            self.assertIsNotNone(self.architecture.search(name))

    @data(*valid_names_list())
    def test_positive_create_arch_2(self, name):
        """
        @Test: Create a new Architecture with different data
        @Feature: Architecture - Positive Create
        @Assert: Architecture is created
        """
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.search(name))

    def test_negative_create_arch_1(self):
        """
        @Test: Create a new Architecture with 256 characters in name
        @Feature: Architecture - Negative Create
        @Assert: Architecture is not created
        """
        name = generate_string("alpha", 256)
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.wait_until_element
                                 (common_locators["alert.error"]))
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

    def test_negative_create_arch_4(self):
        """
        @Test: Create a new Architecture with same name
        @Feature: Architecture - Negative Create
        @Assert: Architecture is not created
        """
        name = generate_string("alpha", 4)
        with Session(self.browser) as session:
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.search(name))
            make_arch(session, name=name)
            self.assertIsNotNone(self.architecture.wait_until_element
                                 (common_locators["name_haserror"]))

    def test_remove_arch(self):
        """
        @Test: Delete an existing Architecture
        @Feature: Architecture - Delete
        @Assert: Architecture is deleted
        """

        name = generate_string("alpha", 4)
        os_name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        with Session(self.browser) as session:
            make_os(session, name=os_name,
                    major_version=major_version)
            self.assertIsNotNone(self.operatingsys.search(os_name))
            make_arch(session, name=name, os_names=[os_name])
            self.assertIsNotNone(self.architecture.search(name))
            self.architecture.delete(name, True)
            self.assertIsNone(self.architecture.search(name))

    def test_update_arch(self):
        """
        @Test: Update Architecture with new name and OS
        @Feature: Architecture - Update
        @Assert: Architecture is updated
        """

        old_name = generate_string("alpha", 6)
        new_name = generate_string("alpha", 4)
        os_name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        with Session(self.browser) as session:
            make_os(session, name=os_name,
                    major_version=major_version)
            self.assertIsNotNone(self.operatingsys.search(os_name))
            make_arch(session, name=old_name)
            self.assertIsNotNone(self.architecture.search(old_name))
            self.architecture.update(old_name, new_name,
                                     new_os_names=[os_name])
            self.assertIsNotNone(self.architecture.search(new_name))
