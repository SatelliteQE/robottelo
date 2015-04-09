# -*- encoding: utf-8 -*-
"""Test class for Host Group UI"""

from ddt import ddt
from ddt import data as ddt_data
from fauxfactory import gen_string
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.helpers import generate_strings_list
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

    @skip_if_bug_open('bugzilla', 1121755)
    @skip_if_bug_open('bugzilla', 1131416)
    @data(*generate_strings_list(len1=4))
    def test_delete_hostgroup(self, name):
        """@Test: Delete a hostgroup

        @Feature: Hostgroup - Positive Delete

        @Assert: Hostgroup is deleted

        """
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            self.hostgroup.delete(name, really=True)
            self.assertIsNone(self.hostgroup.search(name))

    @data({u'name': gen_string('alpha'),
           u'new_name': gen_string('alpha')},
          {u'name': gen_string('latin1'),
           u'new_name': gen_string('latin1')},
          {u'name': gen_string('numeric'),
           u'new_name': gen_string('numeric')},
          {u'name': gen_string('html'),
           u'new_name': gen_string('html')},
          {u'name': gen_string('utf8'),
           u'new_name': gen_string('utf8')},
          {u'name': gen_string('alphanumeric'),
           u'new_name': gen_string('alphanumeric')})
    def test_update_hostgroup(self, test_data):
        """@Test: Update hostgroup with a new name

        @Feature: Hostgroup - Positive Update

        @Assert: Hostgroup is updated

        """
        with Session(self.browser) as session:
            make_hostgroup(session, name=test_data['name'])
            self.assertIsNotNone(self.hostgroup.search(test_data['name']))
            self.hostgroup.update(test_data['name'],
                                  new_name=test_data['new_name'])
            self.assertIsNotNone(self.hostgroup.search(test_data['new_name']))

    @data(*generate_strings_list(len1=256))
    def test_negative_create_hostgroup_1(self, name):
        """@Test: Create new hostgroup with 256 chars in name

        @Feature: Hostgroup - Negative Create

        @Assert: Hostgroup is not created

        """
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.wait_until_element
                                 (common_locators["name_haserror"]))

    @data(*generate_strings_list(len1=6))
    def test_negative_create_hostgroup_2(self, name):
        """@Test: Create new hostgroup with same name

        @Feature: Hostgroup - Negative Create

        @Assert: Hostgroup is not created

        """
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.wait_until_element
                                 (common_locators["name_haserror"]))

    @ddt_data("", "  ")
    def test_negative_create_hostgroup_3(self, name):
        """@Test: Create new hostgroup with whitespaces in name

        @Feature: Hostgroup - Negative Create

        @Assert: Hostgroup is not created

        """
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.wait_until_element
                                 (common_locators["name_haserror"]))
