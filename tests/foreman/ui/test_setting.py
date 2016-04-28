# -*- encoding: utf-8 -*-
"""Test class for Setting Parameter values"""

from fauxfactory import gen_email, gen_string, gen_url
from random import choice, randint
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
        str(randint(10, 99)),
        str(randint(10000, 99999)),
    ]


def valid_urls():
    """Returns a list of valid urls"""
    return [
        gen_url(
            scheme=choice(('http', 'https')),
            subdomain=gen_string('alpha'),
        ),
        gen_url(
            scheme=choice(('http', 'https')),
            subdomain=gen_string('alphanumeric'),
        ),
        gen_url(
            scheme=choice(('http', 'https')),
            subdomain=gen_string('numeric'),
        ),
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

    def setUp(self):
        """Initialize test variables"""
        super(SettingTestCase, self).setUp()
        self.original_value = None
        self.param_name = None
        self.saved_element = None
        self.tab_locator = None
        self.value_type = None

    def tearDown(self):
        """Revert the setting to its default value"""
        if self.original_value:  # do nothing for skipped test
            if self.saved_element != self.original_value:
                with Session(self.browser) as session:
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=self.original_value,
                    )
        super(SettingTestCase, self).tearDown()

    @tier1
    def test_positive_update_authorize_login_delegation_param(self):
        """Updates parameter "authorize_login_delegation" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'authorize_login_delegation'
        self.value_type = 'dropdown'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @skip_if_bug_open('bugzilla', 1125181)
    @tier1
    def test_positive_update_administrator_param(self):
        """Updates parameter "administrator" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully

        @BZ: 1125181
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'administrator'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_authorize_login_delegation_api_param(self):
        """Updates parameter "authorize_login_delegation_api" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'authorize_login_delegation_api'
        self.value_type = 'dropdown'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_entries_per_page_param(self):
        """Updates parameter "entries_per_page" under General tab with
        invalid values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'entries_per_page'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in invalid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    session.nav.click(common_locators['notif.close'])
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_entries_per_page_param(self):
        """Updates parameter "entries_per_page" under General tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated successfully
        """
        param_value = str(randint(30, 1000))
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'entries_per_page'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            edit_param(
                session,
                tab_locator=self.tab_locator,
                param_name=self.param_name,
                value_type=self.value_type,
                param_value=param_value,
            )
            self.saved_element = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            self.assertEqual(param_value, self.saved_element)

    @skip_if_bug_open('bugzilla', 1125181)
    @tier1
    def test_positive_update_email_reply_address_param(self):
        """Updates parameter "email_reply_address" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully

        @BZ: 1125181
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'email_reply_address'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @skip_if_bug_open('bugzilla', 1156195)
    @tier1
    def test_positive_update_fix_db_cache_param(self):
        """Updates parameter "fix_db_cache" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully

        @BZ: 1156195
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'fix_db_cache'
        self.value_type = 'dropdown'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_use_gravatar_param(self):
        """Updates parameter "use_gravatar" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'use_gravatar'
        self.value_type = 'dropdown'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_max_trend_param(self):
        """Updates parameter "max_trend" under General tab with invalid
        values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'max_trend'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in invalid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    session.nav.click(common_locators['notif.close'])
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_max_trend_param(self):
        """Updates parameter "max_trend" under General tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'max_trend'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_maxtrend_timeout_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_idle_timeout_param(self):
        """Updates parameter "idle_timeout" under General tab with
        invalid values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'idle_timeout'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in invalid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    session.nav.click(common_locators['notif.close'])
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_idle_timeout_param(self):
        """Updates parameter "idle_timeout" under Auth tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'idle_timeout'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_maxtrend_timeout_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_foreman_url_param(self):
        """Updates parameter "foreman_url" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'foreman_url'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_urls():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_foreman_url_param(self):
        """Updates parameter "foreman_url" under General tab

        @Feature: Settings - Negative update Parameters

        @Assert: Parameter is not updated
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'foreman_url'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in invalid_foreman_urls():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    session.nav.click(common_locators['notif.close'])
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_dynflow_enable_console_param(self):
        """Updates parameter "dynflow_enable_console" under ForemanTasks
        tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_foremantasks']
        self.param_name = 'dynflow_enable_console'
        self.value_type = 'dropdown'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_auth_source_user_autocreate_param(self):
        """Updates parameter
        "authorize_login_delegation_auth_source_user_autocreate" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = ('authorize_login_delegation_auth_source_user'
                           '_autocreate')
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_login_delegation_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_login_delegation_logout_url_param(self):
        """Updates parameter "login_delegation_logout_url" under Auth
        tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'login_delegation_logout_url'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_urls():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_oauth_active_param(self):
        """Read-only param "oauth_active" under Auth tab shouldn't be
        updated

        @Feature: Settings - Update Parameters

        @Assert: Parameter is not editable
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        with Session(self.browser) as session:
            for param_name in invalid_oauth_active_values():
                with self.subTest(param_name):
                    with self.assertRaises(UIError) as context:
                        edit_param(
                            session,
                            tab_locator=self.tab_locator,
                            param_name=param_name,
                        )
                        self.assertEqual(
                            context.exception.message,
                            'Could not find edit button to update param'
                        )

    @tier1
    def test_positive_update_require_ssl_smart_proxies_param(self):
        """Updates parameter "require_ssl_smart_proxies" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'require_ssl_smart_proxies'
        self.value_type = 'dropdown'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_restrict_registered_smart_proxies_param(self):
        """Updates parameter "restrict_registered_smart_proxies" under
        Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'restrict_registered_smart_proxies'
        self.value_type = 'dropdown'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    self.original_value = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_trusted_puppetmaster_hosts_param(self):
        """Updates parameter "trusted_puppetmaster_hosts" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'trusted_puppetmaster_hosts'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_trusted_puppetmaster_hosts():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_trusted_puppetmaster_hosts_param(self):
        """Updates parameter "trusted_puppetmaster_hosts" under Auth tab

        @Feature: Settings - Negative update Parameters

        @Assert: Parameter is not updated
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'trusted_puppetmaster_hosts'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    session.nav.click(common_locators['notif.close'])
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_ignore_puppet_facts_for_provisioning_param(self):
        """Updates parameter "ignore_puppet_facts_for_provisioning" under
        Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'ignore_puppet_facts_for_provisioning'
        self.value_type = 'dropdown'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_update_manage_puppetca_param(self):
        """Updates parameter "manage_puppetca" under Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'manage_puppetca'
        self.value_type = 'dropdown'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_update_query_local_nameservers_param(self):
        """Updates parameter "query_local_nameservers" under
        Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'query_local_nameservers'
        self.value_type = 'dropdown'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_update_safemode_render_param(self):
        """Updates parameter "safemode_render" under Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'safemode_render'
        self.value_type = 'dropdown'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @run_only_on('sat')
    @tier1
    def test_negative_update_token_duration_param(self):
        """Updates parameter "token_duration" under Provisioning tab
        with invalid values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'token_duration'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in invalid_token_duration():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['notif.error'])
                    )
                    session.nav.click(common_locators['notif.close'])
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_update_token_duration_param(self):
        """Updates param "token_duration" under Provisioning tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated successfully
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'token_duration'
        self.value_type = 'input'
        with Session(self.browser) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_token_duration():
                with self.subTest(param_value):
                    self.original_value = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        value_type=self.value_type,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)
