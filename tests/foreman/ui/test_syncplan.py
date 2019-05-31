"""Test class for Sync Plan UI

:Requirement: Syncplan

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from datetime import datetime, timedelta
from fauxfactory import gen_string
from nailgun import entities
from random import choice
from robottelo.constants import SYNC_INTERVAL
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_values_list
)
from robottelo.decorators import (
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    upgrade,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_syncplan
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


@filtered_datapoint
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

        :id: ceb125a4-449a-4a86-a94f-2a28884e3a41

        :expectedresults: Sync Plan is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description=gen_string('utf8'),
                        sync_interval=choice(valid_sync_intervals()),
                    )
                    self.assertIsNotNone(self.syncplan.search(name))

    @tier1
    def test_positive_create_with_description(self):
        """Create Sync Plan with valid desc values

        :id: 6ccd2229-dcc3-4090-9ec9-84fea837c50c

        :expectedresults: Sync Plan is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for desc in generate_strings_list():
                with self.subTest(desc):
                    name = gen_string('utf8')
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description=desc,
                        sync_interval=choice(valid_sync_intervals()),
                    )
                    self.assertIsNotNone(self.syncplan.search(name))

    @tier1
    def test_positive_create_with_sync_interval(self):
        """Create Sync Plan with valid sync intervals

        :id: 8916285a-c8d2-415a-b694-c32727e93ac0

        :expectedresults: Sync Plan is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Sync Plan with invalid names

        :id: 64724669-0289-4e8a-a44d-eb47e094ef18

        :expectedresults: Sync Plan is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :id: 6d042f9b-82f2-4795-aa48-4603c1698aaa

        :expectedresults: Sync Plan cannot be created with existing name

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        with Session(self) as session:
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

    @skip_if_bug_open('bugzilla', 1460146)
    @tier1
    def test_positive_update_name(self):
        """Update Sync plan's name

        :id: 6b22468f-6abc-4a63-b283-28c7816a5e86

        :expectedresults: Sync Plan's name is updated

        :BZ: 1460146

        :CaseImportance: Critical
        """
        plan_name = gen_string('alpha')
        entities.SyncPlan(
            name=plan_name,
            interval=SYNC_INTERVAL['day'],
            organization=self.organization,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            for new_plan_name in generate_strings_list():
                with self.subTest(new_plan_name):
                    self.syncplan.update(plan_name, new_name=new_plan_name)
                    self.assertIsNotNone(self.syncplan.search(new_plan_name))
                    plan_name = new_plan_name  # for next iteration

    @skip_if_bug_open('bugzilla', 1460146)
    @tier1
    @upgrade
    def test_positive_update_interval(self):
        """Update Sync plan's interval

        :id: 35820efd-099e-45dd-8298-77d5f35c26db

        :expectedresults: Sync Plan's interval is updated and no error raised

        :BZ: 1460146, 1387543

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        start_date = datetime.utcnow() + timedelta(days=1)
        entities.SyncPlan(
            name=name,
            interval=SYNC_INTERVAL['day'],
            organization=self.organization,
            enabled=True,
            sync_date=start_date,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            for new_interval in valid_sync_intervals():
                with self.subTest(new_interval):
                    self.syncplan.update(name, new_sync_interval=new_interval)
                    self.assertIsNone(self.user.wait_until_element(
                        common_locators['haserror'], timeout=3))
                    self.syncplan.click(self.syncplan.search(name))
                    # Assert updated sync interval
                    interval_text = self.syncplan.wait_until_element(
                        locators['sp.fetch_interval']).text
                    self.assertEqual(interval_text, new_interval)
                    # Assert that start date was not changed after interval
                    # changed
                    startdate_text = self.syncplan.wait_until_element(
                        locators['sp.fetch_startdate']).text
                    self.assertNotEqual(startdate_text, 'Invalid Date')
                    self.assertIn(
                        start_date.strftime("%Y/%m/%d"), startdate_text)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete an existing Sync plan

        :id: 81beec05-e38c-48bc-8f01-10cb1e10a3f6

        :expectedresults: Sync Plan is deleted successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for plan_name in generate_strings_list():
                with self.subTest(plan_name):
                    entities.SyncPlan(
                        name=plan_name,
                        interval=SYNC_INTERVAL['day'],
                        organization=self.organization,
                    ).create()
                    session.nav.go_to_select_org(self.organization.name)
                    self.syncplan.delete(plan_name)

    @stubbed()
    @tier2
    def test_positive_create_ostree_sync_plan(self):
        """Create a sync plan for ostree contents.

        :id: bf01f23f-ba55-4c88-baad-85603fce57a4

        :expectedresults: sync plan should be created successfully

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """
