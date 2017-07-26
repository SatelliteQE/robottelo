# -*- encoding: utf-8 -*-
"""Test class for Setting Parameter values

:Requirement: Setting

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import tier1, stubbed
from robottelo.test import CLITestCase


class SettingTestCase(CLITestCase):
    """Implements tests for Settings for CLI"""

    @stubbed()
    @tier1
    def test_negative_update_hostname_with_empty_fact(self):
        """Update the Hostname_facts settings without any string(empty values)

        :id: daca0746-75ad-42fb-97ed-6db0224eeeac

        :expectedresults: Error should be raised on setting empty value for
            hostname_facts setting

        :caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_update_hostname_prefix_without_value(self):
        """Update the Hostname_prefix settings without any string(empty values)

        :id: a84c28ea-6821-4c31-b4ab-8662c22c9135

        :expectedresults: Hostname_prefix should be set without any text

        :caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_update_hostname_default_prefix(self):
        """Update the default set prefix of hostname_prefix setting

        :id: a6e46e53-6273-406a-8009-f184d9551d66

        :expectedresults: Default set prefix should be updated with new value

        :caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_update_hostname_default_facts(self):
        """Update the default set fact of hostname_facts setting with list of
        facts like: bios_vendor,uuid

        :id: 1042c5e2-ee4d-4eaf-a0b2-86c000a79dfb

        :expectedresults: Default set fact should be updated with facts list.

        :caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_discover_host_with_invalid_prefix(self):
        """Update the hostname_prefix with invalid string like
        -mac, 1mac or ^%$

        :id: 73c5da42-28c8-4be7-8fb1-f505fefd6665

        :expectedresults: Validation error should be raised on updating
            hostname_prefix with invalid string, should start w/ letter

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_update_login_page_footer_text(self):
        """Updates parameter "login_text" in settings

        :id: 4d4e1151-5bd6-4fa2-8dbb-e182b43ad7ec

        :steps:

            1. Execute "settings" command with "set" as sub-command
            with any string

        :expectedresults: Parameter is updated successfully

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_update_login_page_footer_text_without_value(self):
        """Updates parameter "login_text" without any string (empty value)

        :id: 01ce95de-2994-42b6-b9f8-f7882981fb69

        :steps:

            1. Execute "settings" command with "set" as sub-command
            without any string(empty value) in value parameter

        :expectedresults: Message on login screen should be removed

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_negative_update_login_page_footer_text(self):
        """Attempt to update parameter "Login_page_footer_text"
            with invalid value(long length) under General tab

        :id: 87ef6b19-fdc5-4541-aba8-e730f1a3caa7

        :steps:

            1. Execute "settings" command with "set" as sub-command
            with invalid string(long length)

        :expectedresults: Parameter is not updated

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_update_email_delivery_method_smtp(self):
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

        :CaseImportance: Critical

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_update_email_delivery_method_sendmail(self):
        """Check Updating Sendmail params through settings subcommand

        :id: 578de898-fde2-4957-b39a-9dd059f490bf

        :steps:
            1. set "delivery_method" to sendmail
            2. set all sendmail related properties:
                2.1. sendmail_arguments
                2.2. sendmail_location

        :expectedresults: Sendmail properties are updated

        :CaseImportance: Critical

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_update_email_reply_address(self):
        """Check email reply address is updated

        :id: cb0907d1-9cb6-45c4-b2bb-e2790ea55f16

        :expectedresults: email_reply_address is updated

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_negative_update_email_reply_address(self):
        """Check email reply address is not updated

        :id: 2a2220c2-badf-47d5-ba3f-e6329930ab39

        :steps: provide invalid email addresses

        :expectedresults: email_reply_address is not updated

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_update_email_subject_prefix(self):
        """Check email subject prefix is updated

        :id: c8e6b323-7b39-43d6-a9f1-5474f920bba2

        :expectedresults: email_subject_prefix is updated

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_negative_update_email_subject_prefix(self):
        """Check email subject prefix not

        :id: 8a638596-248f-4196-af36-ad2982196382

        :steps: provide invalid prefix, like string with more than 255 chars

        :expectedresults: email_subject_prefix is not updated

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_positive_update_send_welcome_email(self):
        """Check email send welcome email is updated

        :id: cdaf6cd0-5eea-4252-87c5-f9ec3ba79ac1

        :steps: valid values: boolean true or false

        :expectedresults: send_welcome_email is updated

        :caseautomation: notautomated
        """

    @stubbed
    @tier1
    def test_negative_update_send_welcome_email(self):
        """Check email send welcome email is updated

        :id: 2f75775d-72a1-4b2f-86c2-98c36e446099

        :steps: set invalid values: not booleans

        :expectedresults: send_welcome_email is not updated

        :caseautomation: notautomated
        """
