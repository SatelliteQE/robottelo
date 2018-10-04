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
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import (
    ANY_CONTEXT,
    FAKE_0_YUM_REPO,
)
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    upgrade
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

        :caseautomation: notautomated

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

        :caseautomation: notautomated

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

        :caseautomation: notautomated

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

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @tier1
    def test_positive_sync_overview_widget(self):
        """Check if the Sync Overview Widget is working in the Dashboard UI

        :id: 515027f5-19e8-4f83-9042-1c347a63758f

        :Steps:

            1. Create a product
            2. Add a repo and sync it
            3. Navigate to Monitor -> Dashboard
            4. Review the Sync Overview widget for the above sync details

        :expectedresults: Sync Overview widget is updated with all sync
            processes

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(
            url=FAKE_0_YUM_REPO,
            content_type='yum',
            product=product,
        ).create()
        repo.sync()
        with Session(self) as session:
            set_context(session, org=org.name)
            self.assertEqual(
                self.dashboard.get_so_product_status(product.name),
                'Syncing Complete.'
            )

    @tier1
    def test_positive_current_subscription_totals(self):
        """Check if the Current Subscriptions Totals widget is working in the
        Dashboard UI

        :id: 6d0f56ff-7007-4cdb-96f3-d9e8b6cc1701

        :Steps:

            1. Make sure sat6 has some active subscriptions
            2. Navigate to Monitor -> Dashboard
            3. Review the Current Subscription Total widget

        :expectedresults: The widget displays all the active subscriptions and
            expired subscriptions details

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        with Session(self) as session:
            set_context(session, org=org.name)
            self.assertGreaterEqual(self.dashboard.get_cst_subs_count(
                'Active Subscriptions'), 1)
            self.assertEqual(self.dashboard.get_cst_subs_count(
                'Subscriptions Expiring in 120 Days'), 0)
            self.assertEqual(self.dashboard.get_cst_subs_count(
                'Recently Expired Subscriptions'), 0)

    @skip_if_bug_open('bugzilla', 1417114)
    @upgrade
    @tier2
    def test_positive_user_access_with_host_filter(self):
        """Check if user with necessary host permissions can access dashboard
        and required widgets are rendered

        :id: 24b4b371-cba0-4bc8-bc6a-294c62e0586d

        :Steps:

            1. Specify proper filter with permission for your role
            2. Create new user and assign role to it
            3. Login into application using this new user
            4. Check dashboard and widgets on it

        :expectedresults: Dashboard and Errata Widget rendered without errors

        :BZ: 1417114

        :CaseLevel: Integration
        """
        user_login = gen_string('alpha')
        user_password = gen_string('alphanumeric')
        org = entities.Organization().create()
        # create a role with necessary permissions
        role = entities.Role().create()
        entities.Filter(
            permission=entities.Permission(
                resource_type='Organization',
                name='view_organizations').search(),
            role=role,
            search=None
        ).create()
        entities.Filter(
            organization=[org],
            permission=entities.Permission(name='view_hosts').search(),
            role=role,
            search='compute_resource = RHEV'
        ).create()
        entities.Filter(
            permission=entities.Permission(
                resource_type=None, name='access_dashboard').search(),
            role=role,
            search=None
        ).create()
        # create a user and assign the above created role
        entities.User(
            default_organization=org,
            organization=[org],
            role=[role],
            login=user_login,
            password=user_password
        ).create()
        with Session(self, user_login, user_password):
            self.assertEqual(
                self.dashboard.get_total_hosts_count(), 0)
            self.assertIsNotNone(self.dashboard.get_widget('Latest Errata'))
            self.assertIsNotNone(self.dashboard.wait_until_element(
                locators['dashboard.latest_errata.empty']))

    @stubbed()
    @tier2
    def test_positive_run_distribution_widget(self):
        """Check if the Run distribution widget is working in the Dashboard UI

        :id: ed2205c6-9ba6-4b9a-895a-d6fa8157cb90

        :Steps:

            1. Navigate Monitor -> Dashboard
            2. Review the Run Distribution in the last 30 minutes widget

        :expectedresults: The widget shows appropriate data

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_latest_errata_widget(self):
        """Check if the Latest Errata widget is working in Dashboard the UI

        :id: 9012744f-9717-4d6e-a05c-bc7b4b1c1657

        :Steps:

            1. Make sure you have applied some errata to content host
            2. Navigate Monitor -> Dashboard
            3. Review the Latest Errata widget

        :expectedresults: The widget is updated with all errata related details

        :caseautomation: notautomated

        :CaseLevel: Integration
        """
