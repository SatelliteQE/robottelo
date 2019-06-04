"""Test class for Setting Parameter values

:Requirement: Setting

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Settings

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_email, gen_url
from nailgun import entities
from pytest import raises
from random import choice, randint
from robottelo.datafactory import filtered_datapoint, gen_string
from robottelo.decorators import (
    fixture,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade
)


@filtered_datapoint
def invalid_settings_values():
    """Returns a list of invalid settings values"""
    return [' ', '-1', 'text', '0']


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


def valid_error_messages():
    """Returns the list of valid error messages"""
    return ['Value is invalid: must be integer',
            'Value must be greater than 0']


def is_valid_error_message(actual_error_message):
    status = False
    for error_message in valid_error_messages():
        if error_message in actual_error_message:
            status = True
            break
    return status


@fixture
def set_original_property_value():
    property_list = {}

    def _set_original_property_value(property_name):
        before_test_setting_param = entities.Setting().search(
            query={'search': 'name="{0}"'.format(property_name)})[0]
        property_list[property_name] = before_test_setting_param.value
        return before_test_setting_param.value
    yield _set_original_property_value
    for key, value in property_list.items():
        after_test_setting_param = entities.Setting().search(
            query={'search': 'name="{0}"'.format(key)})[0]
        after_test_setting_param.value = value


@tier1
def test_positive_update_authorize_login_delegation_param(session, set_original_property_value):
    """Updates parameter "authorize_login_delegation" under Auth tab

    :id: 86ebe42f-0401-4e91-8448-9851d0d5ce10

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    property_name = 'authorize_login_delegation'
    set_original_property_value(property_name)
    with session:
        for param_value in valid_boolean_values():
            session.settings.update(
                'name = {}'.format(property_name),
                param_value
            )
            result = session.settings.read('name = {}'.format(property_name))
            assert result['table'][0]['Value'] == param_value


@tier1
@upgrade
def test_positive_update_administrator_param(session, set_original_property_value):
    """Updates parameter "administrator" under General tab

    :id: c3d53354-b190-4beb-94b7-d2c6e5759608

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    property_name = 'administrator'
    set_original_property_value(property_name)
    with session:
        for param_value in valid_settings_values():
            session.settings.update(
                'name = {}'.format(property_name),
                param_value
            )
            result = session.settings.read('name = {}'.format(property_name))
            assert result['table'][0]['Value'] == param_value


@tier1
def test_positive_update_authorize_login_delegation_api_param(session,
                                                              set_original_property_value):
    """Updates parameter "authorize_login_delegation_api" under Auth tab

    :id: 70245d20-c940-40c6-bf3a-80127fb81758

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    property_name = 'authorize_login_delegation_api'
    set_original_property_value(property_name)
    with session:
        for param_value in valid_boolean_values():
            session.settings.update(
                'name = {}'.format(property_name),
                param_value
            )
            result = session.settings.read('name = {}'.format(property_name))
            assert result['table'][0]['Value'] == param_value


@tier1
def test_negative_update_entries_per_page_param(session, set_original_property_value):
    """Updates parameter "entries_per_page" under General tab with
    invalid values

    :id: 7c75083d-1b4d-4744-aaa4-6fb9e93ab3c2

    :expectedresults: Parameter is not updated

    :CaseImportance: Critical
    """
    property_name = 'entries_per_page'
    set_original_property_value(property_name)
    with session:
        for param_value in invalid_settings_values():
            with raises(AssertionError) as context:
                session.settings.update(
                    'name = {}'.format(property_name),
                    param_value
                )
            assert is_valid_error_message(str(context.value))


@tier1
def test_positive_update_entries_per_page_param(session, set_original_property_value):
    """Updates parameter "entries_per_page" under General tab

    :id: 781ffa76-0646-4359-a0de-e9fc61ed03f1

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    param_value = str(randint(30, 1000))
    property_name = 'entries_per_page'
    set_original_property_value(property_name)
    with session:
        session.settings.update(
            'name = {}'.format(property_name),
            param_value
        )
        result = session.settings.read('name = {}'.format(property_name))
        assert result['table'][0]['Value'] == param_value


@tier1
def test_positive_update_email_reply_address_param(session, set_original_property_value):
    """Updates parameter "email_reply_address" under General tab

    :id: 9440e8f2-612d-452a-843d-38282067380b

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    property_name = 'email_reply_address'
    set_original_property_value(property_name)
    with session:
        for param_value in valid_settings_values():
            session.settings.update(
                'name = {}'.format(property_name),
                param_value
            )
            result = session.settings.read('name = {}'.format(property_name))
            assert result['table'][0]['Value'] == param_value


@tier1
def test_positive_update_fix_db_cache_param(session, set_original_property_value):
    """Updates parameter "fix_db_cache" under General tab

    :id: 7ecae561-e2f1-45db-a55a-1f59c80d2903

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    property_name = 'fix_db_cache'
    set_original_property_value(property_name)
    with session:
        for param_value in valid_boolean_values():
            session.settings.update(
                'name = {}'.format(property_name),
                param_value
            )
            result = session.settings.read('name = {}'.format(property_name))
            assert result['table'][0]['Value'] == param_value


@tier1
def test_negative_update_max_trend_param(session, set_original_property_value):
    """Updates parameter "max_trend" under General tab with invalid
    values

    :id: 2a3102c1-fc3c-41ab-8884-e7402036346a

    :expectedresults: Parameter is not updated

    :CaseImportance: Critical
    """
    property_name = 'max_trend'
    set_original_property_value(property_name)
    with session:
        for param_value in invalid_settings_values():
            with raises(AssertionError) as context:
                session.settings.update(
                    'name = {}'.format(property_name),
                    param_value
                )
            assert is_valid_error_message(str(context.value))


@tier1
def test_positive_update_max_trend_param(session, set_original_property_value):
    """Updates parameter "max_trend" under General tab

    :id: a171d2fc-0e09-4953-a038-42d78171b465

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    property_name = 'max_trend'
    set_original_property_value(property_name)
    with session:
        for param_value in valid_maxtrend_timeout_values():
            session.settings.update(
                'name = {}'.format(property_name),
                param_value
            )
            result = session.settings.read('name = {}'.format(property_name))
            assert result['table'][0]['Value'] == param_value


@tier1
def test_negative_update_idle_timeout_param(session, set_original_property_value):
    """Updates parameter "idle_timeout" under General tab with
    invalid values

    :id: 3b09ea93-753e-40d0-a425-8e4548b8181c

    :expectedresults: Parameter is not updated

    :CaseImportance: Critical
    """
    property_name = 'idle_timeout'
    set_original_property_value(property_name)
    with session:
        for param_value in invalid_settings_values():
            with raises(AssertionError) as context:
                session.settings.update(
                    'name = {}'.format(property_name),
                    param_value
                )
            assert is_valid_error_message(str(context.value))


@tier1
def test_positive_update_idle_timeout_param(session, set_original_property_value):
    """Updates parameter "idle_timeout" under Auth tab

    :id: d3188607-0c75-4808-81fe-cc6fea0637fe

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    property_name = 'idle_timeout'
    set_original_property_value(property_name)
    with session:
        for param_value in valid_maxtrend_timeout_values():
            session.settings.update(
                'name = {}'.format(property_name),
                param_value
            )
            result = session.settings.read('name = {}'.format(property_name))
            assert result['table'][0]['Value'] == param_value


@tier1
def test_positive_update_foreman_url_param(session, set_original_property_value):
    """Updates parameter "foreman_url" under General tab

    :id: c1dd73e0-25f6-4fad-8c8f-b4a39ce108f1

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    property_name = 'foreman_url'
    set_original_property_value(property_name)
    with session:
        for param_value in valid_urls():
            session.settings.update(
                'name = {}'.format(property_name),
                param_value
            )
            result = session.settings.read('name = {}'.format(property_name))
            assert result['table'][0]['Value'] == param_value


@tier1
def test_negative_update_foreman_url_param(session, set_original_property_value):
    """Updates parameter "foreman_url" under General tab

    :id: 087028ac-66bc-4a99-b6dd-adcc4c1e9478

    :expectedresults: Parameter is not updated

    :CaseImportance: Critical
    """
    property_name = 'foreman_url'
    set_original_property_value(property_name)
    with session:
        for param_value in invalid_settings_values():
            with raises(AssertionError) as context:
                session.settings.update(
                    'name = {}'.format(property_name),
                    param_value
                )
            assert 'Value URL must be valid and schema must be one of http and https' \
                   in str(context.value)


@tier1
def test_positive_update_login_page_footer_text(session, set_original_property_value):
    """Updates parameter "Login_page_footer_text" under General tab

    :id: 75000fca-e14e-41ff-ab56-eabff83ac4da

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    property_name = 'login_text'
    set_original_property_value(property_name)
    with session:
        for param_value in valid_urls():
            session.settings.update(
                'name = {}'.format(property_name),
                param_value
            )
            result = session.settings.read('name = {}'.format(property_name))
            assert result['table'][0]['Value'] == param_value


@stubbed()
@tier1
def test_positive_remove_login_page_footer_text():
    """Remove parameter "Login_page_footer_text" under General tab

    :id: cb11148c-c22d-4ed5-90e7-dd7b6f0eb5e4

    :expectedresults: Parameter should be removed

    :CaseImportance: Critical

    :CaseAutomation: notautomated
    """


@stubbed()
@tier1
def test_positive_update_login_page_footer_text_with_long_string():
    """Attempt to update parameter "Login_page_footer_text"
        with long length string under General tab

    :id: b1a51594-43e6-49d8-918b-9bc306f3a1a2

    :steps:

        1. Navigate to Administer -> settings
        2. Click on general tab
        3. Input long length string into login page footer field
        4. Assert value from login page

    :expectedresults: Parameter is updated

    :CaseImportance: Critical

    :CaseAutomation: notautomated
    """


@tier1
def test_positive_update_dynflow_enable_console_param(session, set_original_property_value):
    """Updates parameter "dynflow_enable_console" under ForemanTasks
    tab

    :id: 1c1d6973-afbd-4317-ae9b-30093b3e1fd1

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    property_name = 'dynflow_enable_console'
    set_original_property_value(property_name)
    with session:
        for param_value in valid_boolean_values():
            session.settings.update(
                'name = {}'.format(property_name),
                param_value
            )
            result = session.settings.read('name = {}'.format(property_name))
            assert result['table'][0]['Value'] == param_value


@stubbed()
@tier1
def test_negative_settings_access_to_non_admin():
    """Check non admin users can't access Administer -> Settings tab

    :id: 34bb9376-c5fe-431a-ac0d-ef030c0ab50e

    :steps:
        1. Login with non admin user
        2. Check "Administer" tab is not present
        3. Navigate to /settings
        4. Check message permission denied is present

    :expectedresults: Administer -> Settings tab should not be available to
        non admin users

    :CaseImportance: Critical

    :CaseAutomation: notautomated
    """


@stubbed()
@tier3
def test_positive_update_email_delivery_method_smtp():
    """Updating SMTP params on Email tab

    :id: aa4fb26d-2b3a-4b50-891b-a5dfffb31964

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

    :CaseLevel: Acceptance

    :CaseAutomation: notautomated
    """


@stubbed()
@tier3
@upgrade
def test_negative_update_email_delivery_method_smtp():
    """Updating SMTP params on Email tab fail

    :id: ecb07f03-f132-4319-b63a-cc3f1ac2c6bb

    :steps:
        1. Navigate to Administer > Settings > Email tab
        2. Update delivery method select interface to SMTP
        3. Update SMTP params with invalid configuration:
            3.1. SMTP address
            3.2. SMTP authentication
            3.3. SMTP HELO/EHLO domain
            3.4. SMTP password
            3.5. SMTP port
            3.5. SMTP port
            3.6. SMTP username
        4. Click "Test Email" button
        5. Check error msg "Unable to send email, check server log for more
            information" is shown
        6. Check /var/log/foreman/production.log has error msg related
            to email

    :expectedresults: Email is not sent through SMTP

    :CaseImportance: Critical

    :CaseLevel: Acceptance

    :CaseAutomation: notautomated
    """


@stubbed()
@tier3
def test_positive_update_email_delivery_method_sendmail():
    """Updating Sendmail params on Email tab

    :id: c774e713-9640-402d-8987-c3509e918eb6

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

    :CaseLevel: Acceptance

    :CaseAutomation: notautomated
    """


@stubbed()
@tier3
def test_negative_update_email_delivery_method_sendmail():
    """Updating Sendmail params on Email tab fail

    :id: 3fe2ed56-3b6f-4532-81f2-38d793429297

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

    :CaseLevel: Acceptance

    :CaseAutomation: notautomated
    """


@stubbed()
@tier3
def test_positive_email_yaml_config_precedence():
    """Check configuration file /etc/foreman/email.yaml takes precedence
    over UI. This behaviour will be default until Foreman 1.16. This
    behavior can also be changed through --foreman-email-config-method
    installer parameter

    :id: 6024d5ba-e1ff-47d4-b9fc-f070e882f08c

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

    :CaseLevel: Acceptance

    :CaseAutomation: notautomated
    """


@stubbed()
@tier2
def test_negative_update_hostname_with_empty_fact():
    """Update the Hostname_facts settings without any string(empty values)

    :id: e0eaab69-4926-4c1e-b111-30c51ede273e

    :Steps:

        1. Goto settings ->Discovered tab -> Hostname_facts
        2. Set empty hostname_facts (without any value)

    :expectedresults: Error should be raised on setting empty value for
        hostname_facts setting

    :CaseAutomation: notautomated
    """
