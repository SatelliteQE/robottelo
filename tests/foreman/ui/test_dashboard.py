"""Test module for Dashboard UI"""
from robottelo.decorators import stubbed, tier1, tier2
from robottelo.test import UITestCase


class DashboardTestCase(UITestCase):
    """Tests for Dashboard UI"""

    @stubbed()
    @tier1
    def test_positive_save(self):
        """Save the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to remove some widgets
        3.Select the Manage Dropdown box
        4.Save the Dashboard

        @Assert: Dashboard is saved successfully
        and the removed widgets does not appear.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_reset(self):
        """Reset the Dashboard to default UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to remove some widgets
        3.Select the Manage Dropdown box
        4.Save the Dashboard
        5.Dashboard Widgets are saved successfully
        6.Click Reset to default

        @Assert: Widget positions successfully saved.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_add_widgets(self):
        """Add Widgets to the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Select Manage Dropdown box
        3.Add Widgets

        @Assert: User is able to add widgets.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_search_bookmark(self):
        """Bookmark the search filter in Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Add a filter to search box (eg. environment)
        3.Bookmark the search filter

        @Assert: User is able to list the Bookmark

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_host_configuration_status(self):
        """Check if the Host Configuration Status
        Widget links are working

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Host Configuration Status
        3.Navigate to each of the links which has
        search string associated with it.

        @Assert: Each link shows the right info

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_host_configuration_chart(self):
        """Check if the Host Configuration Chart
        is working in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Host Configuration Chart widget
        3.Navigate to each of the links which
        has search string associated with it.

        @Assert: Each link shows the right info

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_task_status(self):
        """Check if the Task Status is
        working in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Task Status widget
        3.Click each link

        @Assert: Each link shows the right info

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_latest_warning_error_tasks(self):
        """Check if the Latest Warning/Error
        Tasks Status are working in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Latest Warning/Error Tasks widget.

        @Assert: The links to all failed/warnings tasks are working

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_content_view_history(self):
        """Check if the Content View History
        are working in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Content View History widget

        @Assert: Each Content View link shows its current status
        (the environment to which it is published)

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_discovered_hosts(self):
        """Check if the user can access Discovered
        Host Widget in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Discovered Hosts widget
        3.Click on the list of Discovered Hosts

        @Assert: It takes you to discovered hosts

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_latest_events_widget(self):
        """Check if the Latest Events Widget
        is working in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Review the Latest Events widget

        @Assert: The Widget is updated with
        all the latest events

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_sync_overview_widget(self):
        """Check if the Sync Overview Widget
        is working in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Create a product
        2.Add a repo and sync it
        3.Navigate to Monitor -> Dashboard
        4.Review the Sync Overview widget
        for the above sync details

        @Assert: Sync Overview widget is
        updated with all sync processes

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_content_host_subscription_status(self):
        """Check if the Content Host Subscription Status
        is working in the Dashboard UI

        @Feature: Dashboard

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

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_current_subscription_totals(self):
        """Check if the Current Subscriptions Totals widget
        is working in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Make sure sat6 has some active subscriptions
        2.Navigate to Monitor -> Dashboard
        3.Review the Current Subscription Total widget

        @Assert: The widget displays all the active
        subscriptions and expired subscriptions details

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_host_collections(self):
        """Check if the Host Collections widget
        displays list of host collection in UI

        @Feature: Dashboard

        @Steps:

        1.Make sure to have some hosts and host collections
        2.Navigate Monitor -> Dashboard
        3.Review the Host Collections Widget

        @Assert: The list of host collections along
        with content host is displayed in the widget

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_run_distribution_widget(self):
        """Check if the Run distribution widget is
        working in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate Monitor -> Dashboard
        2.Review the Run Distribution
        in the last 30 minutes widget

        @Assert: The widget shows appropriate data

        @Status: Manual
        """

    @stubbed()
    @tier2
    def test_positive_latest_errata_widget(self):
        """Check if the Latest Errata widget is
        working in Dashboard the UI

        @Feature: Dashboard

        @Steps:

        1.Make sure you have applied some errata to content host
        2.Navigate Monitor -> Dashboard
        3.Review the Latest Errata widget

        @Assert: The widget is updated with
        all errata related details

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_remove_widget(self):
        """Check if the user is able to remove widget
        in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to remove some widget

        @Assert: Widget is removed
        The widget is listed under Manage -> Add Widget

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_add_removed_widget(self):
        """Check if the user is able to add removed
        widget in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to remove some widget
        3.Widget is removed
        4.The widget is listed under Manage -> Add Widget
        5.Click to add the widget back

        @Assert: The widget is added back to the Dashboard

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_minimize_widget(self):
        """Check if the user is able to minimize the widget
        in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to minimize some widget

        @Assert: Widget is minimized
        The widget is listed under Manage -> Restore Widget

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_restore_minimize_widget(self):
        """Check if the user is able to restoring the minimized
        widget in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Try to minimize some widget
        3.Widget is minimized
        4.The widget is listed
        under Manage -> Restore Widget
        5.Click to add the widget back

        @Assert: The widget is added
        back to the Dashboard

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_toggle_auto_refresh(self):
        """Check if the user is able to Toggle
        Auto refresh in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Click Auto Refresh ON/OFF

        @Assert: The auto refresh functionality
        works as per the set value.

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_search(self):
        """Check if the search box is working
        in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Add a filter to search box (eg. environment)

        @Assert: Data displayed according to search box

        @Status: Manual
        """

    @stubbed()
    @tier1
    def test_positive_clear_search_box(self):
        """Check if the user is able to clear the
        search box in the Dashboard UI

        @Feature: Dashboard

        @Steps:

        1.Navigate to Monitor -> Dashboard
        2.Add a filter to search box (eg. environment)
        3.Data displayed according to search box
        4.On left side of the box click
        the Clear cross sign

        @Assert: Search box is cleared

        @Status: Manual
        """
