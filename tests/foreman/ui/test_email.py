# -*- encoding: utf-8 -*-
"""UI Tests for the email notification feature"""

from robottelo.decorators import stubbed, tier1, tier3
from robottelo.test import UITestCase


class EmailTestCase(UITestCase):
    """UI Tests for the email notification feature"""

    @stubbed()
    @tier1
    def test_positive_preferences(self):
        """@Test: Manage user email notification preferences

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Attempt to enable and disable the following email notification
           preferences: Mail Enabled, Katello Sync Errata, Katello Host
           Advisory, Katello Promote Errata, Puppet Error state, Puppet
           Summary.

        @Assert: Enabling and disabling email notification preferences saved
        accordingly.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_sync_with_enabled_notification(self):
        """@Test: Receive email after every sync operation

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Enable notification for 'Katello Sync Errata'.
        3. Perform a sync operation on a product.

        @Assert: Email notification received after sync operation.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_sync_with_disabled_notification(self):
        """@Test: Do not receive email after every sync operation

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Disable notification by 'Katello Sync Errata' → 'No Emails'.
        3. Perform a sync operation on a product.

        @Assert: No email notification received after sync operation.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_promote_with_enabled_notification(self):
        """@Test: Receive email after every promote operation

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Enable notification for 'Katello Promote Errata'.
        3. Perform a promote operation in a content view.

        @Assert: Email notification received after Promote operation.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_promote_with_disabled_notification(self):
        """@Test: Do not receive email after every promote operation

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Disable notification by 'Katello Promote Errata' → 'No Emails'.
        3. Perform a promote operation in a content view.

        @Assert: No email notification received after Promote operation.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_host_with_daily_notification(self):
        """@Test: Receive daily email with host advisory information

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Enable notification for 'Katello Host Advisory' → Daily.

        @Assert: Email notification received daily with Katello Host Advisory
        information.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_host_with_weekly_notification(self):
        """@Test: Receive weekly email with host advisory information

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Enable notification for 'Katello Host Advisory' → Weekly.

        @Assert: Email notification received Weekly with Katello Host Advisory
        information.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_host_with_monthly_notification(self):
        """@Test: Receive monthly email with host advisory information

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Enable notification for 'Katello Host Advisory' → Monthly.

        @Assert: Email notification received monthly with Katello Host Advisory
        information.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_host_with_disabled_notification(self):
        """@Test: Receive no email with host advisory information

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Disable notification by 'Katello Host Advisory' → 'No emails'.

        @Assert: No email notification received with Katello Host Advisory
        information.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_puppet_error_with_enabled_notification(self):
        """@Test: Receive email after puppet error

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Enable notification for 'Puppet Error State'.
        3. Simulate a Puppet error.

        @Assert: Email notification received with Puppet error.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_puppet_error_with_disabled_notification(self):
        """@Test: Do not receive email after puppet error

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Disable notification by 'Puppet Error State' → 'No Emails'.
        3. Simulate a Puppet error.

        @Assert: No email notification received after Puppet error.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_sync_errata_notification(self):
        """@Test: Receive 'Katello Sync Errata' notifications - only for
        repositories and content views that the user has view access to

        @Feature: Email Notification

        @setup:

        1. Create multiple products with synced errata.
        2. The test user does not have view access to atleast some of the
           products.

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Enable notification for test user for 'Katello Sync Errata'.
        3. Login as admin and perform sync on a product for which the test user
           does not have view access.

        @Assert: Test user does not receive email notification.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_promote_errata_notification(self):
        """@Test: Receive 'Katello Promote Errata' notifications - only for
        repositories and content views that the user has view access to

        @Feature: Email Notification

        @setup:

        1. Create multiple products with synced errata.
        2. The test user does not have view access to atleast some of the
           products.

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Enable notification for the test user for 'Katello Promote Errata'.
        3. Login as admin and perform sync on a product for which the test user
           does not have view access.

        @Assert: Test user does not receive email notification.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_host_advisory_notification_for_cv_and_repo(self):
        """@Test: Receive 'Katello Host Advisory' notifications - only for
        repositories and content views that the user has view access to

        @Feature: Email Notification

        @setup:

        1. Create multiple products with synced errata.
        2. The test user does not have view access to atleast some of the
           products.

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Enable notification for the test user for 'Katello Host Advisory'.

        @Assert: Test user receives email notification with the host info for
        the repositories and content views that the user has access to.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_host_advisory_notification_for_host(self):
        """@Test: Receive 'Katello Host Advisory' notifications - only for
        content hosts that the user has view access to

        @Feature: Email Notification

        @setup:

        1. Make sure to have multiple content hosts
        2. The test user does not have view access to atleast some of the
           products

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Enable notification for test user for 'Katello Host Advisory'.

        @Assert: Test user receives email notification which does not list the
        content hosts for which the user does not have view access.

        @Status: Manual

        """
