# -*- encoding: utf-8 -*-
"""Test class for Setting Parameter values"""

from fauxfactory import gen_email, gen_string, gen_url
from robottelo.decorators import run_only_on, skip_if_bug_open, tier1
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import edit_param
from robottelo.ui.locators import common_locators, tab_locators
from robottelo.ui.session import Session


def valid_boolean_values():
    """Returns a list of valid boolean values"""
    return [
        'true',
        'false',
    ]


def valid_settings_values():
    """Returns a list of valid settings values"""
    return [
        gen_email(gen_string('alpha')),
        gen_email(gen_string('alphanumeric')),
        gen_email(gen_string('latin1')),
        gen_email(gen_string('numeric')),
        gen_email(gen_string('utf8')),
        gen_email(gen_string('html')),
        gen_email(gen_string('alphanumeric', 40)),
    ]


def invalid_foreman_urls():
    """Returns a list of invalid foreman urls"""
    return[
        'http://\\' + gen_string('alpha') + '.dom.com',
        'http://' + gen_string('utf8') + '.dom.com',
        'http://' + gen_string('latin1') + '.dom.com',
        'http://' + gen_string('html') + '.dom.com',
        ' '
    ]


def invalid_settings_values():
    """Returns a list of invalid settings values"""
    return [' ', '-1', 'text', '0']


def valid_maxtrend_timeout_values():
    """Returns a list of valid maxtrend, timeout values"""
    return [
        gen_string('numeric', 2),
        gen_string('numeric', 5),
    ]


def valid_urls():
    """Returns a list of valid urls"""
    return [
        gen_url(subdomain=gen_string('alpha')),
        gen_url(subdomain=gen_string('alphanumeric')),
        gen_url(subdomain=gen_string('numeric')),
    ]


def valid_login_delegation_values():
    """Returns a list of valid delegation values"""
    return [
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric')
    ]


def invalid_oauth_active_values():
    """Returns a list of invalid oauth_active values"""
    return [
        'oauth_active',
        'oauth_consumer_key',
        'oauth_consumer_secret',
        'oauth_map_users',
    ]


def valid_trusted_puppetmaster_hosts():
    """Returns a list of valid trusted puppetmaster hosts"""
    return [
        '[ ' + gen_string('utf8') + ' ]',
        '[ ' + gen_string('alphanumeric') + ' ]',
        '[ ' + gen_string('numeric') + ' ]'
    ]


def valid_token_duration():
    """Returns a list of valid token durations"""
    return ['90', '0']


def invalid_token_duration():
    """Returns a list of invalid token durations"""
    return [' ', '-1', 'text']


class SettingTestCase(UITestCase):
    """Implements Boundary tests for Settings menu"""

    @tier1
    def test_positive_update_authorize_login_delegation_param(self):
        """@Test: Updates parameter "authorize_login_delegation" under General
        tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'authorize_login_delegation'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='dropdown',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @skip_if_bug_open('bugzilla', 1125181)
    @tier1
    def test_positive_update_administrator_param(self):
        """@Test: Updates parameter "administrator" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully

        @BZ: 1125181
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'administrator'
        with Session(self.browser) as session:
            for param_value in valid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @tier1
    def test_positive_update_authorize_login_delegation_api_param(self):
        """@Test: Updates parameter "authorize_login_delegation_api" under
        General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'authorize_login_delegation_api'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='dropdown',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @skip_if_bug_open('bugzilla', 1125156)
    @tier1
    def test_negative_update_entries_per_page_param(self):
        """@Test: Updates parameter "entries_per_page" under General tab with
        invalid values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'entries_per_page'
        with Session(self.browser) as session:
            for param_value in invalid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertNotEqual(param_value, saved_element)

    @tier1
    def test_positive_update_entries_per_page_param(self):
        """@Test: Updates parameter "entries_per_page" under General tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated successfully
        """
        param_value = gen_string('numeric', 5)
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'entries_per_page'
        with Session(self.browser) as session:
            self.navigator.go_to_settings()
            original_value = self.settings.get_saved_value(
                tab_locator, param_name)
            try:
                edit_param(
                    session,
                    tab_locator=tab_locator,
                    param_name=param_name,
                    value_type='input',
                    param_value=param_value,
                )
                saved_element = self.settings.get_saved_value(
                    tab_locator, param_name)
                # UI automatically strips leading zeros on save,
                # e.g. If param_value = '01400' then UI saves it as '1400'
                # so using 'lstrip' to strip leading zeros from variable
                # 'param_value' too
                self.assertEqual(param_value.lstrip('0'), saved_element)
            finally:
                # Restore previous value
                edit_param(
                    session,
                    tab_locator=tab_locator,
                    param_name=param_name,
                    value_type='input',
                    param_value=original_value,
                )

    @skip_if_bug_open('bugzilla', 1125181)
    @tier1
    def test_positive_update_email_reply_address_param(self):
        """@Test: Updates parameter "email_reply_address" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully

        @BZ: 1125181
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'email_reply_address'
        with Session(self.browser) as session:
            for param_value in valid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @skip_if_bug_open('bugzilla', 1156195)
    @tier1
    def test_positive_update_fix_db_cache_param(self):
        """@Test: Updates parameter "fix_db_cache" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully

        @BZ: 1156195
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'fix_db_cache'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='dropdown',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @tier1
    def test_positive_update_use_gravatar_param(self):
        """@Test: Updates parameter "use_gravatar" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'use_gravatar'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='dropdown',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @skip_if_bug_open('bugzilla', 1125156)
    @tier1
    def test_negative_update_max_trend_param(self):
        """@Test: Updates parameter "max_trend" under General tab with invalid
        values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'max_trend'
        with Session(self.browser) as session:
            for param_value in invalid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertNotEqual(param_value, saved_element)

    @tier1
    def test_positive_update_max_trend_param(self):
        """@Test: Updates parameter "max_trend" under General tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'max_trend'
        with Session(self.browser) as session:
            for param_value in valid_maxtrend_timeout_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    # UI automatically strips leading zeros on save,
                    # e.g. If param_value = '01400' then UI saves it as '1400'
                    # so using lstrip to strip leading zeros from variable
                    # 'param_value' too
                    self.assertEqual(param_value.lstrip('0'), saved_element)

    @skip_if_bug_open('bugzilla', 1125156)
    @tier1
    def test_negative_update_idle_timeout_param(self):
        """@Test: Updates parameter "idle_timeout" under General tab with
        invalid values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'idle_timeout'
        with Session(self.browser) as session:
            for param_value in invalid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertNotEqual(param_value, saved_element)

    @tier1
    def test_positive_update_idle_timeout_param(self):
        """@Test: Updates parameter "idle_timeout" under General tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'idle_timeout'
        with Session(self.browser) as session:
            for param_value in valid_maxtrend_timeout_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    # UI automatically strips leading zeros on save,
                    # e.g. If param_value = '01400' then UI saves it as '1400'
                    # so using lstrip to strip leading zeros from variable
                    # 'param_value' too
                    self.assertEqual(param_value.lstrip('0'), saved_element)

    @tier1
    def test_positive_update_foreman_url_param(self):
        """@Test: Updates parameter "foreman_url" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'foreman_url'
        with Session(self.browser) as session:
            for param_value in valid_urls():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @skip_if_bug_open('bugzilla', 1125156)
    @tier1
    def test_negative_update_foreman_url_param(self):
        """@Test: Updates parameter "foreman_url" under General tab

        @Feature: Settings - Negative update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156
        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'foreman_url'
        with Session(self.browser) as session:
            for param_value in invalid_foreman_urls():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertNotEqual(param_value, saved_element)

    @tier1
    def test_positive_update_dynflow_enable_console_param(self):
        """@Test: Updates parameter "dynflow_enable_console" under ForemanTasks
        tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_foremantasks']
        param_name = 'dynflow_enable_console'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='dropdown',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @tier1
    def test_positive_update_auth_source_user_autocreate_param(self):
        """@Test: Updates parameter
        "authorize_login_delegation_auth_source_user_autocreate" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'authorize_login_delegation_auth_source_user_autocreate'
        with Session(self.browser) as session:
            for param_value in valid_login_delegation_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @tier1
    def test_positive_update_login_delegation_logout_url_param(self):
        """@Test: Updates parameter "login_delegation_logout_url" under Auth
        tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'login_delegation_logout_url'
        with Session(self.browser) as session:
            for param_value in valid_urls():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @tier1
    def test_positive_update_oauth_active_param(self):
        """@Test: Read-only param "oauth_active" under Auth tab shouldn't be
        updated

        @Feature: Settings - Update Parameters

        @Assert: Parameter is not editable
        """
        tab_locator = tab_locators['settings.tab_auth']
        with Session(self.browser) as session:
            for param_name in invalid_oauth_active_values():
                with self.subTest(param_name):
                    with self.assertRaises(UIError) as context:
                        edit_param(
                            session,
                            tab_locator=tab_locator,
                            param_name=param_name,
                        )
                        self.assertEqual(
                            context.exception.message,
                            'Could not find edit button to update param'
                        )

    @tier1
    def test_positive_update_require_ssl_puppetmasters_param(self):
        """@Test: Updates parameter "require_ssl_puppetmasters" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'require_ssl_puppetmasters'
        value_type = 'dropdown'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    session.nav.go_to_settings()
                    default_value = self.settings.get_saved_value(
                        tab_locator, param_name)
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type=value_type,
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type=value_type,
                        param_value=default_value,
                    )

    @tier1
    def test_positive_update_restrict_registered_puppetmasters_param(self):
        """@Test: Updates parameter "restrict_registered_puppetmasters" under
        Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'restrict_registered_puppetmasters'
        value_type = 'dropdown'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    session.nav.go_to_settings()
                    default_value = self.settings.get_saved_value(
                        tab_locator, param_name)
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type=value_type,
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type=value_type,
                        param_value=default_value,
                    )

    @tier1
    def test_positive_update_trusted_puppetmaster_hosts_param(self):
        """@Test: Updates parameter "trusted_puppetmaster_hosts" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'trusted_puppetmaster_hosts'
        with Session(self.browser) as session:
            for param_value in valid_trusted_puppetmaster_hosts():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @skip_if_bug_open('bugzilla', 1125156)
    @tier1
    def test_negative_update_trusted_puppetmaster_hosts_param(self):
        """@Test: Updates parameter "trusted_puppetmaster_hosts" under Auth tab

        @Feature: Settings - Negative update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156
        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'trusted_puppetmaster_hosts'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertNotEqual(param_value, saved_element)

    @tier1
    def test_positive_update_ignore_puppet_facts_for_provisioning_param(self):
        """@Test: Updates parameter "ignore_puppet_facts_for_provisioning"
        under Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'ignore_puppet_facts_for_provisioning'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='dropdown',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_update_manage_puppetca_param(self):
        """@Test: Updates parameter "manage_puppetca" under Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'manage_puppetca'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='dropdown',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_update_query_local_nameservers_param(self):
        """@Test: Updates parameter "query_local_nameservers" under
        Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'query_local_nameservers'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='dropdown',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_update_safemode_render_param(self):
        """@Test: Updates parameter "safemode_render" under Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'safemode_render'
        with Session(self.browser) as session:
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='dropdown',
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1125156)
    @tier1
    def test_negative_update_token_duration_param(self):
        """@Test: Updates parameter "token_duration" under Provisioning tab
        with invalid values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156
        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'token_duration'
        with Session(self.browser) as session:
            for param_value in invalid_token_duration():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type='input',
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertNotEqual(param_value, saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_update_token_duration_param(self):
        """@Test: Updates param "token_duration" under Provisioning tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated successfully
        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'token_duration'
        value_type = 'input'
        with Session(self.browser) as session:
            for param_value in valid_token_duration():
                with self.subTest(param_value):
                    session.nav.go_to_settings()
                    default_value = self.settings.get_saved_value(
                        tab_locator, param_name)
                    edit_param(
                        session,
                        tab_locator=tab_locator,
                        param_name=param_name,
                        value_type=value_type,
                        param_value=param_value,
                    )
                    saved_element = self.settings.get_saved_value(
                        tab_locator, param_name)
                    self.assertEqual(param_value, saved_element)
                    # This is the time in minutes as for how long installation
                    # token should be valid; '0' value is to disable it
                    # Resetting the token_duration to its default value '60'
                    if saved_element == '0':
                        edit_param(
                            session,
                            tab_locator=tab_locator,
                            param_name=param_name,
                            value_type=value_type,
                            param_value=default_value,
                        )
