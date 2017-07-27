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
