# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Setting Parameter values
"""

from ddt import ddt
from robottelo.common.decorators import data, skip_if_bug_open
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

    @skip_if_bug_open('bugzilla', 1125181)
    @data({u'param_value': generate_string("latin1", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("utf8", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("alpha", 10) + "@somemail.com"},
          {u'param_value': generate_string("html", 10) + "@somemail.com"},
          {u'param_value': generate_string("alphanumeric", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("numeric", 10) + "@somemail.com"},
          {u'param_value': generate_string("alphanumeric", 50) + "@somem.com"})
    def test_positive_update_general_param_2(self, test_data):
        """
        @Test: Updates param "administrator" under General tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        @BZ: 1125181
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

    @skip_if_bug_open('bugzilla', 1125156)
    @data({u'param_value': " "},
          {u'param_value': "-1"},
          {u'param_value': "text"},
          {u'param_value': "0"})
    def test_negative_update_general_param_4(self, test_data):
        """
        @Test: Updates param "entries_per_page"
        under General tab with invalid values
        @Feature: Settings - Negative Update Parameters
        @Assert: Parameter is not updated
        @BZ: 1125156
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

    @skip_if_bug_open('bugzilla', 1125181)
    @data({u'param_value': generate_string("latin1", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("utf8", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("alpha", 10) + "@somemail.com"},
          {u'param_value': generate_string("html", 10) + "@somemail.com"},
          {u'param_value': generate_string("alphanumeric", 10) +
           "@somemail.com"},
          {u'param_value': generate_string("numeric", 10) + "@somemail.com"},
          {u'param_value': generate_string("alphanumeric", 50) + "@somem.com"})
    def test_positive_update_general_param_6(self, test_data):
        """
        @Test: Updates param "email_reply_address" under General tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        @BZ: 1125181
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

    @skip_if_bug_open('bugzilla', 1125156)
    @data({u'param_value': " "},
          {u'param_value': "-1"},
          {u'param_value': "text"},
          {u'param_value': "0"})
    def test_negative_update_general_param_9(self, test_data):
        """
        @Test: Updates param "max_trend"
        under General tab with invalid values
        @Feature: Settings - Negative Update Parameters
        @Assert: Parameter is not updated
        @BZ: 1125156
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

    @data({'param_value': generate_string("numeric", 2)},
          {'param_value': generate_string("numeric", 5)})
    def test_positive_update_general_param_10(self, test_data):
        """
        @Test: Updates param "max_trend"
        under General tab
        @Feature: Settings - Positive Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "max_trend"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @skip_if_bug_open('bugzilla', 1125156)
    @data({u'param_value': " "},
          {u'param_value': "-1"},
          {u'param_value': "text"},
          {u'param_value': "0"})
    def test_negative_update_general_param_11(self, test_data):
        """
        @Test: Updates param "idle_timeout"
        under General tab with invalid values
        @Feature: Settings - Negative Update Parameters
        @Assert: Parameter is not updated
        @BZ: 1125156
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

    @data({'param_value': generate_string("numeric", 1)},
          {'param_value': generate_string("numeric", 5)})
    def test_positive_update_general_param_12(self, test_data):
        """
        @Test: Updates param "idle_timeout"
        under General tab
        @Feature: Settings - Positive Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_general"]
        param_name = "idle_timeout"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @data({u'param_value': "http://" + generate_string("alpha", 10) +
           ".dom.com"},
          {u'param_value': "https://" + generate_string("alphanumeric", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("numeric", 10) +
           ".dom.com"})
    def test_positive_update_general_param_13(self, test_data):
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

    @skip_if_bug_open('bugzilla', 1125156)
    @data({u'param_value': "http://\\" + generate_string("alpha", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("utf8", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("latin1", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("html", 10) +
           ".dom.com"},
          {u'param_value': " "})
    def test_negative_update_general_param_14(self, test_data):
        """
        @Test: Updates param "foreman_url" under General tab
        @Feature: Settings - Negative update Parameters
        @Assert: Parameter is not updated
        @BZ: 1125156
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

    @data({u'param_value': "true"},
          {u'param_value': "false"})
    def test_positive_update_foremantasks_param_15(self, test_data):
        """
        @Test: Updates param "dynflow_enable_console"
        under ForemanTasks tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_foremantasks"]
        param_name = "dynflow_enable_console"
        value_type = "dropdown"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @data({u'param_value': generate_string("latin1", 10)},
          {u'param_value': generate_string("utf8", 10)},
          {u'param_value': generate_string("alpha", 10)},
          {u'param_value': generate_string("alphanumeric", 10)},
          {u'param_value': generate_string("numeric", 10)})
    def test_positive_update_auth_param_16(self, test_data):
        """
        @Test: Updates param
        "authorize_login_delegation_auth_source_user_autocreate"
        under Auth tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_auth"]
        param_name = "authorize_login_delegation_auth_source_user_autocreate"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @data({u'param_value': "http://" + generate_string("alpha", 10) +
           ".dom.com"},
          {u'param_value': "https://" + generate_string("alphanumeric", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("numeric", 10) +
           ".dom.com"})
    def test_positive_update_auth_param_17(self, test_data):
        """
        @Test: Updates param "login_delegation_logout_url" under Auth tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_auth"]
        param_name = "login_delegation_logout_url"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @data({u'param_name': "oauth_active"},
          {u'param_name': "oauth_consumer_key"},
          {u'param_name': "oauth_consumer_secret"},
          {u'param_name': "oauth_map_users"})
    def test_positive_update_auth_param_18(self, test_data):
        """
        @Test: Read-only param "oauth_active"
        under Auth tab shouldn't be updated
        @Feature: Settings - Update Parameters
        @Assert: Parameter is not editable
        """

        tab_locator = tab_locators["settings.tab_auth"]
        with Session(self.browser) as session:
            with self.assertRaises(Exception) as context:
                edit_param(session, tab_locator=tab_locator,
                           param_name=test_data['param_name'])
            self.assertEqual(context.exception.message,
                             "Couldn't find edit button to update "
                             "selected param")

    @data({u'param_value': "true"},
          {u'param_value': "false"})
    def test_positive_update_auth_param_19(self, test_data):
        """
        @Test: Updates param "require_ssl_puppetmasters"
        under Auth tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_auth"]
        param_name = "require_ssl_puppetmasters"
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
    def test_positive_update_auth_param_20(self, test_data):
        """
        @Test: Updates param "restrict_registered_puppetmasters"
        under Auth tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_auth"]
        param_name = "restrict_registered_puppetmasters"
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
    def test_positive_update_auth_param_21(self, test_data):
        """
        @Test: Updates param "signo_sso"
        under Auth tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_auth"]
        param_name = "signo_sso"
        value_type = "dropdown"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @data({u'param_value': "http://" + generate_string("alpha", 10) +
           ".dom.com"},
          {u'param_value': "https://" + generate_string("alphanumeric", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("numeric", 10) +
           ".dom.com"})
    def test_positive_update_auth_param_22(self, test_data):
        """
        @Test: Updates param "signo_url" under Auth tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_auth"]
        param_name = "signo_url"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @skip_if_bug_open('bugzilla', 1125156)
    @data({u'param_value': "http://\\" + generate_string("alpha", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("utf8", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("latin1", 10) +
           ".dom.com"},
          {u'param_value': "http://" + generate_string("html", 10) +
           ".dom.com"})
    def test_negative_update_auth_param_23(self, test_data):
        """
        @Test: Updates param "signo_url" under Auth tab
        @Feature: Settings - Negative update Parameters
        @Assert: Parameter is not updated
        @BZ: 1125156
        """

        tab_locator = tab_locators["settings.tab_auth"]
        param_name = "signo_url"
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

    @data({u'param_value': "[ " + generate_string("utf8", 10) + " ]"},
          {u'param_value': "[ " + generate_string("alphanumeric", 10) + " ]"},
          {u'param_value': "[ " + generate_string("numeric", 10) + " ]"})
    def test_positive_update_auth_param_24(self, test_data):
        """
        @Test: Updates param
        "trusted_puppetmaster_hosts"
        under Auth tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_auth"]
        param_name = "trusted_puppetmaster_hosts"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @skip_if_bug_open('bugzilla', 1125156)
    @data({u'param_value': " "},
          {u'param_value': "-1"},
          {u'param_value': "text"},
          {u'param_value': "0"})
    def test_negative_update_auth_param_25(self, test_data):
        """
        @Test: Updates param "trusted_puppetmaster_hosts" under Auth tab
        @Feature: Settings - Negative update Parameters
        @Assert: Parameter is not updated
        @BZ: 1125156
        """

        tab_locator = tab_locators["settings.tab_auth"]
        param_name = "trusted_puppetmaster_hosts"
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

    @data({u'param_value': "true"},
          {u'param_value': "false"})
    def test_positive_update_provisioning_param_26(self, test_data):
        """
        @Test: Updates param "ignore_puppet_facts_for_provisioning"
        under Provisioning tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_provisioning"]
        param_name = "ignore_puppet_facts_for_provisioning"
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
    def test_positive_update_provisioning_param_27(self, test_data):
        """
        @Test: Updates param "ignore_puppet_facts_for_provisioning"
        under Provisioning tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_provisioning"]
        param_name = "ignore_puppet_facts_for_provisioning"
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
    def test_positive_update_provisioning_param_28(self, test_data):
        """
        @Test: Updates param "manage_puppetca"
        under Provisioning tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_provisioning"]
        param_name = "manage_puppetca"
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
    def test_positive_update_provisioning_param_29(self, test_data):
        """
        @Test: Updates param "query_local_nameservers"
        under Provisioning tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_provisioning"]
        param_name = "query_local_nameservers"
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
    def test_positive_update_provisioning_param_30(self, test_data):
        """
        @Test: Updates param "safemode_render"
        under Provisioning tab
        @Feature: Settings - Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_provisioning"]
        param_name = "safemode_render"
        value_type = "dropdown"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)

    @skip_if_bug_open('bugzilla', 1125156)
    @data({u'param_value': " "},
          {u'param_value': "-1"},
          {u'param_value': "text"})
    def test_negative_update_provisioning_param_31(self, test_data):
        """
        @Test: Updates param "token_duration"
        under Provisioning tab with invalid values
        @Feature: Settings - Negative Update Parameters
        @Assert: Parameter is not updated
        @BZ: 1125156
        """

        tab_locator = tab_locators["settings.tab_provisioning"]
        param_name = "token_duration"
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

    @data({'param_value': generate_string("numeric", 1)},
          {'param_value': "0"})
    def test_positive_update_provisioning_param_32(self, test_data):
        """
        @Test: Updates param "token_duration"
        under Provisioning tab
        @Feature: Settings - Positive Update Parameters
        @Assert: Parameter is updated
        """

        tab_locator = tab_locators["settings.tab_provisioning"]
        param_name = "token_duration"
        value_type = "input"
        with Session(self.browser) as session:
            edit_param(session, tab_locator=tab_locator,
                       param_name=param_name,
                       value_type=value_type,
                       param_value=test_data['param_value'])
            saved_element = self.settings.get_saved_value(tab_locator,
                                                          param_name)
            self.assertEqual(test_data['param_value'], saved_element)
