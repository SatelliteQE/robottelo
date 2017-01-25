"""Test module for Dashboard UI

@Requirement: Dashboard

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from robottelo.constants import ANY_CONTEXT
from robottelo.datafactory import gen_string
from robottelo.decorators import stubbed, tier1, tier2
from robottelo.test import UITestCase
from robottelo.ui.factory import set_context
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class DashboardTestCase(UITestCase):
    """Tests for Dashboard UI"""

    @tier1
    def test_positive_search_random(self):
        """Perform search on Dashboard using any random string

        @id: 28062a97-d642-41ac-b107-0b8a41eac478

        @Steps:

        1. Navigate to Monitor -> Dashboard
        2. Perform search using any random test string

        @BZ: 1391365

        @Assert: Check that we have zero as a result of search and any error is
        not raised
        """
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            self.assertEqual(self.dashboard.search(gen_string('alpha')), 0)
            self.assertIsNone(self.dashboard.wait_until_element(
                common_locators['alert.error'], timeout=3))

    @tier1
    def test_positive_search(self):
        """Check if the search box is working in the Dashboard UI

        @id: 1545580c-1f0e-4991-a400-4a6224199452

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Add a filter to search box (eg. environment)

        @Assert: Data displayed according to search box
        """
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            self.assertGreaterEqual(
                self.dashboard.search('production', 'environment'), 1)

    @stubbed()
    @tier1
    def test_positive_save(self):
        """Save the Dashboard UI

        @id: 0bd8560c-d612-49c7-83ee-558bbaa16bce

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to remove some widgets
        3.Select the Manage Dropdown box
        4.Save the Dashboard

        @Assert: Dashboard is saved successfully
        and the removed widgets does not appear.

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_reset(self):
        """Reset the Dashboard to default UI

        @id: 040c5910-a296-4cfc-ad1f-1b4fc9be8199

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to remove some widgets
        3.Select the Manage Dropdown box
        4.Save the Dashboard
        5.Dashboard Widgets are saved successfully
        6.Click Reset to default

        @Assert: Widget positions successfully saved.

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_add_widgets(self):
        """Add Widgets to the Dashboard UI

        @id: ec57d051-83d9-4c11-84ff-4de292784fc1

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Select Manage Dropdown box
        3.Add Widgets

        @Assert: User is able to add widgets.

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_search_bookmark(self):
        """Bookmark the search filter in Dashboard UI

        @id: f9e6259e-2b97-46fc-b357-26ea5ea8d16c

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Add a filter to search box (eg. environment)
        3.Bookmark the search filter

        @Assert: User is able to list the Bookmark

        @caseautomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_host_configuration_status(self):
        """Check if the Host Configuration Status
        Widget links are working

        @id: ffb0a6a1-2b65-4578-83c7-61492122d865

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Host Configuration Status
        3.Navigate to each of the links which has
        search string associated with it.

        @Assert: Each link shows the right info

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_host_configuration_chart(self):
        """Check if the Host Configuration Chart
        is working in the Dashboard UI

        @id: b03314aa-4394-44e5-86da-c341c783003d

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Host Configuration Chart widget
        3.Navigate to each of the links which
        has search string associated with it.

        @Assert: Each link shows the right info

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_task_status(self):
        """Check if the Task Status is
        working in the Dashboard UI

        @id: fb667d6a-7255-4341-9f79-2f03d19e8e0f

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Task Status widget
        3.Click each link

        @Assert: Each link shows the right info

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_latest_warning_error_tasks(self):
        """Check if the Latest Warning/Error
        Tasks Status are working in the Dashboard UI

        @id: c90df864-1472-4b7c-91e6-9ea9e98384a9

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Latest Warning/Error Tasks widget.

        @Assert: The links to all failed/warnings tasks are working

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_content_view_history(self):
        """Check if the Content View History
        are working in the Dashboard UI

        @id: cb63a67d-7cca-4d2c-9abf-9f4f5e92c856

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Content View History widget

        @Assert: Each Content View link shows its current status
        (the environment to which it is published)

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_discovered_hosts(self):
        """Check if the user can access Discovered
        Host Widget in the Dashboard UI

        @id: 1e06af1b-c21f-42a9-a432-2ed18e0b225f

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Discovered Hosts widget
        3.Click on the list of Discovered Hosts

        @Assert: It takes you to discovered hosts

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_latest_events_widget(self):
        """Check if the Latest Events Widget
        is working in the Dashboard UI

        @id: 6ca2f113-bf15-406a-8b15-77c377048ac6

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Latest Events widget

        @Assert: The Widget is updated with
        all the latest events

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_positive_sync_overview_widget(self):
        """Check if the Sync Overview Widget
        is working in the Dashboard UI

        @id: 515027f5-19e8-4f83-9042-1c347a63758f

        @Steps:

        1.Create a product
        2.Add a repo and sync it
        3.Navigate to Monitor -> Dashboard
        4.Review the Sync Overview widget
        for the above sync details

        @Assert: Sync Overview widget is
        updated with all sync processes

        @caseautomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_content_host_subscription_status(self):
        """Check if the Content Host Subscription Status
        is working in the Dashboard UI

        @id: ce0d7b0c-ae6a-4361-8173-e50f6381194a

        @Steps:

        1.Register Content Host and subscribe it
        2.Navigate Monitor -> Dashboard
        3.Review the Content Host Subscription Status
        4.Click each link :
          a.Invalid Subscriptions
          b.Insufficient Subscriptions
          c.Current Subscriptions

        @Assert: The widget is updated with all details for Current,
        Invalid and Insufficient Subscriptions

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_positive_current_subscription_totals(self):
        """Check if the Current Subscriptions Totals widget
        is working in the Dashboard UI

        @id: 6d0f56ff-7007-4cdb-96f3-d9e8b6cc1701

        @Steps:

        1.Make sure sat6 has some active subscriptions
        2.Navigate to Monitor -> Dashboard
        3.Review the Current Subscription Total widget

        @Assert: The widget displays all the active
        subscriptions and expired subscriptions details

        @caseautomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_host_collections(self):
        """Check if the Host Collections widget
        displays list of host collection in UI

        @id: 1feae601-987d-4553-8644-4ceef5059e64

        @Steps:

        1.Make sure to have some hosts and host collections
        2.Navigate Monitor -> Dashboard
        3.Review the Host Collections Widget

        @Assert: The list of host collections along
        with content host is displayed in the widget

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_run_distribution_widget(self):
        """Check if the Run distribution widget is
        working in the Dashboard UI

        @id: ed2205c6-9ba6-4b9a-895a-d6fa8157cb90

        @Steps:

        1.Navigate Monitor -> Dashboard
        2.Review the Run Distribution
        in the last 30 minutes widget

        @Assert: The widget shows appropriate data

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_latest_errata_widget(self):
        """Check if the Latest Errata widget is
        working in Dashboard the UI

        @id: 9012744f-9717-4d6e-a05c-bc7b4b1c1657

        @Steps:

        1.Make sure you have applied some errata to content host
        2.Navigate Monitor -> Dashboard
        3.Review the Latest Errata widget

        @Assert: The widget is updated with
        all errata related details

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @stubbed()
    @tier1
    def test_positive_remove_widget(self):
        """Check if the user is able to remove widget
        in the Dashboard UI

        @id: 25c6e9e8-a7b6-4aa4-96dd-0d303e0c3aa0

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to remove some widget

        @Assert: Widget is removed
        The widget is listed under Manage -> Add Widget

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_add_removed_widget(self):
        """Check if the user is able to add removed
        widget in the Dashboard UI

        @id: 156f559f-bb23-480f-bdf0-5dd2ee545fa9

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to remove some widget
        3.Widget is removed
        4.The widget is listed under Manage -> Add Widget
        5.Click to add the widget back

        @Assert: The widget is added back to the Dashboard

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_minimize_widget(self):
        """Check if the user is able to minimize the widget
        in the Dashboard UI

        @id: 21f10b30-b121-4347-807d-7b949a3f0e4f

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to minimize some widget

        @Assert: Widget is minimized
        The widget is listed under Manage -> Restore Widget

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_restore_minimize_widget(self):
        """Check if the user is able to restoring the minimized
        widget in the Dashboard UI

        @id: f42fdcce-26fb-4c56-ac4e-1e00b077bd78

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to minimize some widget
        3.Widget is minimized
        4.The widget is listed
        under Manage -> Restore Widget
        5.Click to add the widget back

        @Assert: The widget is added
        back to the Dashboard

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_toggle_auto_refresh(self):
        """Check if the user is able to Toggle
        Auto refresh in the Dashboard UI

        @id: 2cbb2f2c-ddf2-492a-bda1-904c30da0de3

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Click Auto Refresh ON/OFF

        @Assert: The auto refresh functionality
        works as per the set value.

        @caseautomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_clear_search_box(self):
        """Check if the user is able to clear the
        search box in the Dashboard UI

        @id: 97335970-dc1a-485d-aeb2-de6ece2197c3

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Add a filter to search box (eg. environment)
        3.Data displayed according to search box
        4.On left side of the box click
        the Clear cross sign

        @Assert: Search box is cleared

        @caseautomation: notautomated
        """
