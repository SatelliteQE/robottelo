"""Test class for Setting Parameter values

:Requirement: Settings

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Settings

:Assignee: shwsingh

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random
from time import sleep

import pytest

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.settings import Settings
from robottelo.config import settings
from robottelo.datafactory import gen_string
from robottelo.datafactory import generate_strings_list
from robottelo.datafactory import invalid_boolean_strings
from robottelo.datafactory import invalid_emails_list
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_emails_list
from robottelo.datafactory import valid_url_list
from robottelo.datafactory import xdist_adapter


@pytest.mark.stubbed
@pytest.mark.tier2
def test_negative_update_hostname_with_empty_fact():
    """Update the Hostname_facts settings without any string(empty values)

    :id: daca0746-75ad-42fb-97ed-6db0224eeeac

    :expectedresults: Error should be raised on setting empty value for hostname_facts setting

    :CaseAutomation: NotAutomated
    """


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['discovery_prefix'], indirect=True)
def test_positive_update_hostname_prefix_without_value(setting_update):
    """Update the Hostname_prefix settings without any string(empty values)

    :id: a84c28ea-6821-4c31-b4ab-8662c22c9135

    :parametrized: yes

    :BZ: 1470083

    :expectedresults: Error should be raised on setting empty value for discovery_prefix setting

    """
    with pytest.raises(CLIReturnCodeError):
        Settings.set({'name': "discovery_prefix", 'value': ""})


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['discovery_prefix'], indirect=True)
def test_positive_update_hostname_default_prefix(setting_update):
    """Update the default set prefix of hostname_prefix setting

    :id: a6e46e53-6273-406a-8009-f184d9551d66

    :parametrized: yes

    :expectedresults: Default set prefix should be updated with new value

    """
    hostname_prefix_value = gen_string('alpha')
    Settings.set({'name': "discovery_prefix", 'value': hostname_prefix_value})
    discovery_prefix = Settings.list({'search': 'name=discovery_prefix'})[0]
    assert hostname_prefix_value == discovery_prefix['value']


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_update_hostname_default_facts():
    """Update the default set fact of hostname_facts setting with list of
    facts like: bios_vendor,uuid

    :id: 1042c5e2-ee4d-4eaf-a0b2-86c000a79dfb

    :expectedresults: Default set fact should be updated with facts list.

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier2
def test_negative_discover_host_with_invalid_prefix():
    """Update the hostname_prefix with invalid string like
    -mac, 1mac or ^%$

    :id: 73c5da42-28c8-4be7-8fb1-f505fefd6665

    :expectedresults: Validation error should be raised on updating
        hostname_prefix with invalid string, should start with letter

    :CaseAutomation: NotAutomated
    """


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['login_text'], indirect=True)
def test_positive_update_login_page_footer_text(setting_update):
    """Updates parameter "login_text" in settings

    :id: 4d4e1151-5bd6-4fa2-8dbb-e182b43ad7ec

    :steps:

        1. Execute "settings" command with "set" as sub-command
        with any string

    :parametrized: yes

    :expectedresults: Parameter is updated successfully

    """
    login_text_value = random.choice(list(valid_data_list().values()))
    Settings.set({'name': "login_text", 'value': login_text_value})
    login_text = Settings.list({'search': 'name=login_text'})[0]
    assert login_text["value"] == login_text_value


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['login_text'], indirect=True)
def test_positive_update_login_page_footer_text_without_value(setting_update):
    """Updates parameter "login_text" without any string (empty value)

    :id: 01ce95de-2994-42b6-b9f8-f7882981fb69

    :steps:

        1. Execute "settings" command with "set" as sub-command
        without any string(empty value) in value parameter

    :parametrized: yes

    :expectedresults: Message on login screen should be removed

    """
    Settings.set({'name': "login_text", 'value': ""})
    login_text = Settings.list({'search': 'name=login_text'})[0]
    assert login_text['value'] == ''


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['login_text'], indirect=True)
def test_positive_update_login_page_footer_text_with_long_string(setting_update):
    """Attempt to update parameter "Login_page_footer_text"
        with long length string under General tab

    :id: 87ef6b19-fdc5-4541-aba8-e730f1a3caa7

    :steps:
        1. Execute "settings" command with "set" as sub-command
        with long length string

    :parametrized: yes

    :expectedresults: Parameter is updated

    :CaseImportance: Low
    """
    login_text_value = random.choice(list(generate_strings_list(1000)))
    Settings.set({'name': "login_text", 'value': login_text_value})
    login_text = Settings.list({'search': 'name=login_text'})[0]
    assert login_text['value'] == login_text_value


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_update_email_delivery_method_smtp():
    """Check Updating SMTP params through settings subcommand

    :id: b26798e9-528c-4ed6-a09b-dc8e4668a8d7

    :steps:
        1. set "delivery_method" to smtp
        2. set all smtp related properties:
            2.1. smtp_address
            2.2. smtp_authentication
            2.3. smtp_domain
            2.4. smtp_enable_starttls_auto
            2.5. smtp_openssl_verify_mode
            2.6. smtp_password
            2.7. smtp_port
            2.8. smtp_user_name

    :expectedresults: SMTP properties are updated

    :CaseImportance: Low

    :CaseAutomation: NotAutomated
    """


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['delivery_method'], indirect=True)
def test_positive_update_email_delivery_method_sendmail(setting_update):
    """Check Updating Sendmail params through settings subcommand

    :id: 578de898-fde2-4957-b39a-9dd059f490bf

    :steps:
        1. set "delivery_method" to sendmail
        2. set all sendmail related properties:
            2.1. sendmail_arguments
            2.2. sendmail_location

    :expectedresults: Sendmail properties are updated

    :CaseImportance: Low

    :CaseAutomation: Automated
    """
    sendmail_argument_value = gen_string('alphanumeric')
    sendmail_config_params = {
        'delivery_method': 'sendmail',
        'sendmail_arguments': f'{sendmail_argument_value}',
        'sendmail_location': '/usr/sbin/sendmail',
    }
    for key, value in sendmail_config_params.items():
        Settings.set({'name': f'{key}', 'value': f'{value}'})
        assert Settings.list({'search': f'name={key}'})[0]['value'] == value


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['email_reply_address'], indirect=True)
def test_positive_update_email_reply_address(setting_update):
    """Check email reply address is updated

    :id: cb0907d1-9cb6-45c4-b2bb-e2790ea55f16

    :parametrized: yes

    :expectedresults: email_reply_address is updated

    :CaseImportance: Low

    :CaseAutomation: Automated
    """
    email_address = random.choice(list(valid_emails_list()))
    email_address = email_address.replace('"', r'\"').replace('`', r'\`')
    Settings.set({'name': "email_reply_address", 'value': email_address})
    email_reply_address = Settings.list(
        {'search': 'name=email_reply_address'}, output_format='json'
    )[0]
    assert email_reply_address['value'] == email_address


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['email_reply_address'], indirect=True)
def test_negative_update_email_reply_address(setting_update):
    """Check email reply address is not updated

    :id: 2a2220c2-badf-47d5-ba3f-e6329930ab39

    :steps: provide invalid email addresses

    :parametrized: yes

    :expectedresults: email_reply_address is not updated

    :CaseImportance: Low

    :CaseAutomation: Automated
    """
    invalid_email_address = random.choice(list(invalid_emails_list()))
    with pytest.raises(CLIReturnCodeError):
        Settings.set({'name': 'email_reply_address', 'value': invalid_email_address})


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['email_subject_prefix'], indirect=True)
def test_positive_update_email_subject_prefix(setting_update):
    """Check email subject prefix is updated

    :id: c8e6b323-7b39-43d6-a9f1-5474f920bba2

    :parametrized: yes

    :expectedresults: email_subject_prefix is updated

    :CaseAutomation: Automated

    :CaseImportance: Low
    """
    email_subject_prefix_value = gen_string('alpha')
    Settings.set({'name': "email_subject_prefix", 'value': email_subject_prefix_value})
    email_subject_prefix = Settings.list({'search': 'name=email_subject_prefix'})[0]
    assert email_subject_prefix_value == email_subject_prefix['value']


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['email_subject_prefix'], indirect=True)
def test_negative_update_email_subject_prefix(setting_update):
    """Check email subject prefix is not updated

    :id: 8a638596-248f-4196-af36-ad2982196382

    :parametrized: yes

    :steps: provide invalid prefix, like string with more than 255 chars

    :expectedresults: email_subject_prefix is not updated

    :CaseAutomation: Automated

    :CaseImportance: Low
    """
    email_subject_prefix_original = Settings.list({'search': 'name=email_subject_prefix'})[0]
    email_subject_prefix_value = gen_string('alpha', 256)
    with pytest.raises(CLIReturnCodeError):
        Settings.set({'name': 'email_subject_prefix', 'value': email_subject_prefix_value})
    email_subject_prefix = Settings.list({'search': 'name=email_subject_prefix'})[0]
    assert email_subject_prefix == email_subject_prefix_original


@pytest.mark.tier2
@pytest.mark.parametrize('send_welcome_email_value', ["true", "false"])
@pytest.mark.parametrize('setting_update', ['send_welcome_email'], indirect=True)
def test_positive_update_send_welcome_email(setting_update, send_welcome_email_value):
    """Check email send welcome email is updated

    :id: cdaf6cd0-5eea-4252-87c5-f9ec3ba79ac1

    :steps: valid values: boolean true or false

    :parametrized: yes

    :expectedresults: send_welcome_email is updated

    :CaseAutomation: Automated

    :CaseImportance: Low
    """
    Settings.set({'name': 'send_welcome_email', 'value': send_welcome_email_value})
    host_value = Settings.list({'search': 'name=send_welcome_email'})[0]['value']
    assert send_welcome_email_value == host_value


@pytest.mark.tier2
@pytest.mark.parametrize('rss_enable_value', ["true", "false"])
@pytest.mark.parametrize('setting_update', ['rss_enable'], indirect=True)
def test_positive_enable_disable_rssfeed(setting_update, rss_enable_value):
    """Check if the RSS feed can be enabled or disabled

    :id: 021cefab-2629-44e2-a30d-49c944d0a234

    :steps: Set rss_enable true or false

    :parametrized: yes

    :expectedresults: rss_enable is updated

    :CaseAutomation: Automated
    """
    Settings.set({'name': 'rss_enable', 'value': rss_enable_value})
    rss_setting = Settings.list({'search': 'name=rss_enable'})[0]
    assert rss_setting["value"] == rss_enable_value


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['rss_url'], indirect=True)
def test_positive_update_rssfeed_url(setting_update):
    """Check if the RSS feed URL is updated

    :id: 166ff6f2-e36e-4934-951f-b947139d0d73

    :steps:
        1. Save the original RSS URL
        2. Update RSS feed with a valid URL
        3. Assert the RSS feed URL was really updated
        4. Restore the original feed URL

    :parametrized: yes

    :expectedresults: RSS feed URL is updated

    :CaseAutomation: Automated
    """
    test_url = random.choice(list(valid_url_list()))
    Settings.set({'name': 'rss_url', 'value': test_url})
    updated_url = Settings.list({'search': 'name=rss_url'})[0]
    assert updated_url['value'] == test_url


@pytest.mark.parametrize('value', **xdist_adapter(invalid_boolean_strings()))
@pytest.mark.tier2
def test_negative_update_send_welcome_email(value):
    """Check email send welcome email is updated

    :id: 2f75775d-72a1-4b2f-86c2-98c36e446099

    :parametrized: yes

    :steps: set invalid values: not booleans

    :parametrized: yes

    :expectedresults: send_welcome_email is not updated

    :CaseAutomation: Automated

    :CaseImportance: Low
    """
    with pytest.raises(CLIReturnCodeError):
        Settings.set({'name': 'send_welcome_email', 'value': value})


@pytest.mark.tier3
@pytest.mark.run_in_one_thread
@pytest.mark.parametrize('setting_update', ['failed_login_attempts_limit'], indirect=True)
def test_positive_failed_login_attempts_limit(setting_update, default_sat):
    """automate brute force protection limit configurable function

    :id: f95407ed-451b-4387-ac9b-2959ae2f51ae

    :steps:
       1. Make sure login works.
       2. Save current value and set it to some lower value:
       3. Try to login with wrong password till failed_login_attempts_limit
       4. Make sure login now does not work:
       5. Wait timeout - 5 minutes + 1 second
       6. Verify you can now login fine
       7. Return the setting to previous value

    :CaseImportance: Critical

    :CaseLevel: System

    :parametrized: yes

    :expectedresults: failed_login_attempts_limit works as expected

    :CaseAutomation: Automated

    :BZ: 1778599
    """
    username = settings.server.admin_username
    password = settings.server.admin_password
    assert default_sat.execute(f'hammer -u {username} -p {password} user list').status == 0
    Settings.set({'name': 'failed_login_attempts_limit', 'value': '5'})
    for _ in range(5):
        assert default_sat.execute(f'hammer -u {username} -p BAD_PASS user list').status == 129
    assert default_sat.execute(f'hammer -u {username} -p {password} user list').status == 129
    sleep(180)
    assert default_sat.execute(f'hammer -u {username} -p {password} user list').status == 0
    Settings.set({'name': 'failed_login_attempts_limit', 'value': '0'})
    assert Settings.info({'name': 'failed_login_attempts_limit'})['value'] == '0'
