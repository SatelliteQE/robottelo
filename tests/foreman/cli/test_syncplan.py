# -*- encoding: utf-8 -*-
"""Test class for Product CLI"""

from datetime import datetime, timedelta
from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError, make_org, make_sync_plan
from robottelo.cli.syncplan import SyncPlan
from robottelo.datafactory import valid_data_list, invalid_values_list
from robottelo.decorators import skip_if_bug_open, tier1
from robottelo.test import CLITestCase


def valid_name_interval_create_tests():
    """Returns a tuple of valid data for interval create tests."""
    return(
        {u'name': gen_string('alpha', 15), u'interval': u'hourly'},
        {u'name': gen_string('alphanumeric', 15), u'interval': u'hourly'},
        {u'name': gen_string('numeric', 15), u'interval': u'hourly'},
        {u'name': gen_string('latin1', 15), u'interval': u'hourly'},
        {u'name': gen_string('utf8', 15), u'interval': u'hourly'},
        {u'name': gen_string('html', 15), u'interval': u'hourly'},
        {u'name': gen_string('alpha', 15), u'interval': u'daily'},
        {u'name': gen_string('alphanumeric', 15), u'interval': u'daily'},
        {u'name': gen_string('numeric', 15), u'interval': u'daily'},
        {u'name': gen_string('latin1', 15), u'interval': u'daily'},
        {u'name': gen_string('utf8', 15), u'interval': u'daily'},
        {u'name': gen_string('html', 15), u'interval': u'daily'},
        {u'name': gen_string('alpha', 15), u'interval': u'weekly'},
        {u'name': gen_string('alphanumeric', 15), u'interval': u'weekly'},
        {u'name': gen_string('numeric', 15), u'interval': 'weekly'},
        {u'name': gen_string('latin1', 15), u'interval': u'weekly'},
        {u'name': gen_string('utf8', 15), u'interval': u'weekly'},
        {u'name': gen_string('html', 15), u'interval': u'weekly'},
    )


def valid_name_interval_update_tests():
    """Returns a tuple of valid data for interval update tests."""
    return(
        {u'name': gen_string('alpha', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('alphanumeric', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('numeric', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('latin1', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('utf8', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('html', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('alpha', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('alphanumeric', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('numeric', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('latin1', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('utf8', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('html', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('alpha', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
        {u'name': gen_string('alphanumeric', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
        {u'name': gen_string('numeric', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
        {u'name': gen_string('latin1', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
        {u'name': gen_string('utf8', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
        {u'name': gen_string('html', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
    )


class SyncPlanTestCase(CLITestCase):
    """Sync Plan CLI tests."""

    org = None

    # pylint: disable=unexpected-keyword-arg
    def setUp(self):
        """Tests for Sync Plans via Hammer CLI"""

        super(SyncPlanTestCase, self).setUp()

        if SyncPlanTestCase.org is None:
            SyncPlanTestCase.org = make_org(cached=True)

    def _make_sync_plan(self, options=None):
        """Make a sync plan and asserts its success"""

        if options is None:
            options = {}

        if not options.get('organization-id', None):
            options[u'organization-id'] = self.org['id']

        return make_sync_plan(options)

    @tier1
    def test_positive_create_with_name(self):
        """@Test: Check if syncplan can be created with random names

        @Feature: Sync Plan

        @Assert: Sync plan is created and has random name
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_sync_plan = self._make_sync_plan({u'name': name})
                self.assertEqual(new_sync_plan['name'], name)

    @tier1
    def test_positive_create_with_description(self):
        """@Test: Check if syncplan can be created with random description

        @Feature: Sync Plan

        @Assert: Sync plan is created and has random description
        """
        for desc in valid_data_list():
            with self.subTest(desc):
                new_sync_plan = self._make_sync_plan({u'description': desc})
                self.assertEqual(new_sync_plan['description'], desc)

    @tier1
    def test_positive_create_with_interval(self):
        """@Test: Check if syncplan can be created with varied intervals

        @Feature: Sync Plan

        @Assert: Sync plan is created and has selected interval
        """
        for test_data in valid_name_interval_create_tests():
            with self.subTest(test_data):
                new_sync_plan = self._make_sync_plan({
                    u'interval': test_data['interval'],
                    u'name': test_data['name'],
                })
                self.assertEqual(new_sync_plan['name'], test_data['name'])
                self.assertEqual(
                    new_sync_plan['interval'],
                    test_data['interval']
                )

    @tier1
    def test_negative_create_with_name(self):
        """@Test: Check if syncplan can be created with random names

        @Feature: Sync Plan

        @Assert: Sync plan is created and has random name
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._make_sync_plan({u'name': name})

    @tier1
    def test_positive_update_description(self):
        """@Test: Check if syncplan description can be updated

        @Feature: Sync Plan

        @Assert: Sync plan is created and description is updated
        """
        new_sync_plan = self._make_sync_plan()
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                SyncPlan.update({
                    u'description': new_desc,
                    u'id': new_sync_plan['id'],
                })
                result = SyncPlan.info({u'id': new_sync_plan['id']})
                self.assertEqual(result['description'], new_desc)

    @tier1
    def test_positive_update_interval(self):
        """@Test: Check if syncplan interval be updated

        @Feature: Sync Plan

        @Assert: Sync plan interval is updated
        """
        for test_data in valid_name_interval_update_tests():
            with self.subTest(test_data):
                new_sync_plan = self._make_sync_plan({
                    u'interval': test_data['interval'],
                    u'name': test_data['name'],
                })
                SyncPlan.update({
                    u'id': new_sync_plan['id'],
                    u'interval': test_data['new-interval'],
                })
                result = SyncPlan.info({u'id': new_sync_plan['id']})
                self.assertEqual(result['interval'], test_data['new-interval'])

    @tier1
    def test_positive_update_sync_date(self):
        """@Test: Check if syncplan sync date can be updated

        @Feature: Sync Plan

        @Assert: Sync plan is created and sync plan is updated
        """
        # Set the sync date to today/right now
        today = datetime.now()
        sync_plan_name = gen_string('alphanumeric')
        new_sync_plan = self._make_sync_plan({
            u'name': sync_plan_name,
            u'sync-date': today.strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Assert that sync date matches data passed
        self.assertEqual(
            new_sync_plan['start-date'],
            today.strftime("%Y/%m/%d %H:%M:%S"),
        )
        # Set sync date 5 days in the future
        future_date = today + timedelta(days=5)
        # Update sync interval
        SyncPlan.update({
            u'id': new_sync_plan['id'],
            u'sync-date': future_date.strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Fetch it
        result = SyncPlan.info({
            u'id': new_sync_plan['id'],
        })
        self.assertNotEqual(result['start-date'], new_sync_plan['start-date'])
        self.assertGreater(
            datetime.strptime(
                result['start-date'],
                '%Y/%m/%d %H:%M:%S',
            ),
            datetime.strptime(
                new_sync_plan['start-date'],
                '%Y/%m/%d %H:%M:%S',
            ),
            'Sync date was not updated',
        )

    @tier1
    def test_positive_delete_by_id(self):
        """@Test: Check if syncplan can be created and deleted

        @Feature: Sync Plan

        @Assert: Sync plan is created and then deleted
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_sync_plan = self._make_sync_plan({u'name': name})
                SyncPlan.delete({u'id': new_sync_plan['id']})
                with self.assertRaises(CLIReturnCodeError):
                    SyncPlan.info({'id': new_sync_plan['id']})

    @skip_if_bug_open('bugzilla', 1261122)
    @tier1
    def test_verify_bugzilla_1261122(self):
        """@Test: Check if Enabled field is displayed in sync-plan info output

        @Feature: Sync Plan Info

        @Assert: Sync plan Enabled state is displayed

        @BZ: 1261122
        """
        new_sync_plan = self._make_sync_plan()
        result = SyncPlan.info({'id': new_sync_plan['id']})
        self.assertIsNotNone(result.get('enabled'))
