# -*- encoding: utf-8 -*-
"""UI Tests for the email notification feature"""

from robottelo.decorators import stubbed
from robottelo.test import UITestCase


class EmailTestCase(UITestCase):
    """UI Tests for the email notification feature"""

    @stubbed()
    def test_email_preference(self):
        """@Test: Manage user email notification preferences

        @Feature: Email Notification

        @Steps:

        1. Navigate to User → My Account → Mail Preferences.
        2. Attempt to enable and disable the following email notification
           preferences: Mail Enabled, Katello Sync Errata, Katello Host
           Advisory, Katello Promote Errata, Puppet Error state, Puppet
           Summary.

        @Assert: Enabling and disabling email notification preferences saved.
        accordingly.

        @Status: Manual

        """

    @stubbed()
    def test_email_sync_1(self):
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
    def test_email_sync_2(self):
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
    def test_email_promote_1(self):
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
    def test_email_promote_2(self):
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
    def test_email_host_1(self):
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
    def test_email_host_2(self):
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
    def test_email_host_3(self):
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
    def test_email_host_4(self):
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
    def test_email_puppet_error_1(self):
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
    def test_email_puppet_error_2(self):
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
    def test_email_permission_1(self):
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
    def test_email_permission_2(self):
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
    def test_email_permission_3(self):
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
    def test_email_permission_4(self):
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
