# -*- encoding: utf-8 -*-
"""Test class for Setting Parameter values

@Requirement: Setting

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_email, gen_string, gen_url
from functools import wraps
from random import choice, randint
from robottelo.datafactory import filtered_datapoint
from robottelo.decorators import (
    affected_by_bz,
    run_only_on,
    skip_if_bug_open,
    tier1,
)
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import edit_param
from robottelo.ui.locators import common_locators, tab_locators
from robottelo.ui.session import Session


def pick_one_if_bz_open(func):
    """Returns random value from provided data set in case specific defect is
    open or full data set otherwise
    """
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        """Check whether defect is open and make corresponding decision"""
        data_set = func(*args, **kwargs)
        if affected_by_bz(1335799):
            data_set = [choice(data_set)]
        return data_set
    return func_wrapper


@filtered_datapoint
def valid_boolean_values():
    """Returns a list of valid boolean values"""
    return [
        'true',
        'false',
    ]


@filtered_datapoint
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


@filtered_datapoint
@pick_one_if_bz_open
def invalid_foreman_urls():
    """Returns a list of invalid foreman urls"""
    return[
        'http://\\' + gen_string('alpha') + '.dom.com',
        'http://' + gen_string('utf8') + '.dom.com',
        'http://' + gen_string('latin1') + '.dom.com',
        'http://' + gen_string('html') + '.dom.com',
        ' '
    ]


@filtered_datapoint
@pick_one_if_bz_open
def invalid_settings_values():
    """Returns a list of invalid settings values"""
    return [' ', '-1', 'text', '0']


@filtered_datapoint
def valid_maxtrend_timeout_values():
    """Returns a list of valid maxtrend, timeout values"""
    return [
        str(randint(10, 99)),
        str(randint(10000, 99999)),
    ]


@filtered_datapoint
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


@filtered_datapoint
def valid_login_delegation_values():
    """Returns a list of valid delegation values"""
    return [
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric')
    ]


@filtered_datapoint
@pick_one_if_bz_open
def invalid_oauth_active_values():
    """Returns a list of invalid oauth_active values"""
    return [
        'oauth_active',
        'oauth_consumer_key',
        'oauth_consumer_secret',
        'oauth_map_users',
    ]


@filtered_datapoint
def valid_trusted_puppetmaster_hosts():
    """Returns a list of valid trusted puppetmaster hosts"""
    return [
        '[ ' + gen_string('utf8') + ' ]',
        '[ ' + gen_string('alphanumeric') + ' ]',
        '[ ' + gen_string('numeric') + ' ]'
    ]


@filtered_datapoint
def valid_token_duration():
    """Returns a list of valid token durations"""
    return ['90', '0']


@filtered_datapoint
@pick_one_if_bz_open
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

        @id: 0b752f6a-5987-483a-9cef-2d02fa42fe73

        @expectedresults: Parameter is updated successfully
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

        @id: ecab6d51-ad29-4904-bc04-e62673ab1028

        @expectedresults: Parameter is updated successfully

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

        @id: 1dc39d96-a0e3-4d2e-aeb8-14aedab2ebe3

        @expectedresults: Parameter is updated successfully
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

        @id: b6bb39e2-797e-43e4-9629-d319c62992a4

        @expectedresults: Parameter is not updated
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

        @id: e41933c8-d835-4126-a356-a186c8e9013f

        @expectedresults: Parameter is updated successfully
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

        @id: 274eaa6d-a6ba-4dbe-a843-c3717fbd70ae

        @expectedresults: Parameter is updated successfully

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

        @id: b7f8df0e-9ac8-4075-8955-c895267e424c

        @expectedresults: Parameter is updated successfully

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

        @id: 6ea676c1-acb9-495f-9ee7-0a2c14f34ea1

        @expectedresults: Parameter is updated successfully
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

        @id: bcc2848d-734a-4b13-80fa-9fd34545cbe7

        @expectedresults: Parameter is not updated
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

        @id: 6e08bb3b-de48-45b4-b982-7180dbb65ed2

        @expectedresults: Parameter is updated successfully
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

        @id: 0c46ec21-7402-4241-8b22-5f8afa1f5316

        @expectedresults: Parameter is not updated
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

        @id: fd5b2fe0-7124-444b-9f00-fca2b38c52f4

        @expectedresults: Parameter is updated successfully
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

        @id: e09e95e9-510a-48b6-a59f-5adc0a383ddc

        @expectedresults: Parameter is updated successfully
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

        @id: ee450e0a-d02e-40c4-a67e-5508a29dc9c8

        @expectedresults: Parameter is not updated
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

        @id: 11a710f1-d5fc-48c7-9f31-a92dbbaebc40

        @expectedresults: Parameter is updated successfully
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

        @id: 82137c0c-1cf5-445d-87fe-1ff80a12df3c

        @expectedresults: Parameter is updated successfully
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

        @id: 67b32c5f-7e8e-4ba7-ab29-9af2ac3660a9

        @expectedresults: Parameter is updated successfully
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

        @id: e69d791a-e5c4-4f42-b5dd-c9d3bca49673

        @expectedresults: Parameter is not editable
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

        @id: 79d5bb5f-6bec-4c1c-b68e-6727aeb04614

        @expectedresults: Parameter is updated successfully
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

        @id: 7dbcf471-3cee-4718-a316-18da6c4c1ef0

        @expectedresults: Parameter is updated successfully
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

        @id: 18596dbc-7e2a-426c-bd1a-338a31ba6e97

        @expectedresults: Parameter is updated successfully
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

        @id: 23af2612-1291-41a1-8002-87263e39bdbe

        @expectedresults: Parameter is not updated
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'trusted_puppetmaster_hosts'
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
    def test_positive_update_ignore_puppet_facts_for_provisioning_param(self):
        """Updates parameter "ignore_puppet_facts_for_provisioning" under
        Provisioning tab

        @id: 71cb4779-7982-43b6-ab65-7198ec193941

        @expectedresults: Parameter is updated successfully
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

        @id: 2f652441-6beb-40c0-9fb3-f0b835d06ca7

        @expectedresults: Parameter is updated successfully
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

        @id: 643960f4-121c-44f3-a5e8-00b9cf66ff99

        @expectedresults: Parameter is updated successfully
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

        @id: 4762a89a-2ebe-4834-b44f-f74888e609bb

        @expectedresults: Parameter is updated successfully
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

        @id: a1d18ba3-a14f-47ab-82fb-1249abc7b076

        @expectedresults: Parameter is not updated
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

        @id: a200b578-4463-444b-bed1-82e540a77529

        @expectedresults: Parameter is updated successfully
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
