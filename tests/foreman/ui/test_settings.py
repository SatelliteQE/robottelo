"""Test class for Setting Parameter values

:Requirement: Setting

:CaseAutomation: Automated

:CaseComponent: Settings

:Team: Endeavour

:CaseImportance: High

"""

import math

from fauxfactory import gen_url
import pytest

from robottelo.config import settings
from robottelo.hosts import get_sat_version
from robottelo.utils.datafactory import filtered_datapoint, gen_string


@filtered_datapoint
def invalid_settings_values():
    """Returns a list of invalid settings values"""
    return [' ', '-1', 'text', '0']


def add_content_views_to_composite(composite_cv, org, repo, module_target_sat):
    """Add necessary number of content views to the composite one

    :param composite_cv: Composite content view object
    :param org: Organisation of satellite
    :param repo: repository need to added in content view
    """
    cv_version = []
    content_view = module_target_sat.api.ContentView(organization=org).create()
    content_view.publish()
    content_view.repository.append(repo)
    content_view.update(['repository'])
    cv_version.append(content_view.read().version[0])
    composite_cv.component = cv_version
    composite_cv.update(['component'])
    return content_view


@pytest.mark.run_in_one_thread
@pytest.mark.parametrize('setting_update', ['restrict_composite_view'], indirect=True)
def test_positive_update_restrict_composite_view(
    session, setting_update, repo_setup, module_target_sat
):
    """Update settings parameter restrict_composite_view to Yes/True and ensure
    a composite content view may not be published or promoted, unless the component
    content view versions that it includes exist in the target environment.

    :id: a5d2d73d-064e-48af-ad62-da68e963e3ee

    :parametrized: yes

    :expectedresults: Parameter is updated successfully

    :CaseImportance: Critical
    """
    property_name = setting_update.name
    composite_cv = module_target_sat.api.ContentView(
        composite=True, organization=repo_setup['org']
    ).create()

    content_view = add_content_views_to_composite(
        composite_cv, repo_setup['org'], repo_setup['repo'], module_target_sat
    )
    composite_cv.publish()
    with session:
        session.organization.select(org_name=repo_setup['org'].name)
        for param_value in ['Yes', 'No']:
            session.settings.update(f'name = {property_name}', param_value)
            if param_value == 'Yes':
                err_message = f"['Danger alert: The action requested on this composite view cannot be performed until all of the component content view versions have been promoted to the target environment: [\"{composite_cv.name}\"]. This restriction is optional and can be modified in the Administrator -> Settings -> Content page using the restrict_composite_view flag.']"
                result = session.contentview_new.promote(
                    composite_cv.name,
                    'version = 1',
                    repo_setup['lce'].name,
                    err_message=err_message,
                )
                assert (
                    'Administrator -> Settings -> Content page using the '
                    'restrict_composite_view flag.' in result[0]
                )
            else:
                result = session.contentview_new.promote(
                    composite_cv.name,
                    'version = 1',
                    repo_setup['lce'].name,
                )
                assert repo_setup['lce'].name in result['Environments']
                for content_view_name in [composite_cv.name, content_view.name]:
                    session.contentview_new.delete(content_view_name)


@pytest.mark.parametrize('setting_update', ['http_proxy'], indirect=True)
def test_positive_httpd_proxy_url_update(session, setting_update):
    """Update the http_proxy_url should pass successfully.

    :id: 593eb8e1-16dd-486b-a760-47b8fdf4dcb9

    :parametrized: yes

    :expectedresults: http_proxy_url updated successfully.

    :BZ: 1677282

    :CaseImportance: Medium
    """
    property_name = setting_update.name
    with session:
        param_value = gen_url(scheme='https')
        session.settings.update(f'name = {property_name}', param_value)
        result = session.settings.read(f'name = {property_name}')
        assert result['table'][0]['Value'] == param_value


@pytest.mark.parametrize('setting_update', ['foreman_url'], indirect=True)
def test_negative_validate_foreman_url_error_message(session, setting_update):
    """Updates some settings with invalid values

    :id: 7c75083d-1b4d-4744-aaa4-6fb9e93ab3c2

    :parametrized: yes

    :expectedresults: Parameter is not updated

    :CaseImportance: Medium
    """
    property_name = setting_update.name
    with session:
        invalid_value = [invalid_value for invalid_value in invalid_settings_values()][0]
        err_msg = 'URL must be valid and schema must be one of http and https, Invalid HTTP(S) URL'
        with pytest.raises(AssertionError) as context:
            session.settings.update(f'name = {property_name}', invalid_value)
        assert err_msg in str(context.value)


@pytest.mark.parametrize('setting_update', ['host_dmi_uuid_duplicates'], indirect=True)
def test_positive_host_dmi_uuid_duplicates(session, setting_update):
    """Check the setting host_dmi_uuid_duplicates value update.

    :id: 529ddd3a-1271-4043-9006-eac436b08b11

    :parametrized: yes

    :BZ: 1975713

    :expectedresults: Value of host_dmi_uuid_duplicates should be updated successfully

    :CaseImportance: High
    """
    property_value = gen_string('alpha')
    property_name = setting_update.name
    with session:
        session.settings.update(f'name = {property_name}', property_value)
        result = session.settings.read(f'name = {property_name}')
        assert result['table'][0]['Value'].strip('[]') == property_value


@pytest.mark.parametrize('setting_update', ['register_hostname_fact'], indirect=True)
def test_positive_register_hostname_fact_update(session, setting_update):
    """Check the settings of register_hostname_fact value update.

    :id: 3d50c163-6a6d-494a-b0f2-1e1dd8a5c476

    :parametrized: yes

    :expectedresults: Value of register_hostname_fact should be updated successfully.

    :CaseImportance: High
    """
    property_name = setting_update.name
    property_value = gen_string('alpha')
    with session:
        session.settings.update(f'name = {property_name}', property_value)
        result = session.settings.read(f'name = {property_name}')
        assert result['table'][0]['Value'] == property_value


@pytest.mark.parametrize('setting_update', ['login_text'], indirect=True)
def test_positive_update_login_page_footer_text(session, setting_update):
    """Testing to update parameter Login_page_footer_text with long length
    string & empty string under General tab

    :id: b1a51594-43e6-49d8-918b-9bc306f3a1a2

    :steps:

        1. Navigate to Administer -> settings
        2. Click on general tab
        3. Input long length string into login page footer field
        4. Assert value from login page
        5. Input default value into the login page footer field
        6. Assert default value from login page
        7. Input empty string into the login page footer field
        8. Assert empty value from login page

    :parametrized: yes

    :expectedresults: Parameter is updated

    :CaseImportance: Medium

    :customerscenario: true

    :BZ: 2157869
    """
    property_name = setting_update.name
    default_value = setting_update.default
    login_text_data = gen_string('alpha', 270)
    empty_str = ""
    login_details = {
        'username': settings.server.admin_username,
        'password': settings.server.admin_password,
    }
    with session:
        session.settings.update(f"name={property_name}", login_text_data)
        result = session.login.logout()
        assert result["login_text"] == login_text_data

        # change back to default (BZ#2157869)
        session.login.login(login_details)
        session.settings.update(f'name = {property_name}', default_value)
        result = session.login.logout()
        sat_version = get_sat_version()
        default_value_with_version_expanded = default_value.replace('$VERSION', str(sat_version))
        assert result["login_text"] == default_value_with_version_expanded

        # set empty
        session.login.login(login_details)
        session.settings.update(f"name={property_name}", empty_str)
        result = session.login.logout()
        assert not result["login_text"]


def test_negative_settings_access_to_non_admin(module_target_sat):
    """Check non admin users can't access Administer -> Settings tab

    :id: 34bb9376-c5fe-431a-ac0d-ef030c0ab50e

    :steps:

        1. Login with non admin user
        2. Check "Administer" tab is not present
        3. Navigate to /settings
        4. Check message permission denied is present

    :expectedresults: Administer -> Settings tab should not be available to non admin users

    :CaseImportance: Medium
    """
    login = gen_string('alpha')
    password = gen_string('alpha')
    module_target_sat.api.User(admin=False, login=login, password=password).create()
    try:
        with module_target_sat.ui_session(user=login, password=password) as session:
            result = session.settings.permission_denied()
            assert (
                result == 'Permission denied You are not authorized to perform this action. '
                'Please request one of the required permissions listed below '
                'from a Satellite administrator: view_settings Back'
            )
    finally:
        module_target_sat.cli.User.delete({'login': login})


@pytest.mark.stubbed
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

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
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

    :CaseAutomation: NotAutomated
    """


@pytest.mark.run_in_one_thread
def test_positive_update_email_delivery_method_sendmail(session, target_sat):
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

    :BZ: 2080324

    :CaseImportance: Critical
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
        content: target_sat.api.Setting().search(query={'search': f'name={content}'})[0]
        for content in mail_config_default_param
    }
    mail_config_new_params = {
        "delivery_method": "Sendmail",
        "email_reply_address": f"root@{target_sat.hostname}",
        "email_subject_prefix": gen_string('alpha'),
        "sendmail_location": "/usr/sbin/sendmail",
        "send_welcome_email": "Yes",
    }
    command = "grep " + f'{mail_config_new_params["email_subject_prefix"]}' + " /var/mail/root"
    if target_sat.execute('systemctl status postfix').status != 0:
        target_sat.execute('systemctl restart postfix')
    with session:
        try:
            for mail_content, mail_content_value in mail_config_new_params.items():
                session.settings.update(mail_content, mail_content_value)
            test_mail_response = session.settings.send_test_mail(property_name)[0]
            assert "Email was sent successfully" in test_mail_response
            assert target_sat.execute(command).status == 0
        finally:
            for key, value in mail_config_default_param.items():
                setting_entity = target_sat.api.Setting().search(query={'search': f'name={key}'})[0]
                setting_entity.value = value.value
                setting_entity.update({'value'})


@pytest.mark.stubbed
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

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
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

    :CaseAutomation: NotAutomated
    """


@pytest.mark.parametrize('setting_update', ['discovery_hostname'], indirect=True)
def test_negative_update_hostname_with_empty_fact(session, setting_update):
    """Update the Hostname_facts settings without any string(empty values)

    :id: e0eaab69-4926-4c1e-b111-30c51ede273e

    :steps:

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
        with pytest.raises(AssertionError) as context:
            session.settings.update(property_name, new_hostname)
        assert 'can\'t be blank' in str(context.value)


@pytest.mark.run_in_one_thread
@pytest.mark.parametrize('setting_update', ['entries_per_page'], indirect=True)
def test_positive_entries_per_page(session, setting_update):
    """Update the per page entry in the settings.

    :id: 009026b6-7550-40aa-9f78-5eb7f7e3800f

    :steps:
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
    """
    property_name = setting_update.name
    property_value = 19
    with session:
        session.settings.update(f"name={property_name}", property_value)
        page_content = session.task.read_all(widget_names="Pagination")
        assert str(property_value) in page_content["Pagination"]["_items"]
        total_pages_str = page_content["Pagination"]['_items'].split()[-2]
        total_pages = math.ceil(int(total_pages_str.split()[-1]) / property_value)
        assert str(total_pages) == page_content["Pagination"]['_total_pages'].split()[-1]


def test_positive_setting_display_fqdn_for_hosts(session, target_sat):
    """Verify setting display_fqdn_for_hosts set as Yes/No, and FQDN is used for host's name
    if it's set to Yes else not, according to setting set.

    :id: b1a51594-43e6-49d8-918b-9bc306f3a1a4

    :steps:
        1. Navigate to Monitor -> Dashboard
        2. Verify NewHosts table view contains host_name is w/ or w/o FQDN value
        3. Navigate to Hosts -> All Hosts -> <host> details page
        4. Verify host_name in breadcrumbs is w/ or w/o FQDN value

    :expectedresults: FQDN is used for hostname if setting is set to Yes(default),
        else hostname is present without FQDN.
    """
    host_name, domain_name = target_sat.hostname.split('.', 1)
    default_value = target_sat.update_setting('display_fqdn_for_hosts', 'No')
    try:
        with target_sat.ui_session() as session:
            dashboard_hosts = session.dashboard.read('NewHosts')
            assert host_name in [
                h['Host'] for h in dashboard_hosts['hosts'] if h['Host'] == host_name
            ]

            values = session.host_new.get_details(host_name, widget_names='breadcrumb')
            assert values['breadcrumb'] == host_name

            # Verify with display_fqdn_for_hosts=Yes
            target_sat.update_setting('display_fqdn_for_hosts', 'Yes')
            full_name = '.'.join((host_name, domain_name))
            dashboard_hosts = session.dashboard.read('NewHosts')
            assert full_name in [
                h['Host'] for h in dashboard_hosts['hosts'] if h['Host'] == full_name
            ]

            values = session.host_new.get_details(target_sat.hostname, widget_names='breadcrumb')
            assert values['breadcrumb'] == full_name
    finally:
        target_sat.update_setting('display_fqdn_for_hosts', default_value)


def test_positive_show_unsupported_templates(request, target_sat, module_org, module_location):
    """Verify setting show_unsupported_templates with new custom template

    :id: e0eaab69-4926-4c1e-b111-30c51ede273z

    :Steps:
        1. Goto Settings -> Provisioning tab -> Show unsupported provisioning templates

    :CaseImportance: Medium

    :expectedresults: Custom template aren't searchable when set to No,
        and are searchable when set to Yes(default)
    """
    pt = target_sat.api.ProvisioningTemplate(
        name=gen_string('alpha'),
        organization=[module_org],
        location=[module_location],
        template=gen_string('alpha'),
        snippet=False,
    ).create()
    request.addfinalizer(pt.delete)
    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        default_value = target_sat.update_setting('show_unsupported_templates', 'No')
        assert not session.provisioningtemplate.search(f'name={pt.name}')

        # Verify with show_unsupported_templates=Yes
        target_sat.update_setting('show_unsupported_templates', default_value)
        template = session.provisioningtemplate.search(f'name={pt.name}')
        assert template[0]['Name'] == pt.name
