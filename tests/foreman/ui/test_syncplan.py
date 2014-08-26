"""
Test class for Sync Plan UI
"""

from datetime import datetime, timedelta

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common.constants import SYNC_INTERVAL
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.common.helpers import generate_string, generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_org
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@ddt
class Syncplan(UITestCase):
    """
    Implements Sync Plan tests in UI
    """

    org_name = None

    def setUp(self):
        super(Syncplan, self).setUp()
        # Make sure to use the Class' org_name instance
        if Syncplan.org_name is None:
            Syncplan.org_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=Syncplan.org_name)

    def configure_syncplan(self):
        """
        Configures sync plan in UI
        """
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_sync_plans()

    @attr('ui', 'syncplan', 'implemented')
    @data({u'name': generate_string('alpha', 10),
           u'desc': generate_string('alpha', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': generate_string('numeric', 10),
           u'desc': generate_string('numeric', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': generate_string('alphanumeric', 10),
           u'desc': generate_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': generate_string('utf8', 10),
           u'desc': generate_string('utf8', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': generate_string('html', 20),
           u'desc': generate_string('html', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': generate_string('alpha', 10),
           u'desc': generate_string('alpha', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': generate_string('numeric', 10),
           u'desc': generate_string('numeric', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': generate_string('alphanumeric', 10),
           u'desc': generate_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': generate_string('utf8', 10),
           u'desc': generate_string('utf8', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': generate_string('html', 20),
           u'desc': generate_string('html', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': generate_string('alpha', 10),
           u'desc': generate_string('alpha', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': generate_string('numeric', 10),
           u'desc': generate_string('numeric', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': generate_string('alphanumeric', 10),
           u'desc': generate_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': generate_string('utf8', 10),
           u'desc': generate_string('utf8', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': generate_string('html', 20),
           u'desc': generate_string('html', 10),
           u'interval': SYNC_INTERVAL['week']})
    def test_positive_create_1(self, test_data):
        """
        @Feature: Content Sync Plan - Positive Create
        @Test: Create Sync Plan with minimal input parameters
        @Assert: Sync Plan is created
        """

        self.configure_syncplan()
        self.syncplan.create(test_data['name'], description=test_data['desc'],
                             sync_interval=test_data['interval'])
        self.assertIsNotNone(self.products.search(test_data['name']))

    @skip_if_bug_open('bugzilla', 1087425)
    @attr('ui', 'syncplan', 'implemented')
    @data(*generate_strings_list())
    def test_positive_create_2(self, name):
        """
        @Feature: Content Sync Plan - Positive Create
        @Test: Create Sync Plan with same input parameters
        @Assert: Sync Plan is not created
        @BZ: 1087425
        """

        description = "with same name"
        # TODO: Due to bug 1087425 using common_haserror instead of name_error
        locator = common_locators["common_haserror"]
        self.configure_syncplan()
        self.syncplan.create(name)
        self.assertIsNotNone(self.products.search(name))
        self.syncplan.create(name, description)
        error = self.products.wait_until_element(locator)
        self.assertTrue(error)

    @skip_if_bug_open('bugzilla', 1131661)
    @attr('ui', 'syncplan', 'implemented')
    def test_positive_create_3(self):
        """
        @Feature: Content Sync Plan - Positive Create
        @Test: Create Sync plan with specified start time
        @Assert: Sync Plan is created with the specified time.
        @BZ: 1131661
        """

        locator = locators["sp.fetch_startdate"]
        plan_name = generate_string("alpha", 8)
        self.configure_syncplan()
        description = "sync plan create with start date"
        current_date = datetime.now()
        startdate = current_date + timedelta(minutes=10)
        starthour = startdate.strftime("%H")
        startminute = startdate.strftime("%M")
        # Formatting current_date to web-UI format "%b %d, %Y %I:%M:%S %p"
        # Removed zero padded hrs & mins as fetching via web-UI doesn't have it
        # Removed the seconds info as it would be too quick to validate via UI.
        fetch_starttime = startdate.strftime("%b %d, %Y %I:%M:%S %p").\
            lstrip("0").replace(" 0", " ").rpartition(':')[0]
        self.syncplan.create(plan_name, description, start_hour=starthour,
                             start_minute=startminute)
        self.assertIsNotNone(self.products.search(plan_name))
        self.syncplan.search(plan_name).click()
        self.syncplan.wait_for_ajax()
        # Removed the seconds info as it would be too quick to validate via UI.
        starttime_text = str(self.syncplan.wait_until_element(locator).text).\
            rpartition(':')[0]
        self.assertEqual(starttime_text, fetch_starttime)

    @skip_if_bug_open('bugzilla', 1131661)
    @attr('ui', 'syncplan', 'implemented')
    def test_positive_create_4(self):
        """
        @Feature: Content Sync Plan - Positive Create
        @Test: Create Sync plan with specified start date
        @Assert: Sync Plan is created with the specified date
        @BZ: 1131661
        """

        locator = locators["sp.fetch_startdate"]
        plan_name = generate_string("alpha", 8)
        self.configure_syncplan()
        description = "sync plan create with start date"
        current_date = datetime.now()
        startdate = current_date + timedelta(days=10)
        startdate_str = startdate.strftime("%Y-%m-%d")
        # validating only for date
        fetch_startdate = startdate.strftime("%b %-d, %Y %I:%M:%S %p").\
            rpartition(',')[0]
        self.syncplan.create(plan_name, description, startdate=startdate_str)
        self.assertIsNotNone(self.products.search(plan_name))
        self.syncplan.search(plan_name).click()
        self.syncplan.wait_for_ajax()
        startdate_text = str(self.syncplan.wait_until_element(locator).text).\
            rpartition(',')[0]
        self.assertEqual(startdate_text, fetch_startdate)

    def test_negative_create_1(self):
        """
        @Feature: Content Sync Plan - Negative Create
        @Test: Create Sync Plan with whitespace as name input parameters
        @Assert: Sync Plan is not created with whitespace input
        """

        name = "   "
        locator = common_locators["common_invalid"]
        self.configure_syncplan()
        self.syncplan.create(name)
        invalid = self.products.wait_until_element(locator)
        self.assertTrue(invalid)

    def test_negative_create_2(self):
        """
        @Feature: Content Sync Plan - Negative Create
        @Test: Create Sync Plan with blank as name input parameters
        @Assert: Sync Plan is not created with blank input
        """

        name = ""
        locator = common_locators["common_invalid"]
        self.configure_syncplan()
        self.syncplan.create(name)
        invalid = self.products.wait_until_element(locator)
        self.assertTrue(invalid)

    @skip_if_bug_open('bugzilla', 1087425)
    @attr('ui', 'syncplan', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_negative_create_3(self, name):
        """
        @Feature: Content Sync Plan - Negative Create
        @Test: Create Sync Plan with long chars for name as input parameters
        @Assert: Sync Plan is not created with more than 255 chars
        @BZ: 1087425
        """

        locator = common_locators["common_haserror"]
        description = "more than 255 chars"
        self.configure_syncplan()
        self.syncplan.create(name, description)
        error = self.products.wait_until_element(locator)
        self.assertTrue(error)

    @attr('ui', 'syncplan', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_1(self, plan_name):
        """
        @Feature: Content Sync Plan - Positive Update name
        @Test: Update Sync plan's name
        @Assert: Sync Plan's name is updated
        """

        new_plan_name = generate_string("alpha", 8)
        description = "update sync plan"
        self.configure_syncplan()
        self.syncplan.create(plan_name, description)
        self.assertIsNotNone(self.products.search(plan_name))
        self.syncplan.update(plan_name, new_name=new_plan_name)
        self.assertIsNotNone(self.products.search(new_plan_name))

    @attr('ui', 'syncplan', 'implemented')
    @data({u'name': generate_string('alpha', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': generate_string('numeric', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': generate_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': generate_string('utf8', 10),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': generate_string('html', 20),
           u'interval': SYNC_INTERVAL['hour']},
          {u'name': generate_string('alpha', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': generate_string('numeric', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': generate_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': generate_string('utf8', 10),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': generate_string('html', 20),
           u'interval': SYNC_INTERVAL['day']},
          {u'name': generate_string('alpha', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': generate_string('numeric', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': generate_string('alphanumeric', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': generate_string('utf8', 10),
           u'interval': SYNC_INTERVAL['week']},
          {u'name': generate_string('html', 20),
           u'interval': SYNC_INTERVAL['week']})
    def test_positive_update_2(self, test_data):
        """
        @Feature: Content Sync Plan - Positive Update interval
        @Test: Update Sync plan's interval
        @Assert: Sync Plan's interval is updated
        """

        description = "delete sync plan"
        locator = locators["sp.fetch_interval"]
        self.configure_syncplan()
        self.syncplan.create(test_data['name'], description)
        self.assertIsNotNone(self.products.search(test_data['name']))
        self.syncplan.update(test_data['name'],
                             new_sync_interval=test_data['interval'])
        self.navigator.go_to_sync_plans()
        self.syncplan.search(test_data['name']).click()
        self.syncplan.wait_for_ajax()
        interval_text = self.syncplan.wait_until_element(locator).text
        self.assertEqual(interval_text, test_data['interval'])

    @attr('ui', 'syncplan', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_3(self, plan_name):
        """
        @Feature: Content Sync Plan - Positive Update add products
        @Test: Update Sync plan and associate products
        @Assert: Sync Plan has the associated product
        """

        prd_name = generate_string("alpha", 8)
        description = "update sync plan, add prds"
        strategy, value = locators["sp.prd_select"]
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.navigator.go_to_sync_plans()
        self.syncplan.create(plan_name, description)
        self.assertIsNotNone(self.products.search(plan_name))
        self.syncplan.update(plan_name, add_products=[prd_name])
        self.syncplan.search(plan_name).click()
        self.syncplan.wait_for_ajax()
        self.syncplan.wait_until_element(tab_locators["sp.tab_products"]).\
            click()
        self.syncplan.wait_for_ajax()
        prd_element = self.syncplan.wait_until_element((strategy,
                                                        value % prd_name))
        self.assertTrue(prd_element)

    @attr('ui', 'syncplan', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_4(self, plan_name):
        """
        @Feature: Content Sync Plan - Positive Update remove products
        @Test: Update Sync plan and disassociate products
        @Assert: Sync Plan does not have the associated product
        """

        prd_name = generate_string("alpha", 8)
        plan_name = generate_string("alpha", 8)
        description = "update sync plan, add prds"
        strategy, value = locators["sp.prd_select"]
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.navigator.go_to_sync_plans()
        self.syncplan.create(plan_name, description)
        self.assertIsNotNone(self.products.search(plan_name))
        self.syncplan.update(plan_name, add_products=[prd_name])
        self.syncplan.search(plan_name).click()
        self.syncplan.wait_for_ajax()
        self.syncplan.wait_until_element(tab_locators["sp.tab_products"]).\
            click()
        self.syncplan.wait_for_ajax()
        prd_element = self.syncplan.wait_until_element((strategy,
                                                        value % prd_name))
        self.assertTrue(prd_element)
        self.syncplan.update(plan_name, rm_products=[prd_name])
        self.syncplan.search(plan_name).click()
        self.syncplan.wait_for_ajax()
        self.syncplan.wait_until_element(tab_locators["sp.tab_products"]).\
            click()
        self.syncplan.wait_for_ajax()
        self.syncplan.wait_until_element(tab_locators["sp.add_prd"]).\
            click()
        self.syncplan.wait_for_ajax()
        prd_element = self.syncplan.wait_until_element((strategy,
                                                        value % prd_name))
        self.assertTrue(prd_element)

    @attr('ui', 'syncplan', 'implemented')
    @data(*generate_strings_list())
    def test_positive_delete_1(self, plan_name):
        """
        @Feature: Content Sync Plan - Positive Delete
        @Test: Delete a Sync plan
        @Assert: Sync Plan is deleted
        """

        description = "delete sync plan"
        self.configure_syncplan()
        self.syncplan.create(plan_name, description)
        self.assertIsNotNone(self.products.search(plan_name))
        self.syncplan.delete(plan_name)
        self.assertIsNone(self.products.search(plan_name))
