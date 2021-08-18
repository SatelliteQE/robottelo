"""Test class for Setting Parameter values

:Requirement: Setting

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Settings

:Assignee: desingh

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import math

import pytest
from airgun.session import Session
from fauxfactory import gen_url
from nailgun import entities

from robottelo import ssh
from robottelo.cleanup import setting_cleanup
from robottelo.cli.user import User
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import gen_string


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
    return content_view


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
@pytest.mark.parametrize('setting_update', ['restrict_composite_view'], indirect=True)
def test_positive_update_restrict_composite_view(session, setting_update, repo_setup):
    """Update settings parameter restrict_composite_view to Yes/True and ensure
    a composite content view may not be published or promoted, unless the component
    content view versions that it includes exist in the target environment.

    :id: a5d2d73d-064e-48af-ad62-da68e963e3ee

    :parametrized: yes

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical

    :CaseLevel: Acceptance
    """
    property_name = setting_update.name
    composite_cv = entities.ContentView(composite=True, organization=repo_setup['org']).create()
    content_view = add_content_views_to_composite(
        composite_cv, repo_setup['org'], repo_setup['repo']
    )
    composite_cv.publish()
    with session:
        session.organization.select(org_name=repo_setup['org'].name)
        for param_value in ['Yes', 'No']:
            session.settings.update(f'name = {property_name}', param_value)
            if param_value == 'Yes':
                with pytest.raises(AssertionError) as context:
                    session.contentview.promote(
                        composite_cv.name, 'Version 1.0', repo_setup['lce'].name
                    )
                    assert (
                        'Administrator -> Settings -> Content page using the '
                        'restrict_composite_view flag.' in str(context.value)
                    )
            else:
                result = session.contentview.promote(
                    composite_cv.name, 'Version 1.0', repo_setup['lce'].name
                )
                assert repo_setup['lce'].name in result['Environments']
                for content_view_name in [composite_cv.name, content_view.name]:
                    session.contentview.remove_version(content_view_name, 'Version 1.0')
                    session.contentview.delete(content_view_name)


@pytest.mark.skip_if_open("BZ:1677282")
@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['http_proxy'], indirect=True)
def test_positive_httpd_proxy_url_update(session, setting_update):
    """Update the http_proxy_url should pass successfully.

    :id: 593eb8e1-16dd-486b-a760-47b8fdf4dcb9

    :parametrized: yes

    :expectedresults: http_proxy_url updated successfully.

    :BZ: 1677282

    :Assignee: jpathan

    :CaseImportance: Medium

    """
    property_name = setting_update.name
    with session:
        param_value = gen_url(scheme='https')
        session.settings.update(f'name = {property_name}', param_value)
        result = session.settings.read(f'name = {property_name}')
        assert result['table'][0]['Value'] == param_value


@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['foreman_url', 'entries_per_page'], indirect=True)
def test_negative_validate_foreman_url_error_message(session, setting_update):
    """Updates some settings with invalid values (an exceptional tier2 test)

    :id: 7c75083d-1b4d-4744-aaa4-6fb9e93ab3c2

    :parametrized: yes

    :expectedresults: Parameter is not updated

    :CaseImportance: Medium
    """
    property_name = setting_update.name
    with session:
        invalid_value = [invalid_value for invalid_value in invalid_settings_values()][0]
        with pytest.raises(AssertionError) as context:
            session.settings.update(f'name = {property_name}', invalid_value)
            assert is_valid_error_message(str(context.value))


@pytest.mark.skip_if_open('BZ:1975713')
@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['host_dmi_uuid_duplicates'], indirect=True)
def test_positive_host_dmi_uuid_duplicates(session, setting_update):
    """Check the setting host_dmi_uuid_duplicates value update.

    :id: 529ddd3a-1271-4043-9006-eac436b08b11

    :parametrized: yes

    :BZ: 1975713

    :expectedresults: Value of host_dmi_uuid_duplicates should be updated successfully

    :CaseImportance: High
    """
    property_value = f'[ {gen_string("alpha")} ]'
    property_name = setting_update.name
    with session:
        session.settings.update(f'name = {setting_update.name}', property_value)
        result = session.settings.read(f'name = {property_name}')
        assert result['table'][0]['Value'] == property_value


@pytest.mark.tier2
@pytest.mark.parametrize(
    'setting_update', ['register_hostname_fact', 'content_view_solve_dependencies'], indirect=True
)
def test_positive_register_hostname_and_cvs_dependencies_update(session, setting_update):
    """Check the settings of register_hostname_fact & content_view_solve_dependencies value
       update.

    :id: 3d50c163-6a6d-494a-b0f2-1e1dd8a5c476

    :parametrized: yes

    :expectedresults: Value of register_hostname_fact and content_view_solve_dependencies
        should be updated successfully.

    :CaseImportance: High
    """
    property_dict = {
        "content_view_solve_dependencies": "Yes",
        "register_hostname_fact": gen_string('alpha'),
    }

    property_name = setting_update.name
    with session:
        session.settings.update(f'name = {property_name}', property_dict[setting_update.name])
        result = session.settings.read(f'name = {property_name}')
        assert result['table'][0]['Value'] == property_dict[setting_update.name]


@pytest.mark.tier3
@pytest.mark.parametrize('setting_update', ['login_text'], indirect=True)
def test_positive_update_login_page_footer_text_with_long_string(session, setting_update):
    """Testing to update parameter "Login_page_footer_text with long length
    string under General tab

    :id: b1a51594-43e6-49d8-918b-9bc306f3a1a2

    :steps:

        1. Navigate to Administer -> settings
        2. Click on general tab
        3. Input long length string into login page footer field
        4. Assert value from login page

    :parametrized: yes

    :expectedresults: Parameter is updated

    :CaseImportance: Medium

    :CaseLevel: Acceptance
    """
    property_name = setting_update.name
    login_text_data = gen_string('alpha', 270)
    with session:
        session.settings.update(f"name={property_name}", f"{login_text_data}")
        result = session.login.logout()
        assert result["login_text"] == login_text_data


@pytest.mark.tier3
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
            result = session.settings.permission_denied()
            assert (
                result == 'Permission denied You are not authorized to perform this action. '
                'Please request one of the required permissions listed below '
                'from a Satellite administrator: view_settings Back'
            )
    finally:
        User.delete({'login': login})


@pytest.mark.stubbed
@pytest.mark.tier3
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

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.upgrade
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

    :CaseAutomation: NotAutomated
    """


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
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


@pytest.mark.stubbed
@pytest.mark.tier3
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

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
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

    :CaseAutomation: NotAutomated
    """


@pytest.mark.skip_if_open("BZ:1989706")
@pytest.mark.tier2
@pytest.mark.parametrize('setting_update', ['discovery_hostname'], indirect=True)
def test_negative_update_hostname_with_empty_fact(session, setting_update):
    """Update the Hostname_facts settings without any string(empty values)

    :id: e0eaab69-4926-4c1e-b111-30c51ede273e

    :Steps:

        1. Goto settings ->Discovered tab -> Hostname_facts
        2. Set empty hostname_facts (without any value)

    :BZ: 1470083, 1989706

    :parametrized: yes

    :CaseImportance: Medium

    :expectedresults: Error should be raised on setting empty value for
        hostname_facts setting

    """
    new_hostname = ""
    property_name = setting_update.name
    with session:
        response = session.settings.update(property_name, new_hostname)
        assert response is not None, "Value can't be blank"


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
@pytest.mark.parametrize('setting_update', ['entries_per_page'], indirect=True)
def test_positive_entries_per_page(session, setting_update):
    """Update the per page entry in the settings.

    :id: 009026b6-7550-40aa-9f78-5eb7f7e3800f

    :Steps:
        1. Navigate to Administer > Settings > General tab
        2. Update the entries per page value
        3. GoTo Monitor > Tasks Table > Pagination
        4. Check the new per page entry is updated in pagination list
        5. Check the page count on the basis of the new updated entries per page.

    :parametrized: yes

    :customerscenario: true

    :expectedresults: New set entry-per-page should be available in the pagination list and
        page count should match according to the new setting

    :BZ: 1746221

    :CaseImportance: Medium

    :CaseLevel: Acceptance
    """
    property_name = setting_update.name
    property_value = 19
    with session:
        session.settings.update(f"name={property_name}", property_value)
        page_content = session.task.read_all(widget_names="Pagination")
        assert str(property_value) in page_content["Pagination"]["per_page"]
        total_pages = math.ceil(int(page_content["Pagination"]["total_items"]) / property_value)
        assert str(total_pages) == page_content["Pagination"]["pages"]
