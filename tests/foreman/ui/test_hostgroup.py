# -*- encoding: utf-8 -*-
"""Test class for Host Group UI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.decorators import data, run_only_on
from robottelo.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_hostgroup
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class Hostgroup(UITestCase):
    """Implements HostGroup tests from UI"""

    @data(*generate_strings_list(len1=4))
    def test_create_hostgroup(self, name):
        """@Test: Create new hostgroup

        @Feature: Hostgroup - Positive Create

        @Assert: Hostgroup is created

        """
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))

    @data(*generate_strings_list(len1=4))
    def test_delete_hostgroup(self, name):
        """@Test: Delete a hostgroup

        @Feature: Hostgroup - Positive Delete

        @Assert: Hostgroup is deleted

        """
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.hostgroup.delete(name)

    @data(*generate_strings_list(len1=4))
    def test_update_hostgroup(self, new_name):
        """@Test: Update hostgroup with a new name

        @Feature: Hostgroup - Positive Update

        @Assert: Hostgroup is updated

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            self.hostgroup.update(name, new_name=new_name)
            self.assertIsNotNone(self.hostgroup.search(new_name))

    @data(*generate_strings_list(len1=256))
    def test_negative_create_hostgroup_with_too_long_name(self, name):
        """@Test: Create new hostgroup with 256 chars in name

        @Feature: Hostgroup - Negative Create

        @Assert: Hostgroup is not created

        """
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.wait_until_element
                                 (common_locators['name_haserror']))

    def test_negative_create_hostgroup_with_same_name(self):
        """@Test: Create new hostgroup with same name

        @Feature: Hostgroup - Negative Create

        @Assert: Hostgroup is not created

        """
        name = gen_string('utf8')
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.wait_until_element
                                 (common_locators['name_haserror']))

    @data('', '  ')
    def test_negative_create_hostgroup_with_blank_name(self, name):
        """@Test: Create new hostgroup with whitespaces in name

        @Feature: Hostgroup - Negative Create

        @Assert: Hostgroup is not created

        """
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.wait_until_element
                                 (common_locators['name_haserror']))
