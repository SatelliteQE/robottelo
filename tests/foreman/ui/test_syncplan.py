"""Test class for Sync Plan UI"""

from datetime import datetime, timedelta
from fauxfactory import gen_string
from nailgun import entities
from random import randint
from robottelo.constants import SYNC_INTERVAL
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import run_only_on, stubbed, tier1, tier2
from robottelo.test import UITestCase
from robottelo.ui.factory import make_syncplan
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


def valid_sync_intervals():
    """Returns a list of valid sync intervals"""
    return [
        SYNC_INTERVAL['hour'],
        SYNC_INTERVAL['day'],
        SYNC_INTERVAL['week'],
    ]


class SyncPlanTestCase(UITestCase):
    """Implements Sync Plan tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(SyncPlanTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create Sync Plan with valid name values

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description=gen_string('utf8'),
                        sync_interval=valid_sync_intervals()[randint(0, 2)],
                    )
                    self.assertIsNotNone(self.syncplan.search(name))

    @tier1
    def test_positive_create_with_description(self):
        """Create Sync Plan with valid desc values

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created
        """
        with Session(self.browser) as session:
            for desc in generate_strings_list():
                with self.subTest(desc):
                    name = gen_string('utf8')
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description=desc,
                        sync_interval=valid_sync_intervals()[randint(0, 2)],
                    )
                    self.assertIsNotNone(self.syncplan.search(name))

    @tier1
    def test_positive_create_with_sync_interval(self):
        """Create Sync Plan with valid sync intervals

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created
        """
        with Session(self.browser) as session:
            for interval in valid_sync_intervals():
                with self.subTest(interval):
                    name = gen_string('alphanumeric')
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description=name,
                        sync_interval=interval,
                    )
                    self.assertIsNotNone(self.syncplan.search(name))

    @tier2
    def test_positive_create_with_start_time(self):
        """Create Sync plan with specified start time

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created with the specified time.
        """
        plan_name = gen_string('alpha')
        startdate = datetime.now() + timedelta(minutes=10)
        # Formatting current_date to web-UI format "%b %d, %Y %I:%M:%S %p" and
        # removed zero-padded date(%-d) and hrs(%l) as fetching via web-UI
        # doesn't have it
        formatted_date_time = startdate.strftime("%b %-d, %Y %-l:%M:%S %p")
        # Removed the seconds info as it would be too quick to validate via UI.
        starttime = formatted_date_time.rpartition(':')[0]
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start time',
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
            )
            self.assertIsNotNone(self.syncplan.search(plan_name))
            self.syncplan.search(plan_name).click()
            self.syncplan.wait_for_ajax()
            starttime_text = self.syncplan.wait_until_element(
                locators['sp.fetch_startdate']).text
            # Removed the seconds info as it would be too quick
            # to validate via UI.
            saved_starttime = str(starttime_text).rpartition(':')[0]
            self.assertEqual(saved_starttime, starttime)

    @tier2
    def test_positive_create_with_start_date(self):
        """Create Sync plan with specified start date

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created with the specified date
        """
        plan_name = gen_string('alpha')
        startdate = datetime.now() + timedelta(days=10)
        startdate_str = startdate.strftime("%Y-%m-%d")
        current_date_time = startdate.strftime("%b %-d, %Y %I:%M:%S %p")
        # validating only for date
        fetch_startdate = current_date_time.rpartition(',')[0]
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start date',
                startdate=startdate_str,
            )
            self.assertIsNotNone(self.syncplan.search(plan_name))
            self.syncplan.search(plan_name).click()
            self.syncplan.wait_for_ajax()
            startdate_text = self.syncplan.wait_until_element(
                locators['sp.fetch_startdate']).text
            saved_startdate = str(startdate_text).rpartition(',')[0]
            self.assertEqual(saved_startdate, fetch_startdate)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Sync Plan with invalid names

        @Feature: Content Sync Plan - Negative Create

        @Assert: Sync Plan is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description='invalid name',
                    )
                    self.assertIsNotNone(self.syncplan.wait_until_element(
                        common_locators['common_invalid']))

    @tier1
    def test_negative_create_with_same_name(self):
        """Create Sync Plan with an existing name

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan cannot be created with existing name
        """
        name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_syncplan(session, org=self.organization.name, name=name)
            self.assertIsNotNone(self.syncplan.search(name))
            make_syncplan(
                session,
                org=self.organization.name,
                name=name,
                description='with same name',
            )
            self.assertIsNotNone(self.syncplan.wait_until_element(
                common_locators['common_invalid']))

    @tier1
    def test_positive_update_name(self):
        """Update Sync plan's name

        @Feature: Content Sync Plan - Positive Update name

        @Assert: Sync Plan's name is updated
        """
        plan_name = gen_string('alpha')
        entities.SyncPlan(
            name=plan_name,
            interval=SYNC_INTERVAL['day'],
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            for new_plan_name in generate_strings_list():
                with self.subTest(new_plan_name):
                    session.nav.go_to_select_org(self.organization.name)
                    session.nav.go_to_sync_plans()
                    self.syncplan.update(plan_name, new_name=new_plan_name)
                    self.assertIsNotNone(self.syncplan.search(new_plan_name))
                    plan_name = new_plan_name  # for next iteration

    @tier1
    def test_positive_update_interval(self):
        """Update Sync plan's interval

        @Feature: Content Sync Plan - Positive Update interval

        @Assert: Sync Plan's interval is updated
        """
        name = gen_string('alpha')
        entities.SyncPlan(
            name=name,
            interval=SYNC_INTERVAL['day'],
            organization=self.organization,
            enabled=True,
        ).create()
        with Session(self.browser) as session:
            for new_interval in valid_sync_intervals():
                with self.subTest(new_interval):
                    session.nav.go_to_select_org(self.organization.name)
                    session.nav.go_to_sync_plans()
                    self.syncplan.update(name, new_sync_interval=new_interval)
                    session.nav.go_to_sync_plans()
                    self.syncplan.search(name).click()
                    # Assert updated sync interval
                    interval_text = self.syncplan.wait_until_element(
                        locators['sp.fetch_interval']
                    ).text
                    self.assertEqual(interval_text, new_interval)

    @tier2
    def test_positive_update_product(self):
        """Update Sync plan and associate products

        @Feature: Content Sync Plan - Positive Update add products

        @Assert: Sync Plan has the associated product
        """
        strategy, value = locators['sp.prd_select']
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for plan_name in generate_strings_list():
                with self.subTest(plan_name):
                    entities.SyncPlan(
                        name=plan_name,
                        interval=SYNC_INTERVAL['week'],
                        organization=self.organization,
                    ).create()
                    session.nav.go_to_select_org(self.organization.name)
                    session.nav.go_to_sync_plans()
                    self.syncplan.update(
                        plan_name, add_products=[product.name])
                    self.syncplan.search(plan_name).click()
                    # Assert product is associated with sync plan
                    self.syncplan.click(tab_locators['sp.tab_products'])
                    element = self.syncplan.wait_until_element(
                        (strategy, value % product.name))
                    self.assertIsNotNone(element)

    @tier2
    def test_positive_update_and_disassociate_product(self):
        """Update Sync plan and disassociate products

        @Feature: Content Sync Plan - Positive Update remove products

        @Assert: Sync Plan does not have the associated product
        """
        plan_name = gen_string('utf8')
        strategy, value = locators['sp.prd_select']
        product = entities.Product(organization=self.organization).create()
        entities.SyncPlan(
            name=plan_name,
            interval=SYNC_INTERVAL['week'],
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_sync_plans()
            self.syncplan.update(plan_name, add_products=[product.name])
            self.syncplan.search(plan_name).click()
            self.syncplan.wait_for_ajax()
            self.syncplan.click(tab_locators['sp.tab_products'])
            element = self.syncplan.wait_until_element(
                (strategy, value % product.name))
            self.assertIsNotNone(element)
            # Dis-associate the product from sync plan and the selected product
            # should automatically move from 'List/Remove` tab to 'Add' tab
            self.syncplan.update(plan_name, rm_products=[product.name])
            self.syncplan.search(plan_name).click()
            self.syncplan.wait_for_ajax()
            self.syncplan.click(tab_locators['sp.tab_products'])
            self.syncplan.click(tab_locators['sp.add_prd'])
            element = self.syncplan.wait_until_element(
                (strategy, value % product.name))
            self.assertIsNotNone(element)

    @tier1
    def test_positive_delete(self):
        """Delete an existing Sync plan

        @Feature: Content Sync Plan - Positive Delete

        @Assert: Sync Plan is deleted successfully
        """
        with Session(self.browser) as session:
            for plan_name in generate_strings_list():
                with self.subTest(plan_name):
                    entities.SyncPlan(
                        name=plan_name,
                        interval=SYNC_INTERVAL['day'],
                        organization=self.organization,
                    ).create()
                    session.nav.go_to_select_org(self.organization.name)
                    self.syncplan.delete(plan_name)

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_create_ostree_sync_plan(self):
        """Create a sync plan for ostree contents.

        @Feature: ostree sync plan

        @Assert: sync plan should be created successfully

        @Status: Manual
        """
