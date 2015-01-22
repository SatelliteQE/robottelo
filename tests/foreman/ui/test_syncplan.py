"""Test class for Sync Plan UI"""

from ddt import ddt
from datetime import datetime, timedelta
from fauxfactory import gen_string
from robottelo import entities
from robottelo.common.constants import SYNC_INTERVAL
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.common.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_syncplan
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@ddt
class Syncplan(UITestCase):
    """Implements Sync Plan tests in UI"""

    @classmethod
    def setUpClass(cls):
        org_attrs = entities.Organization().create()
        cls.org_name = org_attrs['name']
        cls.org_id = org_attrs['id']

        super(Syncplan, cls).setUpClass()

    @data({u'name': gen_string('alpha', 10),
           u'desc': gen_string('alpha', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': gen_string('numeric', 10),
           u'desc': gen_string('numeric', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': gen_string('alphanumeric', 10),
           u'desc': gen_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': gen_string('utf8', 10),
           u'desc': gen_string('utf8', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': gen_string('html', 20),
           u'desc': gen_string('html', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': gen_string('alpha', 10),
           u'desc': gen_string('alpha', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': gen_string('numeric', 10),
           u'desc': gen_string('numeric', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': gen_string('alphanumeric', 10),
           u'desc': gen_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': gen_string('utf8', 10),
           u'desc': gen_string('utf8', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': gen_string('html', 20),
           u'desc': gen_string('html', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': gen_string('alpha', 10),
           u'desc': gen_string('alpha', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': gen_string('numeric', 10),
           u'desc': gen_string('numeric', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': gen_string('alphanumeric', 10),
           u'desc': gen_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': gen_string('utf8', 10),
           u'desc': gen_string('utf8', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': gen_string('html', 20),
           u'desc': gen_string('html', 10),
           u'interval': SYNC_INTERVAL['week']})
    def test_positive_create_1(self, test_data):
        """@Test: Create Sync Plan with minimal input parameters

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created

        """
        with Session(self.browser) as session:
            make_syncplan(session, org=self.org_name,
                          name=test_data['name'],
                          description=test_data['desc'],
                          sync_interval=test_data['interval'])
            self.assertIsNotNone(self.syncplan.search(test_data['name']))

    @skip_if_bug_open('bugzilla', 1131661)
    def test_positive_create_2(self):
        """@Test: Create Sync plan with specified start time

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created with the specified time.

        @BZ: 1131661

        """
        locator = locators["sp.fetch_startdate"]
        plan_name = gen_string("alpha", 8)
        description = "sync plan create with start date"
        current_date = datetime.now()
        startdate = current_date + timedelta(minutes=10)
        starthour = startdate.strftime("%H")
        startminute = startdate.strftime("%M")
        # Formatting current_date to web-UI format "%b %d, %Y %I:%M:%S %p" and
        # removed zero-padded date(%-d) and hrs(%l) as fetching via web-UI
        # doesn't have it
        formatted_date_time = startdate.strftime("%b %-d, %Y %l:%M:%S %p")
        # Removed the seconds info as it would be too quick to validate via UI.
        starttime = formatted_date_time.rpartition(':')[0]
        with Session(self.browser) as session:
            make_syncplan(session, org=self.org_name, name=plan_name,
                          description=description, start_hour=starthour,
                          start_minute=startminute)
            self.assertIsNotNone(self.syncplan.search(plan_name))
            self.syncplan.search(plan_name).click()
            self.syncplan.wait_for_ajax()
            starttime_text = self.syncplan.wait_until_element(locator).text
            # Removed the seconds info as it would be too quick
            # to validate via UI.
            saved_starttime = str(starttime_text).rpartition(':')[0]
            self.assertEqual(saved_starttime, starttime)

    @skip_if_bug_open('bugzilla', 1131661)
    def test_positive_create_3(self):
        """@Test: Create Sync plan with specified start date

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created with the specified date

        @BZ: 1131661

        """
        locator = locators["sp.fetch_startdate"]
        plan_name = gen_string("alpha", 8)
        description = "sync plan create with start date"
        current_date = datetime.now()
        startdate = current_date + timedelta(days=10)
        startdate_str = startdate.strftime("%Y-%m-%d")
        current_date_time = startdate.strftime("%b %-d, %Y %I:%M:%S %p")
        # validating only for date
        fetch_startdate = current_date_time.rpartition(',')[0]
        with Session(self.browser) as session:
            make_syncplan(session, org=self.org_name, name=plan_name,
                          description=description, startdate=startdate_str)
            self.assertIsNotNone(self.syncplan.search(plan_name))
            self.syncplan.search(plan_name).click()
            self.syncplan.wait_for_ajax()
            startdate_text = self.syncplan.wait_until_element(locator).text
            saved_startdate = str(startdate_text).rpartition(',')[0]
            self.assertEqual(saved_startdate, fetch_startdate)

    @data("", "  ")
    def test_negative_create_1(self, name):
        """@Test: Create Sync Plan with blank and whitespace in name

        @Feature: Content Sync Plan - Negative Create

        @Assert: Sync Plan is not created
        """
        locator = common_locators["common_invalid"]
        with Session(self.browser) as session:
            make_syncplan(session, org=self.org_name, name=name,
                          submit_validate=False)
            invalid = self.syncplan.wait_until_element(locator)
            self.assertIsNotNone(invalid)

    @skip_if_bug_open('bugzilla', 1087425)
    @data(*generate_strings_list(len1=256))
    def test_negative_create_2(self, name):
        """@Test: Create Sync Plan with 256 characters in name

        @Feature: Content Sync Plan - Negative Create

        @Assert: Sync Plan is not created with more than 255 chars

        @BZ: 1087425

        """
        locator = common_locators["common_haserror"]
        description = "more than 255 chars"
        with Session(self.browser) as session:
            make_syncplan(session, org=self.org_name, name=name,
                          description=description, submit_validate=False)
            error = self.syncplan.wait_until_element(locator)
            self.assertIsNotNone(error)

    @data(*generate_strings_list())
    def test_negative_create_3(self, name):
        """@Test: Create Sync Plan with an existing name

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan cannot be created with existing name

        @BZ: 1087425

        """
        description = "with same name"
        # TODO: Due to bug 1087425 using common_haserror instead of name_error
        locator = common_locators["common_haserror"]
        with Session(self.browser) as session:
            make_syncplan(session, org=self.org_name, name=name)
            self.assertIsNotNone(self.syncplan.search(name))
            make_syncplan(session, org=self.org_name, name=name,
                          description=description, submit_validate=False)
            error = self.syncplan.wait_until_element(locator)
            self.assertIsNotNone(error)

    @data(*generate_strings_list())
    def test_positive_update_1(self, plan_name):
        """@Test: Update Sync plan's name

        @Feature: Content Sync Plan - Positive Update name

        @Assert: Sync Plan's name is updated

        """
        new_plan_name = gen_string("alpha", 8)
        entities.Organization(id=self.org_id).sync_plan(
            name=plan_name,
            interval=SYNC_INTERVAL['day']
        )
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_sync_plans()
            self.syncplan.update(plan_name, new_name=new_plan_name)
            self.assertIsNotNone(self.syncplan.search(new_plan_name))

    @data({u'name': gen_string('alpha', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': gen_string('numeric', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': gen_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': gen_string('utf8', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': gen_string('html', 20),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': gen_string('alpha', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': gen_string('numeric', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': gen_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': gen_string('utf8', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': gen_string('html', 20),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': gen_string('alpha', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': gen_string('numeric', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': gen_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': gen_string('utf8', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': gen_string('html', 20),
           u'interval': SYNC_INTERVAL['week']})
    def test_positive_update_2(self, test_data):
        """@Test: Update Sync plan's interval

        @Feature: Content Sync Plan - Positive Update interval

        @Assert: Sync Plan's interval is updated

        """
        locator = locators["sp.fetch_interval"]
        entities.Organization(id=self.org_id).sync_plan(
            name=test_data['name'],
            interval=SYNC_INTERVAL['day']
        )
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_sync_plans()
            self.syncplan.update(test_data['name'],
                                 new_sync_interval=test_data['interval'])
            session.nav.go_to_sync_plans()
            self.syncplan.search(test_data['name']).click()
            self.syncplan.wait_for_ajax()
            # Assert updated sync interval
            interval_text = self.syncplan.wait_until_element(locator).text
            self.assertEqual(interval_text, test_data['interval'])

    @data(*generate_strings_list())
    def test_positive_update_3(self, plan_name):
        """@Test: Update Sync plan and associate products

        @Feature: Content Sync Plan - Positive Update add products

        @Assert: Sync Plan has the associated product

        """
        strategy, value = locators["sp.prd_select"]
        product_name = entities.Product(
            organization=self.org_id
        ).create()['name']
        entities.Organization(id=self.org_id).sync_plan(
            name=plan_name,
            interval=SYNC_INTERVAL['week']
        )
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_sync_plans()
            self.syncplan.update(plan_name, add_products=[product_name])
            self.syncplan.search(plan_name).click()
            self.syncplan.wait_for_ajax()
            # Assert product is associated with sync plan
            self.syncplan.wait_until_element(
                tab_locators["sp.tab_products"]).click()
            self.syncplan.wait_for_ajax()
            element = self.syncplan.wait_until_element(
                (strategy, value % product_name))
            self.assertIsNotNone(element)

    @data(*generate_strings_list())
    def test_positive_update_4(self, plan_name):
        """@Test: Update Sync plan and disassociate products

        @Feature: Content Sync Plan - Positive Update remove products

        @Assert: Sync Plan does not have the associated product

        """
        strategy, value = locators["sp.prd_select"]
        product_name = entities.Product(
            organization=self.org_id
        ).create()['name']
        entities.Organization(id=self.org_id).sync_plan(
            name=plan_name,
            interval=SYNC_INTERVAL['week']
        )
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_sync_plans()
            self.syncplan.update(plan_name, add_products=[product_name])
            self.syncplan.search(plan_name).click()
            self.syncplan.wait_for_ajax()
            self.syncplan.wait_until_element(
                tab_locators["sp.tab_products"]).click()
            self.syncplan.wait_for_ajax()
            element = self.syncplan.wait_until_element(
                (strategy, value % product_name))
            self.assertIsNotNone(element)
            # Dis-associate the product from sync plan and the selected product
            # should automatically move from 'List/Remove` tab to 'Add' tab
            self.syncplan.update(plan_name, rm_products=[product_name])
            self.syncplan.search(plan_name).click()
            self.syncplan.wait_for_ajax()
            self.syncplan.wait_until_element(
                tab_locators["sp.tab_products"]).click()
            self.syncplan.wait_for_ajax()
            self.syncplan.wait_until_element(
                tab_locators["sp.add_prd"]).click()
            self.syncplan.wait_for_ajax()
            element = self.syncplan.wait_until_element(
                (strategy, value % product_name))
            self.assertIsNotNone(element)

    @data(*generate_strings_list())
    def test_positive_delete_1(self, plan_name):
        """@Test: Delete a Sync plan

        @Feature: Content Sync Plan - Positive Delete

        @Assert: Sync Plan is deleted

        """
        entities.Organization(id=self.org_id).sync_plan(
            name=plan_name,
            interval=SYNC_INTERVAL['day']
        )
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_sync_plans()
            self.syncplan.delete(plan_name)
            self.assertIsNone(self.syncplan.search(plan_name))
