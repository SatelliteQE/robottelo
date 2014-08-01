# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Setting Parameter values
"""

from ddt import ddt
from robottelo.common.decorators import data, skip_if_bz_bug_open
from robottelo.common.helpers import generate_string
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_org, make_loc,
                                  edit_param)
from robottelo.ui.locators import tab_locators, common_locators
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

    @skip_if_bz_bug_open(1125156)
    @data({u'param_value': " "},
          {u'param_value': "-1"},
          {u'param_value': "text"},
          {u'param_value': "0"})
    def test_negative_update_general_param_4(self, test_data):
        """
        @Test: Updates param "entries_per_page"
        under General tab with negative values
        @Feature: Settings - Negative Update Parameters
        @Assert: Parameter is not updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "entries_per_page"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            self.assertIsNotNone(session.nav.wait_until_element
                                 (common_locators["notif.error"]))
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertNotEqual(test_data['param_value'], saved_element)

    def test_positive_update_general_param_5(self):
        """
        @Test: Updates param "entries_per_page"
        under General tab
        @Feature: Settings - Positive Update Parameters
        @Assert: Parameter is updated
        """
        param_value = generate_string("numeric", 5)
        tab_locator = tab_locators["settings.tab_general"]
        param_name = "entries_per_page"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type, param_value=param_value)
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(param_value, saved_element)

    @data({u'param_value': generate_string("latin1", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("utf8", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("alpha", 10) + "@somemail.com"},
          {u'param_value': generate_string("alphanumeric", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("numeric", 10) + "@somemail.com"},
          {u'param_value': generate_string("alphanumeric", 50) + "@somem.com"})
    def test_positive_update_general_param_6(self, test_data):
        """
        @Test: Updates param "email_reply_address" under General tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "email_reply_address"
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
    def test_positive_update_general_param_7(self, test_data):
        """
        @Test: Updates param "fix_db_cache"
        under General tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "fix_db_cache"
        value_type = "dropdown"
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
    def test_positive_update_general_param_8(self, test_data):
        """
        @Test: Updates param "use_gravatar"
        under General tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "use_gravatar"
        value_type = "dropdown"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @skip_if_bz_bug_open(1125156)
    @data({u'param_value': " "},
          {u'param_value': "-1"},
          {u'param_value': "text"},
          {u'param_value': "0"})
    def test_negative_update_general_param_9(self, test_data):
        """
        @Test: Updates param "max_trend"
        under General tab with negative values
        @Feature: Settings - Negative Update Parameters
        @Assert: Parameter is not updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "max_trend"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            self.assertIsNotNone(session.nav.wait_until_element
                                 (common_locators["notif.error"]))
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertNotEqual(test_data['param_value'], saved_element)

    @skip_if_bz_bug_open(1125156)
    @data({u'param_value': " "},
          {u'param_value': "-1"},
          {u'param_value': "text"},
          {u'param_value': "0"})
    def test_negative_update_general_param_10(self, test_data):
        """
        @Test: Updates param "idle_timeout"
        under General tab with negative values
        @Feature: Settings - Negative Update Parameters
        @Assert: Parameter is not updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "idle_timeout"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            self.assertIsNotNone(session.nav.wait_until_element
                                 (common_locators["notif.error"]))
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertNotEqual(test_data['param_value'], saved_element)

    @data({u'param_value': "http://" + generate_string("alpha", 10) +
           ".dom.com"},
          {u'param_value': "https://" + generate_string("alphanumeric", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("numeric", 10) +
           ".dom.com"})
    def test_positive_update_general_param_11(self, test_data):
        """
        @Test: Updates param "foreman_url" under General tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "foreman_url"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @data({u'param_value': "http://\\" + generate_string("alpha", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("utf8", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("latin1", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("html", 10) +
           ".dom.com"},
          {u'param_value': " "})
    def test_negative_update_general_param_12(self, test_data):
        """
        @Test: Updates param "foreman_url" under General tab
        @Feature: Settings - Negative update Parameters
        @Assert: Parameter is not updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "foreman_url"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            self.assertIsNotNone(session.nav.wait_until_element
                                 (common_locators["notif.error"]))
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertNotEqual(test_data['param_value'], saved_element)
