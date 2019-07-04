# -*- encoding: utf-8 -*-
"""Test class for Setting Parameter values

:Requirement: Setting

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice, randint

from fauxfactory import gen_email, gen_string, gen_url
from nailgun import entities

from robottelo.datafactory import filtered_datapoint, valid_data_list
from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier1,
    tier2,
    tier4,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.base import UINoSuchElementError
from robottelo.ui.factory import edit_param
from robottelo.ui.locators import common_locators, tab_locators
from robottelo.ui.session import Session


@filtered_datapoint
def valid_boolean_values():
    """Returns a list of valid boolean values"""
    return [
        'Yes',
        'No',
    ]


@filtered_datapoint
def valid_settings_values():
    """Returns a list of valid settings values"""
    return [
        gen_email(gen_string('alpha')),
        gen_email(gen_string('alphanumeric')),
        gen_email(gen_string('numeric')),
    ]


@filtered_datapoint
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
        '[ ' + gen_string('alpha') + ' ]',
        '[ ' + gen_string('alphanumeric') + ' ]',
        '[ ' + gen_string('numeric') + ' ]'
    ]


@filtered_datapoint
def valid_token_duration():
    """Returns a list of valid token durations"""
    return ['90', '0']


@filtered_datapoint
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
        if self.original_value is not None:  # do nothing for skipped test
            if self.saved_element != self.original_value:
                if self.original_value == 'Empty':
                    # we cannot pass value Empty as it's not considered as None
                    # value can not be None a failure is raised
                    # when passing empty string the UI show Empty again
                    # other values like Yes, No and numbers in strings
                    # are handled correctly
                    self.original_value = ''
                setting_param = entities.Setting().search(
                    query={'search': 'name="{0}"'.format(self.param_name)})[0]
                setting_param.value = self.original_value
                setting_param.update({'value'})
        super(SettingTestCase, self).tearDown()

    @tier1
    def test_positive_update_authorize_login_delegation_param(self):
        """Updates parameter "authorize_login_delegation" under Auth tab

        :id: 0b752f6a-5987-483a-9cef-2d02fa42fe73

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'authorize_login_delegation'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    @upgrade
    def test_positive_update_administrator_param(self):
        """Updates parameter "administrator" under General tab

        :id: ecab6d51-ad29-4904-bc04-e62673ab1028

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'administrator'
        with Session(self) as session:
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

        :id: 1dc39d96-a0e3-4d2e-aeb8-14aedab2ebe3

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'authorize_login_delegation_api'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_entries_per_page_param(self):
        """Updates parameter "entries_per_page" under General tab with
        invalid values

        :id: b6bb39e2-797e-43e4-9629-d319c62992a4

        :expectedresults: Parameter is not updated

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'entries_per_page'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in invalid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['haserror']))
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_entries_per_page_param(self):
        """Updates parameter "entries_per_page" under General tab

        :id: e41933c8-d835-4126-a356-a186c8e9013f

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        param_value = str(randint(30, 1000))
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'entries_per_page'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            edit_param(
                session,
                tab_locator=self.tab_locator,
                param_name=self.param_name,
                param_value=param_value,
            )
            self.saved_element = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_email_reply_address_param(self):
        """Updates parameter "email_reply_address" under General tab

        :id: 274eaa6d-a6ba-4dbe-a843-c3717fbd70ae

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_email']
        self.param_name = 'email_reply_address'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_fix_db_cache_param(self):
        """Updates parameter "fix_db_cache" under General tab

        :id: b7f8df0e-9ac8-4075-8955-c895267e424c

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'fix_db_cache'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_use_gravatar_param(self):
        """Updates parameter "use_gravatar" under General tab

        :id: 6ea676c1-acb9-495f-9ee7-0a2c14f34ea1

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'use_gravatar'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_max_trend_param(self):
        """Updates parameter "max_trend" under General tab with invalid
        values

        :id: bcc2848d-734a-4b13-80fa-9fd34545cbe7

        :expectedresults: Parameter is not updated

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'max_trend'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in invalid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['haserror']))
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_max_trend_param(self):
        """Updates parameter "max_trend" under General tab

        :id: 6e08bb3b-de48-45b4-b982-7180dbb65ed2

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'max_trend'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_maxtrend_timeout_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_idle_timeout_param(self):
        """Updates parameter "idle_timeout" under General tab with
        invalid values

        :id: 0c46ec21-7402-4241-8b22-5f8afa1f5316

        :expectedresults: Parameter is not updated

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'idle_timeout'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in invalid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['haserror']))
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_idle_timeout_param(self):
        """Updates parameter "idle_timeout" under Auth tab

        :id: fd5b2fe0-7124-444b-9f00-fca2b38c52f4

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'idle_timeout'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_maxtrend_timeout_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_foreman_url_param(self):
        """Updates parameter "foreman_url" under General tab

        :id: e09e95e9-510a-48b6-a59f-5adc0a383ddc

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'foreman_url'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_urls():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_foreman_url_param(self):
        """Updates parameter "foreman_url" under General tab

        :id: ee450e0a-d02e-40c4-a67e-5508a29dc9c8

        :expectedresults: Parameter is not updated

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'foreman_url'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in invalid_foreman_urls():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['haserror']))
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_login_page_footer_text(self):
        """Updates parameter "Login_page_footer_text" under General tab

        :id: 56a983c4-925f-4cbe-8fdb-ce344219d739

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'login_text'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_data_list():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_remove_login_page_footer_text(self):
        """Remove parameter "Login_page_footer_text" under General tab

        :id: e31544bf-8d78-4452-9ddb-fd4b76544673

        :expectedresults: Parameter should be removed

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_general']
        self.param_name = 'login_text'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            edit_param(
                session,
                tab_locator=self.tab_locator,
                param_name=self.param_name,
                param_value=gen_string('alpha'),
            )
            self.settings.remove_parameter(self.tab_locator, self.param_name)
            self.saved_element = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            self.assertEqual("Empty", self.saved_element)

    @stubbed
    @tier2
    def test_positive_update_login_page_footer_text_with_long_string(self):
        """Attempt to update parameter "Login_page_footer_text"
            with long length string under General tab

        :id: c76d91e8-a207-43c6-904c-7ca2dae7cd16

        :steps:

            1. Navigate to Administer -> settings
            2. Click on general tab
            3. Input long length string into login page footer field
            4. Assert value from login page

        :expectedresults: Parameter is updated

        :CaseImportance: Critical
        """

    @tier1
    def test_positive_update_dynflow_enable_console_param(self):
        """Updates parameter "dynflow_enable_console" under ForemanTasks
        tab

        :id: 11a710f1-d5fc-48c7-9f31-a92dbbaebc40

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_foremantasks']
        self.param_name = 'dynflow_enable_console'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_auth_source_user_autocreate_param(self):
        """Updates parameter
        "authorize_login_delegation_auth_source_user_autocreate" under Auth tab

        :id: 82137c0c-1cf5-445d-87fe-1ff80a12df3c

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = ('authorize_login_delegation_auth_source_user'
                           '_autocreate')
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_login_delegation_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_login_delegation_logout_url_param(self):
        """Updates parameter "login_delegation_logout_url" under Auth
        tab

        :id: 67b32c5f-7e8e-4ba7-ab29-9af2ac3660a9

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'login_delegation_logout_url'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_urls():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_oauth_active_param(self):
        """Read-only param "oauth_active" under Auth tab shouldn't be
        updated

        :id: e69d791a-e5c4-4f42-b5dd-c9d3bca49673

        :expectedresults: Parameter is not editable

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        with Session(self) as session:
            for param_name in invalid_oauth_active_values():
                with self.subTest(param_name):
                    with self.assertRaises(UINoSuchElementError) as context:
                        edit_param(
                            session,
                            tab_locator=self.tab_locator,
                            param_name=param_name,
                        )
                    self.assertEqual(
                        str(context.exception),
                        'Could not find edit button to update selected param'
                    )

    @tier1
    def test_positive_update_require_ssl_smart_proxies_param(self):
        """Updates parameter "require_ssl_smart_proxies" under Auth tab

        :id: 79d5bb5f-6bec-4c1c-b68e-6727aeb04614

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'require_ssl_smart_proxies'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_restrict_registered_smart_proxies_param(self):
        """Updates parameter "restrict_registered_smart_proxies" under
        Auth tab

        :id: 7dbcf471-3cee-4718-a316-18da6c4c1ef0

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'restrict_registered_smart_proxies'
        with Session(self) as session:
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
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_trusted_puppetmaster_hosts_param(self):
        """Updates parameter "trusted_puppetmaster_hosts" under Auth tab

        :id: 18596dbc-7e2a-426c-bd1a-338a31ba6e97

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'trusted_puppetmaster_hosts'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_trusted_puppetmaster_hosts():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @tier1
    def test_negative_update_trusted_puppetmaster_hosts_param(self):
        """Updates parameter "trusted_puppetmaster_hosts" under Auth tab

        :id: 23af2612-1291-41a1-8002-87263e39bdbe

        :expectedresults: Parameter is not updated

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_auth']
        self.param_name = 'trusted_puppetmaster_hosts'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in invalid_settings_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['haserror']))
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @tier1
    def test_positive_update_ignore_puppet_facts_for_provisioning_param(self):
        """Updates parameter "ignore_puppet_facts_for_provisioning" under
        Provisioning tab

        :id: 71cb4779-7982-43b6-ab65-7198ec193941

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'ignore_puppet_facts_for_provisioning'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_update_manage_puppetca_param(self):
        """Updates parameter "manage_puppetca" under Provisioning tab

        :id: 2f652441-6beb-40c0-9fb3-f0b835d06ca7

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'manage_puppetca'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
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

        :id: 643960f4-121c-44f3-a5e8-00b9cf66ff99

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'query_local_nameservers'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_update_safemode_render_param(self):
        """Updates parameter "safemode_render" under Provisioning tab

        :id: 4762a89a-2ebe-4834-b44f-f74888e609bb

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'safemode_render'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in valid_boolean_values():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
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

        :id: a1d18ba3-a14f-47ab-82fb-1249abc7b076

        :expectedresults: Parameter is not updated

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'token_duration'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            for param_value in invalid_token_duration():
                with self.subTest(param_value):
                    edit_param(
                        session,
                        tab_locator=self.tab_locator,
                        param_name=self.param_name,
                        param_value=param_value,
                    )
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['haserror']))
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertNotEqual(param_value, self.saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_update_token_duration_param(self):
        """Updates param "token_duration" under Provisioning tab

        :id: a200b578-4463-444b-bed1-82e540a77529

        :expectedresults: Parameter is updated successfully

        :CaseImportance: Critical
        """
        self.tab_locator = tab_locators['settings.tab_provisioning']
        self.param_name = 'token_duration'
        with Session(self) as session:
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
                        param_value=param_value,
                    )
                    self.saved_element = self.settings.get_saved_value(
                        self.tab_locator, self.param_name)
                    self.assertEqual(param_value, self.saved_element)

    @stubbed()
    @tier1
    def test_negative_settings_access_to_non_admin(self):
        """Check non admin users can't access Administer -> Settings tab

        :id: cefb64ba-5209-4901-b09a-84a433e5e344

        :steps:
            1. Login with non admin user
            2. Check "Administer" tab is not present
            3. Navigate to /settings
            4. Check message permission denied is present

        :expectedresults: Administer -> Settings tab should not be available to
            non admin users

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_update_email_delivery_method_smtp(self):
        """Updating SMTP params on Email tab

        :id: 3668e81a-6bb0-4399-b192-cad191f6a167

        :steps:
            1. Navigate to Administer > Settings > Email tab
            2. Update delivery method select interface to SMTP
            3. SMTP params configuration:
                3.1. SMTP address
                3.2. SMTP authentication
                3.3. SMTP HELO/EHLO domain
                3.4. SMTP StartTLS  AUTO
                3.5. SMTP OpenSSL verify mode
                3.6. SMTP password
                3.7. SMTP port
                3.8. SMTP username
            4. Update "Email reply address" and "Email subject prefix"
            5. Click "Test Email" button
            6. Check success msg "Email was sent successfully" is shown
            7. Check sent email has updated values on sender and subject
                accordingly

        :expectedresults: Email is sent through SMTP

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    @upgrade
    def test_negative_update_email_delivery_method_smtp(self):
        """Updating SMTP params on Email tab fail

        :id: d2a40c36-4a7e-45cb-a1b6-750ed49f222b

        :steps:
            1. Navigate to Administer > Settings > Email tab
            2. Update delivery method select interface to SMTP
            3. Update SMTP params with invalid configuration:
                3.1. SMTP address
                3.2. SMTP authentication
                3.3. SMTP HELO/EHLO domain
                3.4. SMTP password
                3.5. SMTP port
                3.6. SMTP username
            4. Click "Test Email" button
            5. Check error msg "Unable to send email, check server log for more
                information" is shown
            6. Check /var/log/foreman/production.log has error msg related
                to email

        :expectedresults: Email is not sent through SMTP

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_positive_update_email_delivery_method_sendmail(self):
        """Updating Sendmail params on Email tab

        :id: 1651e820-7fc2-4295-acef-68737da8e1e2

        :steps:
            1. Navigate to Administer > Settings > Email tab
            2. Update delivery method select interface to Sendmail
            3. Sendmail params configuration:
                3.1. Sendmail arguments
                3.2. Sendmail location
                3.3. Send welcome email
            4. Update "Email reply address" and "Email subject prefix"
            5. Click "Test Email" button
            6. Check success msg "Email was sent successfully" is shown
            7. Check sent email has updated values on sender and subject
                accordingly

        :expectedresults: Email is sent through Sendmail

        :CaseImportance: Critical
        """

    @stubbed()
    @tier1
    def test_negative_update_email_delivery_method_sendmail(self):
        """Updating Sendmail params on Email tab fail

        :id: 72391f12-68dd-4fce-b289-d3876564ce8a

        :steps:
            1. Navigate to Administer > Settings > Email tab
            2. Update delivery method select interface to Sendmail
            3. update Sendmail params with invalid configuration:
                3.1. Sendmail arguments
                3.2. Sendmail location
                3.3. Send welcome email
            4. Click "Test Email" button
            5. Check error msg "Unable to send email, check server log for more
                information" is shown
            6. Check /var/log/foreman/production.log has error msg related
                to email

        :expectedresults: Email is not sent through Sendmail

        :CaseImportance: Critical
        """

    @stubbed()
    @tier4
    def test_positive_email_yaml_config_precedence(self):
        """Check configuration file /etc/foreman/email.yaml takes precedence
        over UI. This behaviour will be default until Foreman 1.16. This
        behavior can also be changed through --foreman-email-config-method
        installer parameter

        :id: 17b9fcd9-9b4b-41c9-b9f3-d3bd956c3939

        :steps:
            1. create a /etc/foreman/email.yaml file with smtp configuration
            2. Restart katello service
            3. Check only a few parameters are editable:
                3.1 : Email reply address
                3.2 : Email subject prefix
                3.3 : Send welcome email
            4. Delete or move email.yaml file
            5. Restart katello service
            6. Check all parameters on Administer/Settings/Email tab are
                editable.

        :expectedresults: File configuration takes precedence over ui

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_update_hostname_with_empty_fact(self):
        """Update the Hostname_facts settings without any string(empty values)

        :id: 13dbb5d2-f052-42fe-8cbc-9b58fa6553e7

        :Steps:

            1. Goto settings ->Discovered tab -> Hostname_facts
            2. Set empty hostname_facts (without any value)

        :expectedresults: Error should be raised on setting empty value for
            hostname_facts setting

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @tier1
    def test_positive_remove_hostname_default_prefix(self):
        """Remove the set(default) prefix from hostname_prefix setting

        :id: c609dd46-6104-4710-8171-966d7195674f

        :Steps:

            1. Goto settings -> Discovered tab -> Hostname_prefix
            2. Click on 'X' sign to remove the text and save

        :expectedresults: Default set prefix should be removed
        """
        self.tab_locator = tab_locators['settings.tab_discovered']
        self.param_name = 'discovery_prefix'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            edit_param(
                session,
                tab_locator=self.tab_locator,
                param_name=self.param_name,
                param_value=gen_string('alpha'),
            )
            self.settings.remove_parameter(self.tab_locator, self.param_name)
            self.saved_element = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            self.assertEqual("Empty", self.saved_element)

    @run_only_on('sat')
    @tier1
    def test_positive_remove_hostname_default_facts(self):
        """Remove the set(default) fact from hostname_facts setting and
        update w/ new fact

        :id: 250b8bf4-eca1-44d4-8154-7ec94a5fb16a

        :Steps:

            1. Goto settings ->Discovered tab -> Hostname_facts
            2. Click on 'X' sign to remove the text and update w/ fact UUID

        :expectedresults: Default set fact should be removed and a new fact
            should be set
        """
        self.tab_locator = tab_locators['settings.tab_discovered']
        self.param_name = 'discovery_hostname'
        with Session(self) as session:
            self.original_value = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            edit_param(
                session,
                tab_locator=self.tab_locator,
                param_name=self.param_name,
                param_value=gen_string('alpha'),
            )
            self.settings.remove_parameter(self.tab_locator, self.param_name)
            self.saved_element = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            self.assertEqual("Empty", self.saved_element)
            edit_param(
                session,
                tab_locator=self.tab_locator,
                param_name=self.param_name,
                param_value="uuid",
            )
            self.saved_element = self.settings.get_saved_value(
                self.tab_locator, self.param_name)
            self.assertEqual("uuid", self.saved_element)

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_discover_host_with_invalid_prefix(self):
        """Update the hostname_prefix with invalid string like
        -mac, 1mac or ^%$

        :id: 46c1c383-8ee7-4152-a6ca-0a049f3f70b0

        :Steps:

            1. Goto settings -> Discovered tab -> Hostname_prefix
            2. Update hostname_prefix starting with '-' or ^&$

        :expectedresults: Validation error should be raised on updating
            hostname_prefix with invalid string, should start w/ letter

        :CaseAutomation: notautomated
        """
