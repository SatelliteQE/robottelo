# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Product CLI
"""

from datetime import datetime, timedelta
from ddt import data
from ddt import ddt
from robottelo.cli.factory import make_org, make_sync_plan
from robottelo.cli.syncplan import SyncPlan
from robottelo.common.decorators import bzbug
from robottelo.common.helpers import generate_string
from nose.plugins.attrib import attr
from tests.cli.basecli import BaseCLI


@ddt
class TestSyncPlan(BaseCLI):
    """
    Sync Plan CLI tests.
    """

    org = None

    def setUp(self):
        """
        Tests for Sync Plans via Hammer CLI
        """

        super(TestSyncPlan, self).setUp()

        if TestSyncPlan.org is None:
            TestSyncPlan.org = make_org()

    def _make_sync_plan(self, options=None):
        """
        Make a sync plan and asserts its success
        """

        if options is None:
            options = {}

        if not options.get('organization-id', None):
            options['organization-id'] = self.org['label']

        new_sync_plan = make_sync_plan(options)

        # Fetch it
        result = SyncPlan.info(
            self.org['label'],
            {
                'id': new_sync_plan['id']
            }
        )

        self.assertEqual(
            result.return_code,
            0,
            "Sync plan was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Return the sync plan dictionary
        return new_sync_plan

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'syncplan')
    def test_positive_create_1(self, test_data):
        """
        @Test: Check if syncplan can be created with random names
        @Feature: Sync Plan
        @Assert: Sync plan is created and has random name
        """

        new_sync_plan = self._make_sync_plan({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_sync_plan['name'],
            test_data['name'],
            "Names don't match"
        )

    @data(
        {'description': generate_string('alpha', 15)},
        {'description': generate_string('alphanumeric', 15)},
        {'description': generate_string('numeric', 15)},
        {'description': generate_string('latin1', 15)},
        {'description': generate_string('utf8', 15)},
        {'description': generate_string('html', 15)},
    )
    @attr('cli', 'syncplan')
    def test_positive_create_2(self, test_data):
        """
        @Test: Check if syncplan can be created with random description
        @Feature: Sync Plan
        @Assert: Sync plan is created and has random description
        """

        new_sync_plan = self._make_sync_plan(
            {'description': test_data['description']})
        # Assert that description matches data passed
        self.assertEqual(
            new_sync_plan['description'],
            test_data['description'],
            "Descriptions don't match"
        )

    @data(
        {'name': generate_string('alpha', 15), 'interval': 'hourly'},
        {'name': generate_string('alphanumeric', 15), 'interval': 'hourly'},
        {'name': generate_string('numeric', 15), 'interval': 'hourly'},
        {'name': generate_string('latin1', 15), 'interval': 'hourly'},
        {'name': generate_string('utf8', 15), 'interval': 'hourly'},
        {'name': generate_string('html', 15), 'interval': 'hourly'},
        {'name': generate_string('alpha', 15), 'interval': 'daily'},
        {'name': generate_string('alphanumeric', 15), 'interval': 'daily'},
        {'name': generate_string('numeric', 15), 'interval': 'daily'},
        {'name': generate_string('latin1', 15), 'interval': 'daily'},
        {'name': generate_string('utf8', 15), 'interval': 'daily'},
        {'name': generate_string('html', 15), 'interval': 'daily'},
        {'name': generate_string('alpha', 15), 'interval': 'weekly'},
        {'name': generate_string('alphanumeric', 15), 'interval': 'weekly'},
        {'name': generate_string('numeric', 15), 'interval': 'weekly'},
        {'name': generate_string('latin1', 15), 'interval': 'weekly'},
        {'name': generate_string('utf8', 15), 'interval': 'weekly'},
        {'name': generate_string('html', 15), 'interval': 'weekly'},
    )
    @attr('cli', 'syncplan')
    def test_positive_create_3(self, test_data):
        """
        @Test: Check if syncplan can be created with varied intervals
        @Feature: Sync Plan
        @Assert: Sync plan is created and has selected interval
        """

        new_sync_plan = self._make_sync_plan(
            {'name': test_data['name'],
             'interval': test_data['interval']})
        # Assert that name and interval matches data passed
        self.assertEqual(
            new_sync_plan['name'],
            test_data['name'],
            "Names don't match"
        )
        self.assertEqual(
            new_sync_plan['interval'],
            test_data['interval'],
            "Intervals don't match"
        )

    @data(
        {'name': generate_string('alpha', 300)},
        {'name': generate_string('alphanumeric', 300)},
        {'name': generate_string('numeric', 300)},
        {'name': generate_string('latin1', 300)},
        {'name': generate_string('utf8', 300)},
        {'name': generate_string('html', 300)},
    )
    @attr('cli', 'syncplan')
    def test_negative_create_1(self, test_data):
        """
        @Test: Check if syncplan can be created with random names
        @Feature: Sync Plan
        @Assert: Sync plan is created and has random name
        """

        with self.assertRaises(Exception):
            self._make_sync_plan({'name': test_data['name']})

    @bzbug('1082157')
    @data(
        {'description': generate_string('alpha', 15)},
        {'description': generate_string('alphanumeric', 15)},
        {'description': generate_string('numeric', 15)},
        {'description': generate_string('latin1', 15)},
        {'description': generate_string('utf8', 15)},
        {'description': generate_string('html', 15)},
    )
    @attr('cli', 'syncplan')
    def test_positive_update_1(self, test_data):
        """
        @Test: Check if syncplan description can be updated
        @Feature: Sync Plan
        @Assert: Sync plan is created and description is updated
        @BZ: 1082157
        """

        new_sync_plan = self._make_sync_plan()
        # Assert that description matches data passed
        self.assertNotEqual(
            new_sync_plan['description'],
            test_data['description'],
            "Descriptions don't match"
        )

        # Update sync plan
        result = SyncPlan.update(
            {
                'id': new_sync_plan['id'],
                'organization-id': self.org['label'],
                'description': test_data['description']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Sync plan was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = SyncPlan.info(
            self.org['label'],
            {
                'id': new_sync_plan['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Sync plan was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # Assert that description matches new value
        self.assertIsNotNone(
            result.stdout.get('description', None),
            "The description field was not returned"
        )
        self.assertEqual(
            result.stdout['description'],
            test_data['description'],
            "Descriptions should match"
        )
        # Assert that description does not matches original value
        self.assertNotEqual(
            new_sync_plan['description'],
            result.stdout['description'],
            "Descriptions should not match"
        )

    @data(
        {'name': generate_string('alpha', 15),
         'interval': 'daily', 'new-interval': 'hourly'},
        {'name': generate_string('alphanumeric', 15),
         'interval': 'daily', 'new-interval': 'hourly'},
        {'name': generate_string('numeric', 15),
         'interval': 'daily', 'new-interval': 'hourly'},
        {'name': generate_string('latin1', 15),
         'interval': 'daily', 'new-interval': 'hourly'},
        {'name': generate_string('utf8', 15),
         'interval': 'daily', 'new-interval': 'hourly'},
        {'name': generate_string('html', 15),
         'interval': 'daily', 'new-interval': 'hourly'},
        {'name': generate_string('alpha', 15),
         'interval': 'weekly', 'new-interval': 'daily'},
        {'name': generate_string('alphanumeric', 15),
         'interval': 'weekly', 'new-interval': 'daily'},
        {'name': generate_string('numeric', 15),
         'interval': 'weekly', 'new-interval': 'daily'},
        {'name': generate_string('latin1', 15),
         'interval': 'weekly', 'new-interval': 'daily'},
        {'name': generate_string('utf8', 15),
         'interval': 'weekly', 'new-interval': 'daily'},
        {'name': generate_string('html', 15),
         'interval': 'weekly', 'new-interval': 'daily'},
        {'name': generate_string('alpha', 15),
         'interval': 'hourly', 'new-interval': 'weekly'},
        {'name': generate_string('alphanumeric', 15),
         'interval': 'hourly', 'new-interval': 'weekly'},
        {'name': generate_string('numeric', 15),
         'interval': 'hourly', 'new-interval': 'weekly'},
        {'name': generate_string('latin1', 15),
         'interval': 'hourly', 'new-interval': 'weekly'},
        {'name': generate_string('utf8', 15),
         'interval': 'hourly', 'new-interval': 'weekly'},
        {'name': generate_string('html', 15),
         'interval': 'hourly', 'new-interval': 'weekly'},
    )
    @attr('cli', 'syncplan')
    def test_positive_update_2(self, test_data):
        """
        @Test: Check if syncplan interval be updated
        @Feature: Sync Plan
        @Assert: Sync plan interval is updated
        """

        new_sync_plan = self._make_sync_plan(
            {
                'name': test_data['name'],
                'interval': test_data['interval']
            })
        # Assert that name and interval matches data passed
        self.assertEqual(
            new_sync_plan['name'],
            test_data['name'],
            "Descriptions don't match"
        )
        self.assertEqual(
            new_sync_plan['interval'],
            test_data['interval'],
            "Intervals don't match"
        )

        # Update sync interval
        result = SyncPlan.update(
            {
                'id': new_sync_plan['id'],
                'organization-id': self.org['label'],
                'interval': test_data['new-interval']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Sync plan was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = SyncPlan.info(
            self.org['label'],
            {
                'id': new_sync_plan['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Sync plan was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # Assert that interval was updated
        self.assertEqual(
            result.stdout['interval'],
            test_data['new-interval'],
            "Intervals don't match"
        )
        self.assertNotEqual(
            new_sync_plan['interval'],
            result.stdout['interval'],
            "Intervals don't match"
        )

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'syncplan')
    def test_positive_update_3(self, test_data):
        """
        @Test: Check if syncplan sync date can be updated
        @Feature: Sync Plan
        @Assert: Sync plan is created and sync plan is updated
        """

        # Set the sync date to today/right now
        today = datetime.now()
        new_sync_plan = self._make_sync_plan(
            {
                'name': test_data['name'],
                'sync-date': today.strftime("%Y-%m-%d %H:%M:%S")
            })
        # Assert that sync date matches data passed
        self.assertEqual(
            new_sync_plan['sync-date'],
            today.strftime("%Y-%m-%d %H:%M:%S"),
            "Sync dates don't match"
        )

        # Set sync date 5 days in the future
        future_date = today + timedelta(days=5)
        # Update sync interval
        result = SyncPlan.update(
            {
                'id': new_sync_plan['id'],
                'organization-id': self.org['label'],
                'sync-date': future_date.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Sync plan was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = SyncPlan.info(
            self.org['label'],
            {
                'id': new_sync_plan['id'],
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Sync plan was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertNotEqual(
            result.stdout['start-date'],
            new_sync_plan['sync-date'],
            "Sync date was not updated"
        )
        self.assertGreater(
            datetime.strptime(
                result.stdout['start-date'],
                "%Y/%m/%d %H:%M:%S"),
            datetime.strptime(
                new_sync_plan['start-date'],
                "%Y/%m/%d %H:%M:%S"),
            "Sync date was not updated"
        )

    @bzbug('1082169')
    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'syncplan')
    def test_positive_delete_1(self, test_data):
        """
        @Test: Check if syncplan can be created and deleted
        @Feature: Sync Plan
        @Assert: Sync plan is created and then deleted
        @BZ: 1082169
        """

        new_sync_plan = self._make_sync_plan({'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_sync_plan['name'],
            test_data['name'],
            "Names don't match"
        )

        # Delete it
        result = SyncPlan.delete(
            {'id': new_sync_plan['id'],
             'organization-id': self.org['label']})
        self.assertEqual(
            result.return_code,
            0,
            "Sync plan was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = SyncPlan.info(
            self.org['label'],
            {
                'id': new_sync_plan['id'],
            }
        )
        self.assertNotEqual(
            result.return_code,
            0,
            "Sync plan should not be found"
        )
        self.assertGreater(
            len(result.stderr),
            0,
            "Expected an error here"
        )
