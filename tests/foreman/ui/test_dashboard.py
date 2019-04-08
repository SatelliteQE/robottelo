"""Test module for Dashboard UI

:Requirement: Dashboard

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities
from robottelo.constants import ANY_CONTEXT
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    run_in_one_thread,
    stubbed,
    tier1,
    tier2,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import set_context
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


class DashboardTestCase(UITestCase):
    """Tests for Dashboard UI"""

    @tier1
    def test_positive_search_random(self):
        """Perform search on Dashboard using any random string

        :id: 28062a97-d642-41ac-b107-0b8a41eac478

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Perform search using any random test string

        :BZ: 1391365

        :expectedresults: Check that we have zero as a result of search and any
            error is not raised

        :CaseImportance: Critical
        """
        with Session(self) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            self.assertEqual(self.dashboard.search(gen_string('alpha')), 0)
            self.assertIsNone(self.dashboard.wait_until_element(
                common_locators['alert.error'], timeout=3))

    @tier1
    def test_positive_search(self):
        """Check if the search box is working in the Dashboard UI

        :id: 1545580c-1f0e-4991-a400-4a6224199452

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Add a filter to search box (eg. environment)

        :expectedresults: Data displayed according to search box

        :CaseImportance: Critical
        """
        with Session(self) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            self.assertGreaterEqual(
                self.dashboard.search('production', 'environment'), 1)

    @tier1
    def test_positive_clear_search_box(self):
        """Check if the user is able to clear the search box in the Dashboard
        UI

        :id: 97335970-dc1a-485d-aeb2-de6ece2197c3

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Add a filter to search box (eg. environment)
            3. Data displayed according to search box
            4. On left side of the box click the Clear cross sign

        :expectedresults: Search box is cleared

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        entities.Host(organization=org).create()
        host = entities.Host(organization=org).create()
        with Session(self) as session:
            set_context(session, org=org.name)
            self.assertEqual(
                self.dashboard.search(host.name, 'name'), 1)
            self.dashboard.clear_search_box()
            self.dashboard.click(common_locators['search_button'])
            self.assertEqual(
                self.dashboard.get_total_hosts_count(), 2)

    @run_in_one_thread
    @tier1
    def test_positive_remove_widget(self):
        """Check if the user is able to remove widget in the Dashboard UI

        :id: 25c6e9e8-a7b6-4aa4-96dd-0d303e0c3aa0

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Try to remove some widget

        :expectedresults: Widget is removed and is not present on Dashboard

        :CaseImportance: Critical
        """
        with Session(self):
            self.dashboard.remove_widget('Latest Events')
            self.assertIsNone(self.dashboard.get_widget('Latest Events'))

    @run_in_one_thread
    @tier1
    def test_positive_save(self):
        """Save the Dashboard UI

        :id: 0bd8560c-d612-49c7-83ee-558bbaa16bce

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Try to remove some widgets
            3. Select the Manage Dropdown box
            4. Save the Dashboard

        :expectedresults: Dashboard is saved successfully and the removed
            widgets does not appear.

        :CaseImportance: Critical
        """
        with Session(self):
            self.dashboard.remove_widget('Host Configuration Chart')
            self.dashboard.manage_widget('Save Dashboard')
            self.assertIsNone(
                self.dashboard.get_widget('Host Configuration Chart'))

    @run_in_one_thread
    @tier1
    def test_positive_reset(self):
        """Reset the Dashboard to default UI

        :id: 040c5910-a296-4cfc-ad1f-1b4fc9be8199

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Try to remove some widgets
            3. Select the Manage Dropdown box
            4. Save the Dashboard
            5. Dashboard Widgets are saved successfully
            6. Click Reset to default

        :expectedresults: Widget positions successfully saved.

        :CaseImportance: Critical
        """
        with Session(self):
            self.dashboard.remove_widget('Task Status')
            self.dashboard.manage_widget('Save Dashboard')
            self.assertIsNone(self.dashboard.get_widget('Task Status'))
            self.dashboard.manage_widget('Reset Dashboard')
            self.assertIsNotNone(self.dashboard.get_widget('Task Status'))

    @stubbed()
    @tier1
    def test_positive_add_widgets(self):
        """Add Widgets to the Dashboard UI

        :id: ec57d051-83d9-4c11-84ff-4de292784fc1

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Select Manage Dropdown box
            3. Add Widgets

        :expectedresults: User is able to add widgets.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @run_in_one_thread
    @tier1
    def test_positive_add_removed_widget(self):
        """Check if the user is able to add removed
        widget in the Dashboard UI

        :id: 156f559f-bb23-480f-bdf0-5dd2ee545fa9

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Try to remove some widget
            3. Widget is removed
            4. The widget is listed under Manage -> Add Widget
            5. Click to add the widget back

        :expectedresults: The widget is added back to the Dashboard

        :CaseImportance: Critical
        """
        with Session(self):
            for widget in ['Discovered Hosts', 'Content Views']:
                self.dashboard.remove_widget(widget)
                self.dashboard.manage_widget('Save Dashboard')
                self.dashboard.manage_widget('Add Widget', widget)
                self.assertIsNotNone(self.dashboard.get_widget(widget))

    @tier1
    def test_positive_toggle_auto_refresh(self):
        """Check if the user is able to Toggle Auto refresh in the Dashboard UI

        :id: 2cbb2f2c-ddf2-492a-bda1-904c30da0de3

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Click Auto Refresh ON/OFF

        :expectedresults: The auto refresh functionality works as per the set
            value.

        :CaseImportance: Critical
        """
        with Session(self):
            self.dashboard.navigate_to_entity()
            self.assertEqual(
                self.browser.current_url.split('/')[-1],
                '?auto_refresh=0'
            )
            self.dashboard.click(locators['dashboard.auto_refresh'])
            self.browser.refresh()
            self.dashboard.wait_for_ajax()
            self.assertEqual(
                self.browser.current_url.split('/')[-1],
                '?auto_refresh=1'
            )

    @stubbed()
    @tier1
    def test_positive_search_bookmark(self):
        """Bookmark the search filter in Dashboard UI

        :id: f9e6259e-2b97-46fc-b357-26ea5ea8d16c

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Add a filter to search box (eg. environment)
            3. Bookmark the search filter

        :expectedresults: User is able to list the Bookmark

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier2
    def test_positive_discovered_hosts(self):
        """Check if the user can access Discovered Host Widget in the Dashboard
        UI

        :id: 1e06af1b-c21f-42a9-a432-2ed18e0b225f

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Review the Discovered Hosts widget
            3. Click on the list of Discovered Hosts

        :expectedresults: It takes you to discovered hosts

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_latest_events_widget(self):
        """Check if the Latest Events Widget is working in the Dashboard UI

        :id: 6ca2f113-bf15-406a-8b15-77c377048ac6

        :Steps:

            1. Navigate to Monitor -> Dashboard
            2. Review the Latest Events widget

        :expectedresults: The Widget is updated with all the latest events

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_run_distribution_widget(self):
        """Check if the Run distribution widget is working in the Dashboard UI

        :id: ed2205c6-9ba6-4b9a-895a-d6fa8157cb90

        :Steps:

            1. Navigate Monitor -> Dashboard
            2. Review the Run Distribution in the last 30 minutes widget

        :expectedresults: The widget shows appropriate data

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """
