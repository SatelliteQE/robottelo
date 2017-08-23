# -*- encoding: utf-8 -*-
"""UI Tests for the email notification feature

:Requirement: Email

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import stubbed, tier1, tier3, upgrade
from robottelo.test import UITestCase


class EmailTestCase(UITestCase):
    """UI Tests for the email notification feature"""

    @stubbed()
    @tier1
    def test_positive_preferences(self):
        """Manage user email notification preferences

        :id: 6852256e-4907-454d-bb53-242063222a1f

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Attempt to enable and disable the following email notification
                preferences: Mail Enabled, Katello Sync Errata, Katello Host
                Advisory, Katello Promote Errata, Puppet Error state, Puppet
                Summary.

        :expectedresults: Enabling and disabling email notification preferences
            saved accordingly.

        :caseautomation: notautomated


        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_sync_with_enabled_notification(self):
        """Receive email after every sync operation

        :id: 79ed2bc9-3707-4548-bdab-290ae5e9abf3

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Enable notification for 'Katello Sync Errata'.
            3. Perform a sync operation on a product.

        :expectedresults: Email notification received after sync operation.

        :caseautomation: notautomated


        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_sync_with_disabled_notification(self):
        """Do not receive email after every sync operation

        :id: c0b8b5d6-ed44-42b7-9700-1dd26bb4ae55

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Disable notification by 'Katello Sync Errata' → 'No Emails'.
            3. Perform a sync operation on a product.

        :expectedresults: No email notification received after sync operation.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_promote_with_enabled_notification(self):
        """Receive email after every promote operation

        :id: cb14b622-cbfd-4834-889d-bc6e7884bfb0

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Enable notification for 'Katello Promote Errata'.
            3. Perform a promote operation in a content view.

        :expectedresults: Email notification received after Promote operation.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_promote_with_disabled_notification(self):
        """Do not receive email after every promote operation

        :id: 4cca1869-f869-414b-b652-d6a5b3ce6f17

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Disable notification by 'Katello Promote Errata' → 'No Emails'.
            3. Perform a promote operation in a content view.

        :expectedresults: No email notification received after Promote
            operation.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_host_with_daily_notification(self):
        """Receive daily email with host advisory information

        :id: 3a21d0ef-3c67-4e47-bcec-a8dd1a5aa564

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Enable notification for 'Katello Host Advisory' → Daily.

        :expectedresults: Email notification received daily with Katello Host
            Advisory information.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_host_with_weekly_notification(self):
        """Receive weekly email with host advisory information

        :id: b195fc2e-0449-4cb3-9f4c-ed8c8266651b

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Enable notification for 'Katello Host Advisory' → Weekly.

        :expectedresults: Email notification received Weekly with Katello Host
            Advisory information.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_host_with_monthly_notification(self):
        """Receive monthly email with host advisory information

        :id: e05398b9-6fbd-4aa5-84e9-70ae0a2db9a1

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Enable notification for 'Katello Host Advisory' → Monthly.

        :expectedresults: Email notification received monthly with Katello Host
            Advisory information.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_host_with_disabled_notification(self):
        """Receive no email with host advisory information

        :id: 5540ba69-aab0-42a3-afda-298249880348

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Disable notification by 'Katello Host Advisory' → 'No emails'.

        :expectedresults: No email notification received with Katello Host
            Advisory information.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_puppet_error_with_enabled_notification(self):
        """Receive email after puppet error

        :id: 2c14a0d9-2f37-47da-b095-0c984a24091d

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Enable notification for 'Puppet Error State'.
            3. Simulate a Puppet error.

        :expectedresults: Email notification received with Puppet error.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_puppet_error_with_disabled_notification(self):
        """Do not receive email after puppet error

        :id: fd6e7274-b9c1-44f8-91de-ad5162f21c74

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Disable notification by 'Puppet Error State' → 'No Emails'.
            3. Simulate a Puppet error.

        :expectedresults: No email notification received after Puppet error.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_sync_errata_notification(self):
        """Receive 'Katello Sync Errata' notifications - only for
        repositories and content views that the user has view access to

        :id: b0e4a823-4225-4788-8cfd-2d1ccf4d9ded

        :setup:

            1. Create multiple products with synced errata.
            2. The test user does not have view access to atleast some of the
                products.

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Enable notification for test user for 'Katello Sync Errata'.
            3. Login as admin and perform sync on a product for which the test
                user does not have view access.

        :expectedresults: Test user does not receive email notification.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_promote_errata_notification(self):
        """Receive 'Katello Promote Errata' notifications - only for
        repositories and content views that the user has view access to

        :id: 44435f4f-ea9f-4f6e-b1c0-d273974ec9e5

        :setup:

            1. Create multiple products with synced errata.
            2. The test user does not have view access to atleast some of the
                products.

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Enable notification for the test user for 'Katello Promote
                Errata'.
            3. Login as admin and perform sync on a product for which the test
                user does not have view access.

        :expectedresults: Test user does not receive email notification.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_host_advisory_notification_for_cv_and_repo(self):
        """Receive 'Katello Host Advisory' notifications - only for
        repositories and content views that the user has view access to

        :id: aea2cfa7-0a44-4b72-bd10-275e604100a9

        :setup:

            1. Create multiple products with synced errata.
            2. The test user does not have view access to atleast some of the
                products.

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Enable notification for the test user for 'Katello Host
                Advisory'.

        :expectedresults: Test user receives email notification with the host
            info for the repositories and content views that the user has
            access to.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_host_advisory_notification_for_host(self):
        """Receive 'Katello Host Advisory' notifications - only for
        content hosts that the user has view access to

        :id: 2acc2979-926a-4176-b87a-57bc880e4b31

        :setup:

            1. Make sure to have multiple content hosts
            2. The test user does not have view access to atleast some of the
                products

        :Steps:

            1. Navigate to User → My Account → Mail Preferences.
            2. Enable notification for test user for 'Katello Host Advisory'.

        :expectedresults: Test user receives email notification which does not
            list the content hosts for which the user does not have view
            access.

        :caseautomation: notautomated

        :CaseLevel: System
        """
