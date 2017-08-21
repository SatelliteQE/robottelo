# -*- coding: utf-8 -*-
"""Test class for Notification Drawer

:Requirement: Notification Drawer

:CaseAutomation: notautomated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import stubbed, tier1, tier3, destructive
from robottelo.test import UITestCase


class NotificationDrawerTestCase(UITestCase):
    """Implements Notification Drawer UI test cases"""

    @stubbed()
    @tier1
    def test_positive_empty_notification_icon(self):
        """Check empty notification icon is shown when there is no notification

        :id: 6f5b7dfa-5607-4eee-b202-1954fefd1168

        :steps: Clear all existing notifications

        :expectedresults: Empty notification icon is shown

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_clear_notification(self):
        """Check a notification is deleted by clicking on "Clear" button
        within it

        :id: 62e0694c-82c8-45a7-9918-cf867366ed22

        :setup:
            1. provision a new host

        :steps:
            1. Open Notification Drawer
            2. Choose a notification
            3. Click on "Clear" within it

        :expectedresults: Assert chose notification is deleted from
            Notification Drawer

        :CaseImportance: Critical
        """

    @stubbed()
    @destructive
    def test_positive_notification_expiration(self):
        """Check a notification expires after 24 hours

        :id: 7fb71f80-cd85-4cb5-b498-92723f541238

        :setup:
            1. provision a new host
            2. advance system clock more than 24 hours

        :steps:
            1. Open Notification Drawer

        :expectedresults: Assert there is no notifications

        :teardown: reset back system clock

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_pending_notification_icon(self):
        """Check pending notification icon is shown when there is a new
        notification

        :id: c6fa095b-c604-4d73-a9c3-1162c02b8b71

        :setup: Trigger a notification by provisioning a new host

        :steps: Update browser

        :expectedresults: Assert pending notification icon is shown

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_discovery_system_notification(self):
        """Check a notification is listed when a discovery system become
        available

        :id: b09d142d-9d9c-47ab-af22-d85227cb412c

        :setup: Create a discovery system

        :steps: Open Notification Drawer

        :expectedresults: Assert notification regarding discovery system is
            listed

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_discovery_system_notification_link(self):
        """Check a discovery system notification has a "Detail link" which
        takes the user to the detail page of respective discovery system

        :id: 24e4cead-3c95-4030-9107-1fdcf5cd42b1

        :setup: Create a discovery system

        :steps:
            1. Open Notification Drawer
            2. Find a discovery system notification
            3. Click on "Detail link"

        :expectedresults: Assert Detail page from Discovery Link is available

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_discovery_system_notification_removal(self):
        """Check a discovery system notifications are removed once all
        discovery systems are deleted

        :id: 5e1cd508-fcde-4aac-891f-8ff41b4f1d16

        :setup:
            1. Create at least on discovery system
            2. Delete all discovery systems

        :steps:
            1. Open Notification Drawer

        :expectedresults: Assert no discovery system notification is listed

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_new_host_provisioned_notification(self):
        """Check a new host provisioned notification is listed when a new
        provisioning occurs

        :id: 2d6ee2a6-839c-4ee9-b992-44f02b594b5b

        :setup: provision a new host

        :steps:
            1. Open Notification Drawer

        :expectedresults: Assert a new host provisioned notification is listed

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_host_detail_notification_link(self):
        """Check a host notification has a "Detail link" which
        takes the user to the detail page of respective host

        :id: 4cdc8beb-057e-4799-bbbe-913812629911

        :setup: Provision a new host

        :steps:
            1. Open Notification Drawer
            2. Find new host notification
            3. Click on its "Detail link"

        :expectedresults: Assert Detail page from host is available

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_no_owner_warning_notification(self):
        """Check a warning notification is raised when a host is provisioned
        without a proper owner with proper fix link

        :id: 92789281-a424-4dfe-ae76-432b92b006cc

        :setup: Provision a new host without a proper owner

        :steps:
            1. Open Notification Drawer
            2. Find a warning notification due to host provision without owner
            3. Click on its "Update host page"

        :expectedresults: Assert "Update host page" is available so a user
            can be set

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_delete_host_notification(self):
        """Check a delete host notification is listed when a host is deleted

        :id: ceb5ac50-9b0e-4739-9d83-7ca56fa93b56

        :setup:
            1. provision a new host
            2. delete the host

        :steps:
            1. Open Notification Drawer

        :expectedresults: Assert a delete host notification is listed

        :CaseImportance: Critical
        """
