"""Test class for Setting Parameter values

:Requirement: Setting

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Settings

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from airgun.session import Session
from fauxfactory import gen_url
from nailgun import entities
from pytest import raises

from robottelo import ssh
from robottelo.cli.user import User
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import stubbed
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import upgrade


@filtered_datapoint
def invalid_settings_values():
    """Returns a list of invalid settings values"""
    return [' ', '-1', 'text', '0']


def valid_error_messages():
    """Returns the list of valid error messages"""
    return [
        'Value is invalid: must be integer',
        'Value must be greater than 0',
        'Value URL must be valid and schema must be one of http and https',
    ]


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
            query={'search': 'name="{0}"'.format(property_name)}
        )[0]
        property_list[property_name] = before_test_setting_param.value
        return before_test_setting_param.value

    yield _set_original_property_value
    for key, value in property_list.items():
        after_test_setting_param = entities.Setting().search(
            query={'search': 'name="{0}"'.format(key)}
        )[0]
        after_test_setting_param.value = value


def setting_cleanup(setting_name=None, setting_value=None):
    """Put necessary value for a specified setting"""
    setting_entity = entities.Setting().search(query={'search': 'name={}'.format(setting_name)})[0]
    setting_entity.value = setting_value
    setting_entity.update({'value'})


def add_content_views_to_composite(composite_cv, org, repo):
    """Add necessary number of content views to the composite one

    :param composite_cv: Composite content view object
    :param org: Organisation of satellite
    :param repo: repository need to added in content view
    """
    content_view = entities.ContentView(organization=org).create()
    content_view.repository = [repo]
    content_view.update(['repository'])
    content_view.publish()
    composite_cv.component = [content_view.read().version[0]]
    composite_cv.update(['component'])


@tier3
def test_positive_update_restrict_composite_view(session, set_original_property_value):
    """Update settings parameter restrict_composite_view to Yes/True and ensure
    a composite content view may not be published or promoted, unless the component
    content view versions that it includes exist in the target environment.

    :id: a5d2d73d-064e-48af-ad62-da68e963e3ee

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical

    :CaseLevel: Acceptance
    """
    repo_name = gen_string('alpha')
    property_name = 'restrict_composite_view'
    set_original_property_value(property_name)
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    repo = entities.Repository(name=repo_name, product=product).create()
    composite_cv = entities.ContentView(composite=True, organization=org).create()
    add_content_views_to_composite(composite_cv, org, repo)
    composite_cv.publish()
    with session:
        session.organization.select(org_name=org.name)
        for param_value in ('Yes', 'No'):
            session.settings.update('name = {}'.format(property_name), param_value)
            if param_value == 'Yes':
                with raises(AssertionError) as context:
                    session.contentview.promote(composite_cv.name, 'Version 1.0', lce.name)
                assert (
                    'Administrator -> Settings -> Content page using the '
                    'restrict_composite_view flag.' in str(context.value)
                )
            else:
                result = session.contentview.promote(composite_cv.name, 'Version 1.0', lce.name)
                assert lce.name in result['Environments']


@pytest.mark.skip_if_open("BZ:1677282")
@tier2
def test_positive_httpd_proxy_url_update(session, set_original_property_value):
    """Update the http_proxy_url should pass successfully.

    :id: 593eb8e1-16dd-486b-a760-47b8fdf4dcb9

    :expectedresults: http_proxy_url updated successfully.

    :BZ: 1677282

    :CaseImportance: Medium

    """
    property_name = 'http_proxy'
    with session:
        set_original_property_value(property_name)
        param_value = gen_url(scheme='https')
        session.settings.update('name = {}'.format(property_name), param_value)
        result = session.settings.read('name = {}'.format(property_name))
        assert result['table'][0]['Value'] == param_value


@tier2
def test_negative_validate_error_message(session, set_original_property_value):
    """Updates some settings with invalid values (an exceptional tier2 test)

    :id: 7c75083d-1b4d-4744-aaa4-6fb9e93ab3c2

    :expectedresults: Parameter is not updated

    :CaseImportance: Medium
    """
    property_names = ['entries_per_page', 'foreman_url']
    with session:
        for property_name in property_names:
            set_original_property_value(property_name)
            for param_value in invalid_settings_values():
                with raises(AssertionError) as context:
                    session.settings.update('name = {}'.format(property_name), param_value)
                assert is_valid_error_message(str(context.value))


@run_in_one_thread
@tier2
def test_positive_selectors(session):
    """"Testing input for selectors: dropdown, text area, input box

    :id: 529ddd3a-1271-4043-9006-eac436b08b11

    :expectedresults: Successfully add value to different selectors

    :CaseImportance: High
    """
    uuid_input = "[ {} ]".format(gen_string("alpha"))
    random_input = gen_string('alpha')
    uuid_duplicate_prop = ('host_dmi_uuid_duplicates', uuid_input)
    reg_host_prop = ('register_hostname_fact', random_input)
    dep_solve_prop = ('content_view_solve_dependencies', 'Yes')

    with session:
        for setting_attr, value in [uuid_duplicate_prop, dep_solve_prop, reg_host_prop]:
            # Stores original values for each type of selectors
            original_val = entities.Setting().search(
                query={'search': 'name={}'.format(setting_attr)}
            )[0]
            # Update to new value and resets value to back to old state
            try:
                session.settings.update('name = {}'.format(setting_attr), value)
                result = session.settings.read('name = {}'.format(setting_attr))
                assert result['table'][0]['Value'] == value
            finally:
                setting_cleanup(setting_attr, str(original_val.default))


@tier3
def test_positive_update_login_page_footer_text_with_long_string(session):
    """Testing to update parameter "Login_page_footer_text with long length
    string under General tab

    :id: b1a51594-43e6-49d8-918b-9bc306f3a1a2

    :steps:

        1. Navigate to Administer -> settings
        2. Click on general tab
        3. Input long length string into login page footer field
        4. Assert value from login page

    :expectedresults: Parameter is updated

    :CaseImportance: Medium

    :CaseLevel: Acceptance
    """
    property_name = 'login_text'
    property_value = entities.Setting().search(query={'search': f'name={property_name}'})[0]
    login_text_data = gen_string('alpha', 270)
    with session:
        try:
            session.settings.update(f"name={property_name}", f"{login_text_data}")
            result = session.login.logout()
            assert result["login_text"] == login_text_data
        finally:
            setting_cleanup(setting_name=property_name, setting_value=property_value.value)


@tier3
def test_negative_settings_access_to_non_admin():
    """Check non admin users can't access Administer -> Settings tab

    :id: 34bb9376-c5fe-431a-ac0d-ef030c0ab50e

    :steps:

        1. Login with non admin user
        2. Check "Administer" tab is not present
        3. Navigate to /settings
        4. Check message permission denied is present

    :expectedresults: Administer -> Settings tab should not be available to non admin users

    :CaseImportance: Medium

    :CaseLevel: Acceptance
    """
    login = gen_string('alpha')
    password = gen_string('alpha')
    entities.User(admin=False, login=login, password=password).create()
    try:
        with Session(user=login, password=password) as session:
            assert session.settings.browser.title == 'Permission denied'
    finally:
        User.delete({'login': login})


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


@tier3
def test_positive_update_email_delivery_method_sendmail(session):
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
    """
    property_name = "Email"
    mail_config_default_param = {
        "delivery_method": "",
        "email_reply_address": "",
        "email_subject_prefix": "",
        "sendmail_arguments": "",
        "sendmail_location": "",
        "send_welcome_email": "",
    }
    mail_config_default_param = {
        content: entities.Setting().search(query={'search': f'name={content}'})[0]
        for content in mail_config_default_param
    }
    mail_config_new_params = {
        "delivery_method": "Sendmail",
        "email_reply_address": f"root@{ssh.settings.server.hostname}",
        "email_subject_prefix": [gen_string('alpha')],
        "sendmail_location": "/usr/sbin/sendmail",
        "send_welcome_email": "Yes",
    }
    command = "grep " + f'{mail_config_new_params["email_subject_prefix"]}' + " /var/mail/root"

    with session:
        try:
            for mail_content, mail_content_value in mail_config_new_params.items():
                session.settings.update(mail_content, mail_content_value)
            test_mail_response = session.settings.send_test_mail(property_name)[0]
            assert test_mail_response == "Email was sent successfully"
            assert ssh.command(command).return_code == 0
        finally:
            for key, value in mail_config_default_param.items():
                setting_cleanup(setting_name=key, setting_value=value.value)


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

@tier2
def test_negative_update_hostname_with_empty_fact(session):
    """Update the Hostname_facts settings without any string(empty values)

    :id: e0eaab69-4926-4c1e-b111-30c51ede273e

    :Steps:

        1. Goto settings ->Discovered tab -> Hostname_facts
        2. Set empty hostname_facts (without any value)

    :expectedresults: Error should be raised on setting empty value for
        hostname_facts setting
    """
    property_name = "Discovered"
    discovery_config_default_param = { "discovery_hostname" : "" }
    discovery_config_default_param = {
        content: entities.Setting().search(query={'search': f'name='
                                                            f'{content}'})[
            0] for content in discovery_config_default_param
    }
    discovery_config_new_param = { "discovery_hostname" : ""}
    with session:
        try:
            for discovery_content, discovery_content_value in \
                    discovery_config_new_param.items():
                discovery_update_response = session.settings.update(
                    discovery_content, discovery_content_value)
            assert discovery_update_response != None, "Empty string accepted"
        finally:
            for discovery_content, discovery_content_value in \
                    discovery_config_default_param.items():
                setting_cleanup(setting_name=discovery_content,
                                setting_value=discovery_content_value.value)
