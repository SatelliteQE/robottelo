"""Test class for Sync Plan UI"""

from datetime import datetime, timedelta
from ddt import ddt, data
from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import SYNC_INTERVAL
from robottelo.decorators import skip_if_bug_open
from robottelo.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_syncplan
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@ddt
class Syncplan(UITestCase):
    """Implements Sync Plan tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(Syncplan, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @data(
        {
            u'name': gen_string('alpha'),
            u'desc': gen_string('alpha'),
            u'interval': SYNC_INTERVAL['hour']
        },
        {
            u'name': gen_string('numeric'),
            u'desc': gen_string('numeric'),
            u'interval': SYNC_INTERVAL['hour']
        },
        {
            u'name': gen_string('alphanumeric'),
            u'desc': gen_string('alphanumeric'),
            u'interval': SYNC_INTERVAL['hour']
        },
        {
            u'name': gen_string('utf8'),
            u'desc': gen_string('utf8'),
            u'interval': SYNC_INTERVAL['hour']
        },
        {
            u'name': gen_string('html', 20),
            u'desc': gen_string('html'),
            u'interval': SYNC_INTERVAL['hour']
        },
        {
            u'name': gen_string('alphanumeric'),
            u'desc': gen_string('alphanumeric'),
            u'interval': SYNC_INTERVAL['day']
        },
        {
            u'name': gen_string('utf8'),
            u'desc': gen_string('utf8'),
            u'interval': SYNC_INTERVAL['day']
        },
        {
            u'name': gen_string('alpha'),
            u'desc': gen_string('alpha'),
            u'interval': SYNC_INTERVAL['week']
        },
        {
            u'name': gen_string('utf8'),
            u'desc': gen_string('utf8'),
            u'interval': SYNC_INTERVAL['week']
        },
        {
            u'name': gen_string('html'),
            u'desc': gen_string('html'),
            u'interval': SYNC_INTERVAL['week']
        }
    )
    def test_positive_create_basic(self, test_data):
        """@Test: Create Sync Plan with minimal input parameters

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created

        """
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=test_data['name'],
                description=test_data['desc'],
                sync_interval=test_data['interval'],
            )
            self.assertIsNotNone(self.syncplan.search(test_data['name']))

    def test_positive_create_with_start_time(self):
        """@Test: Create Sync plan with specified start time

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

    @skip_if_bug_open('bugzilla', 1246262)
    def test_positive_create_with_start_date(self):
        """@Test: Create Sync plan with specified start date

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created with the specified date

        @BZ: 1246262

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

    @data('', '   ')
    def test_negative_create_with_blank_name(self, name):
        """@Test: Create Sync Plan with blank and whitespace in name

        @Feature: Content Sync Plan - Negative Create

        @Assert: Sync Plan is not created

        """
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=name,
                submit_validate=False,
            )
            self.assertIsNotNone(self.syncplan.wait_until_element(
                common_locators['common_invalid']))

    @data(*generate_strings_list(len1=256))
    def test_negative_create_with_too_long_name(self, name):
        """@Test: Create Sync Plan with 256 characters in name

        @Feature: Content Sync Plan - Negative Create

        @Assert: Sync Plan is not created with more than 255 chars

        """
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=name,
                description='more than 255 chars',
                submit_validate=False,
            )
            self.assertIsNotNone(self.syncplan.wait_until_element(
                common_locators['common_invalid']))

    @data(*generate_strings_list())
    def test_negative_create_with_same_name(self, name):
        """@Test: Create Sync Plan with an existing name

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan cannot be created with existing name

        """
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=name,
            )
            self.assertIsNotNone(self.syncplan.search(name))
            make_syncplan(
                session,
                org=self.organization.name,
                name=name,
                description='with same name',
                submit_validate=False,
            )
            self.assertIsNotNone(self.syncplan.wait_until_element(
                common_locators['common_invalid']))

    @data(*generate_strings_list())
    def test_positive_update_name(self, new_plan_name):
        """@Test: Update Sync plan's name

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
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_sync_plans()
            self.syncplan.update(plan_name, new_name=new_plan_name)
            self.assertIsNotNone(self.syncplan.search(new_plan_name))

    @data(
        SYNC_INTERVAL['hour'],
        SYNC_INTERVAL['day'],
        SYNC_INTERVAL['week'],
    )
    def test_positive_update_interval(self, new_interval):
        """@Test: Update Sync plan's interval

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
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_sync_plans()
            self.syncplan.update(
                name, new_sync_interval=new_interval)
            session.nav.go_to_sync_plans()
            self.syncplan.search(name).click()
            self.syncplan.wait_for_ajax()
            # Assert updated sync interval
            interval_text = self.syncplan.wait_until_element(
                locators['sp.fetch_interval']).text
            self.assertEqual(interval_text, new_interval)

    @data(*generate_strings_list())
    def test_positive_update_product(self, plan_name):
        """@Test: Update Sync plan and associate products

        @Feature: Content Sync Plan - Positive Update add products

        @Assert: Sync Plan has the associated product

        """
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
            # Assert product is associated with sync plan
            self.syncplan.click(tab_locators['sp.tab_products'])
            element = self.syncplan.wait_until_element(
                (strategy, value % product.name))
            self.assertIsNotNone(element)

    def test_positive_update_and_disassociate_product(self):
        """@Test: Update Sync plan and disassociate products

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

    @data(*generate_strings_list())
    def test_positive_delete(self, plan_name):
        """@Test: Delete a Sync plan

        @Feature: Content Sync Plan - Positive Delete

        @Assert: Sync Plan is deleted

        """
        entities.SyncPlan(
            name=plan_name,
            interval=SYNC_INTERVAL['day'],
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_sync_plans()
            self.syncplan.delete(plan_name)
            self.assertIsNone(self.syncplan.search(plan_name))
