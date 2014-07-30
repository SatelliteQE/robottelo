# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Setting Parameter values
"""

from ddt import ddt
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_org, make_loc,
                                  edit_param)
from robottelo.ui.locators import tab_locators
from robottelo.ui.session import Session


@ddt
class Settings(UITestCase):
    """
    Implements Boundary tests for Settings menu
    """

    org_name = None
    loc_name = None

    def setUp(self):
        super(Settings, self).setUp()
        #  Make sure to use the Class' org_name instance
        if (Settings.org_name is None and Settings.loc_name is None):
            Settings.org_name = generate_string("alpha", 8)
            Settings.loc_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=Settings.org_name)
                make_loc(session, name=Settings.loc_name)

    @data({u'param_value': "true"},
          {u'param_value': "false"})
    def test_positive_update_general_param_1(self, test_data):
        """
        @Test: Updates param "authorize_login_delegation"
        under General tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "authorize_login_delegation"
        value_type = "dropdown"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @data({u'param_value': generate_string("latin1", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("utf8", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("alpha", 10) + "@somemail.com"},
          {u'param_value': generate_string("alphanumeric", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("numeric", 10) + "@somemail.com"},
          {u'param_value': generate_string("alphanumeric", 50) + "@somem.com"})
    def test_positive_update_general_param_2(self, test_data):
        """
        @Test: Updates param "administrator" under General tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "administrator"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @data({u'param_value': "true"},
          {u'param_value': "false"})
    def test_positive_update_general_param_3(self, test_data):
        """
        @Test: Updates param "authorize_login_delegation_api"
        under General tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "authorize_login_delegation_api"
        value_type = "dropdown"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)
