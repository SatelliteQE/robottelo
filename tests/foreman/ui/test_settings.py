# -*- encoding: utf-8 -*-
"""Test class for Setting Parameter values"""

from ddt import ddt
from fauxfactory import gen_email, gen_string, gen_url
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import edit_param
from robottelo.ui.locators import common_locators, tab_locators
from robottelo.ui.session import Session


@ddt
class Settings(UITestCase):
    """Implements Boundary tests for Settings menu"""

    @data('true', 'false')
    def test_positive_update_general_param_1(self, param_value):
        """@Test: Updates param "authorize_login_delegation" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'authorize_login_delegation'
        with Session(self.browser) as session:
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
    @data(
        gen_email(gen_string('alpha')),
        gen_email(gen_string('alphanumeric')),
        gen_email(gen_string('latin1')),
        gen_email(gen_string('numeric')),
        gen_email(gen_string('utf8')),
        gen_email(gen_string('html')),
        gen_email(gen_string('alphanumeric', 40)),
    )
    def test_positive_update_general_param_2(self, param_value):
        """@Test: Updates param "administrator" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        @BZ: 1125181

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'administrator'
        with Session(self.browser) as session:
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

    @data('true', 'false')
    def test_positive_update_general_param_3(self, param_value):
        """@Test: Updates param "authorize_login_delegation_api" under General
        tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'authorize_login_delegation_api'
        with Session(self.browser) as session:
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
    @data(' ', '-1', 'text', '0')
    def test_negative_update_general_param_4(self, param_value):
        """@Test: Updates param "entries_per_page" under General tab with
        invalid values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'entries_per_page'
        with Session(self.browser) as session:
            edit_param(
                session,
                tab_locator=tab_locator,
                param_name=param_name,
                value_type='input',
                param_value=param_value,
            )
            self.assertIsNotNone(
                session.nav.wait_until_element(common_locators['notif.error']))
            saved_element = self.settings.get_saved_value(
                tab_locator, param_name)
            self.assertNotEqual(param_value, saved_element)

    def test_positive_update_general_param_5(self):
        """@Test: Updates param "entries_per_page" under General tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated

        """
        param_value = gen_string('numeric', 5)
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'entries_per_page'
        with Session(self.browser) as session:
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

    @skip_if_bug_open('bugzilla', 1125181)
    @data(
        gen_email(gen_string('alpha')),
        gen_email(gen_string('alphanumeric')),
        gen_email(gen_string('latin1')),
        gen_email(gen_string('numeric')),
        gen_email(gen_string('utf8')),
        gen_email(gen_string('html')),
        gen_email(gen_string('alphanumeric', 40)),
    )
    def test_positive_update_general_param_6(self, param_value):
        """@Test: Updates param "email_reply_address" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        @BZ: 1125181

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'email_reply_address'
        with Session(self.browser) as session:
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
    @data('true', 'false')
    def test_positive_update_general_param_7(self, param_value):
        """@Test: Updates param "fix_db_cache" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        @BZ: 1156195

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'fix_db_cache'
        with Session(self.browser) as session:
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

    @data('true', 'false')
    def test_positive_update_general_param_8(self, param_value):
        """@Test: Updates param "use_gravatar" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'use_gravatar'
        with Session(self.browser) as session:
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
    @data(' ', '-1', 'text', '0')
    def test_negative_update_general_param_9(self, param_value):
        """@Test: Updates param "max_trend" under General tab with invalid
        values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'max_trend'
        with Session(self.browser) as session:
            edit_param(
                session,
                tab_locator=tab_locator,
                param_name=param_name,
                value_type='input',
                param_value=param_value,
            )
            self.assertIsNotNone(
                session.nav.wait_until_element(common_locators['notif.error']))
            saved_element = self.settings.get_saved_value(
                tab_locator, param_name)
            self.assertNotEqual(param_value, saved_element)

    @data(gen_string('numeric', 2), gen_string('numeric', 5))
    def test_positive_update_general_param_10(self, param_value):
        """@Test: Updates param "max_trend" under General tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'max_trend'
        with Session(self.browser) as session:
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
    @data(' ', '-1', 'text', '0')
    def test_negative_update_general_param_11(self, param_value):
        """@Test: Updates param "idle_timeout" under General tab with invalid
        values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'idle_timeout'
        with Session(self.browser) as session:
            edit_param(
                session,
                tab_locator=tab_locator,
                param_name=param_name,
                value_type='input',
                param_value=param_value,
            )
            self.assertIsNotNone(
                session.nav.wait_until_element(common_locators['notif.error']))
            saved_element = self.settings.get_saved_value(
                tab_locator, param_name)
            self.assertNotEqual(param_value, saved_element)

    @data(gen_string('numeric', 1), gen_string('numeric', 5))
    def test_positive_update_general_param_12(self, param_value):
        """@Test: Updates param "idle_timeout" under General tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'idle_timeout'
        with Session(self.browser) as session:
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

    @data(
        gen_url(subdomain=gen_string('alpha')),
        gen_url(subdomain=gen_string('alphanumeric')),
        gen_url(subdomain=gen_string('numeric')),
    )
    def test_positive_update_general_param_13(self, param_value):
        """@Test: Updates param "foreman_url" under General tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'foreman_url'
        with Session(self.browser) as session:
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
    @data(
        'http://\\' + gen_string('alpha') + '.dom.com',
        'http://' + gen_string('utf8') + '.dom.com',
        'http://' + gen_string('latin1') + '.dom.com',
        'http://' + gen_string('html') + '.dom.com',
        ' '
    )
    def test_negative_update_general_param_14(self, param_value):
        """@Test: Updates param "foreman_url" under General tab

        @Feature: Settings - Negative update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156

        """
        tab_locator = tab_locators['settings.tab_general']
        param_name = 'foreman_url'
        with Session(self.browser) as session:
            edit_param(
                session,
                tab_locator=tab_locator,
                param_name=param_name,
                value_type='input',
                param_value=param_value,
            )
            self.assertIsNotNone(
                session.nav.wait_until_element(common_locators['notif.error']))
            saved_element = self.settings.get_saved_value(
                tab_locator, param_name)
            self.assertNotEqual(param_value, saved_element)

    @data('true', 'false')
    def test_positive_update_foremantasks_param_15(self, param_value):
        """@Test: Updates param "dynflow_enable_console" under ForemanTasks tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_foremantasks']
        param_name = 'dynflow_enable_console'
        with Session(self.browser) as session:
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

    @data(
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
    )
    def test_positive_update_auth_param_16(self, param_value):
        """@Test: Updates param
        "authorize_login_delegation_auth_source_user_autocreate" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'authorize_login_delegation_auth_source_user_autocreate'
        with Session(self.browser) as session:
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

    @data(
        gen_url(subdomain=gen_string('alpha')),
        gen_url(subdomain=gen_string('alphanumeric')),
        gen_url(subdomain=gen_string('numeric')),
    )
    def test_positive_update_auth_param_17(self, param_value):
        """@Test: Updates param "login_delegation_logout_url" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'login_delegation_logout_url'
        with Session(self.browser) as session:
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

    @data(
        'oauth_active',
        'oauth_consumer_key',
        'oauth_consumer_secret',
        'oauth_map_users'
    )
    def test_positive_update_auth_param_18(self, param_name):
        """@Test: Read-only param "oauth_active" under Auth tab shouldn't be
        updated

        @Feature: Settings - Update Parameters

        @Assert: Parameter is not editable

        """
        tab_locator = tab_locators['settings.tab_auth']
        with Session(self.browser) as session:
            with self.assertRaises(UIError) as context:
                edit_param(
                    session,
                    tab_locator=tab_locator,
                    param_name=param_name,
                )
                self.assertEqual(
                    context.exception.message,
                    'Could not find edit button to update selected param'
                )

    @data('true', 'false')
    def test_positive_update_auth_param_19(self, param_value):
        """@Test: Updates param "require_ssl_puppetmasters" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'require_ssl_puppetmasters'
        value_type = 'dropdown'
        with Session(self.browser) as session:
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

    @data('true', 'false')
    def test_positive_update_auth_param_20(self, param_value):
        """@Test: Updates param "restrict_registered_puppetmasters" under Auth
        tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'restrict_registered_puppetmasters'
        value_type = 'dropdown'
        with Session(self.browser) as session:
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

    @data(
        '[ ' + gen_string('utf8') + ' ]',
        '[ ' + gen_string('alphanumeric') + ' ]',
        '[ ' + gen_string('numeric') + ' ]'
    )
    def test_positive_update_auth_param_21(self, param_value):
        """@Test: Updates param "trusted_puppetmaster_hosts" under Auth tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'trusted_puppetmaster_hosts'
        with Session(self.browser) as session:
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
    @data(' ', '-1', 'text', '0')
    def test_negative_update_auth_param_22(self, param_value):
        """@Test: Updates param "trusted_puppetmaster_hosts" under Auth tab

        @Feature: Settings - Negative update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156

        """
        tab_locator = tab_locators['settings.tab_auth']
        param_name = 'trusted_puppetmaster_hosts'
        with Session(self.browser) as session:
            edit_param(
                session,
                tab_locator=tab_locator,
                param_name=param_name,
                value_type='input',
                param_value=param_value,
            )
            self.assertIsNotNone(
                session.nav.wait_until_element(common_locators['notif.error']))
            saved_element = self.settings.get_saved_value(
                tab_locator, param_name)
            self.assertNotEqual(param_value, saved_element)

    @data('true', 'false')
    def test_positive_update_provisioning_param_23(self, param_value):
        """@Test: Updates param "ignore_puppet_facts_for_provisioning" under
        Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'ignore_puppet_facts_for_provisioning'
        with Session(self.browser) as session:
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
    @data('true', 'false')
    def test_positive_update_provisioning_param_24(self, param_value):
        """@Test: Updates param "ignore_puppet_facts_for_provisioning" under
        Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'ignore_puppet_facts_for_provisioning'
        with Session(self.browser) as session:
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
    @data('true', 'false')
    def test_positive_update_provisioning_param_25(self, param_value):
        """@Test: Updates param "manage_puppetca" under Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'manage_puppetca'
        with Session(self.browser) as session:
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
    @data('true', 'false')
    def test_positive_update_provisioning_param_26(self, param_value):
        """@Test: Updates param "query_local_nameservers" under Provisioning
        tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'query_local_nameservers'
        with Session(self.browser) as session:
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
    @data('true', 'false')
    def test_positive_update_provisioning_param_27(self, param_value):
        """@Test: Updates param "safemode_render" under Provisioning tab

        @Feature: Settings - Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'safemode_render'
        with Session(self.browser) as session:
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
    @data(' ', '-1', 'text')
    def test_negative_update_provisioning_param_28(self, param_value):
        """@Test: Updates param "token_duration" under Provisioning tab with
        invalid values

        @Feature: Settings - Negative Update Parameters

        @Assert: Parameter is not updated

        @BZ: 1125156

        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'token_duration'
        with Session(self.browser) as session:
            edit_param(
                session,
                tab_locator=tab_locator,
                param_name=param_name,
                value_type='input',
                param_value=param_value,
            )
            self.assertIsNotNone(
                session.nav.wait_until_element(common_locators['notif.error']))
            saved_element = self.settings.get_saved_value(
                tab_locator, param_name)
            self.assertNotEqual(param_value, saved_element)

    @run_only_on('sat')
    @data('90', '0')
    def test_positive_update_provisioning_param_29(self, param_value):
        """@Test: Updates param "token_duration" under Provisioning tab

        @Feature: Settings - Positive Update Parameters

        @Assert: Parameter is updated

        """
        tab_locator = tab_locators['settings.tab_provisioning']
        param_name = 'token_duration'
        value_type = 'input'
        with Session(self.browser) as session:
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
            # This is the time in minutes as for how long installation token
            # should be valid; '0' value is to disable it
            # Resetting the token_duration to its default value '60'
            if saved_element == '0':
                edit_param(
                    session,
                    tab_locator=tab_locator,
                    param_name=param_name,
                    value_type=value_type,
                    param_value=default_value,
                )
