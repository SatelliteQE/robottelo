"""
Test class for Sync Plan UI
"""

from ddt import data, ddt
from nose.plugins.attrib import attr
from robottelo.common.constants import SYNC_INTERVAL
from robottelo.common.helpers import generate_string, generate_strings_list
from robottelo.ui.factory import make_org
from robottelo.ui.session import Session
from tests.foreman.ui.baseui import BaseUI


@ddt
class Syncplan(BaseUI):
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

    @attr('ui', 'syncplan', 'implemented')
    @data({'name': generate_string('alpha', 10),
           'desc': generate_string('alpha', 10),
           'interval': SYNC_INTERVAL['day']},
          {'name': generate_string('numeric', 10),
           'desc': generate_string('numeric', 10),
           'interval': SYNC_INTERVAL['day']},
          {'name': generate_string('alphanumeric', 10),
           'desc': generate_string('alphanumeric', 10),
           'interval': SYNC_INTERVAL['day']},
          {'name': generate_string('utf8', 10),
           'desc': generate_string('utf8', 10),
           'interval': SYNC_INTERVAL['day']},
          {'name': generate_string('html', 20),
           'desc': generate_string('html', 10),
           'interval': SYNC_INTERVAL['day']},
          {'name': generate_string('alpha', 10),
           'desc': generate_string('alpha', 10),
           'interval': SYNC_INTERVAL['week']},
          {'name': generate_string('numeric', 10),
           'desc': generate_string('numeric', 10),
           'interval': SYNC_INTERVAL['week']},
          {'name': generate_string('alphanumeric', 10),
           'desc': generate_string('alphanumeric', 10),
           'interval': SYNC_INTERVAL['week']},
          {'name': generate_string('utf8', 10),
           'desc': generate_string('utf8', 10),
           'interval': SYNC_INTERVAL['week']},
          {'name': generate_string('html', 20),
           'desc': generate_string('html', 10),
           'interval': SYNC_INTERVAL['week']})
    def test_positive_create_1(self, test_data):
        """
        @Feature: Content Sync Plan - Positive Create
        @Test: Create Sync Plan with minimal input parameters
        @Assert: Sync Plan is created
        """

        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_sync_plans()
        self.syncplan.create(test_data['name'], description=test_data['desc'],
                             sync_interval=test_data['interval'])
        self.assertIsNotNone(self.products.search(test_data['name']))

    @attr('ui', 'syncplan', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_1(self, plan_name):
        """
        @Feature: Content Sync Plan - Positive Update
        @Test: Update Sync plan's name
        @Assert: Sync Plan's name is updated
        """

        new_plan_name = generate_string("alpha", 8)
        description = "update sync plan"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_sync_plans()
        self.syncplan.create(plan_name, description)
        self.assertIsNotNone(self.products.search(plan_name))
        self.syncplan.update(plan_name, new_name=new_plan_name)
        self.assertIsNotNone(self.products.search(new_plan_name))

    @attr('ui', 'syncplan', 'implemented')
    @data(*generate_strings_list())
    def test_positive_delete_1(self, plan_name):
        """
        @Feature: Content Sync Plan - Positive Delete
        @Test: Delete a Sync plan
        @Assert: Sync Plan is deleted
        """

        description = "delete sync plan"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_sync_plans()
        self.syncplan.create(plan_name, description)
        self.assertIsNotNone(self.products.search(plan_name))
        self.syncplan.delete(plan_name)
