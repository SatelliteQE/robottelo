# -*- encoding: utf-8 -*-
"""Test class for Product CLI"""

from datetime import datetime, timedelta
from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.factory import CLIFactoryError, make_org, make_sync_plan
from robottelo.cli.syncplan import SyncPlan
from robottelo.decorators import data, skip_if_bug_open
from robottelo.test import CLITestCase


@ddt
class TestSyncPlan(CLITestCase):
    """Sync Plan CLI tests."""

    org = None

    def setUp(self):  # noqa
        """Tests for Sync Plans via Hammer CLI"""

        super(TestSyncPlan, self).setUp()

        if TestSyncPlan.org is None:
            TestSyncPlan.org = make_org(cached=True)

    def _make_sync_plan(self, options=None):
        """Make a sync plan and asserts its success"""

        if options is None:
            options = {}

        if not options.get('organization-id', None):
            options[u'organization-id'] = self.org['id']

        return make_sync_plan(options)

    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_create_1(self, test_data):
        """@Test: Check if syncplan can be created with random names

        @Feature: Sync Plan

        @Assert: Sync plan is created and has random name

        """

        new_sync_plan = self._make_sync_plan({u'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_sync_plan['name'],
            test_data['name'],
            "Names don't match"
        )

    @data(
        {u'description': gen_string('alpha', 15)},
        {u'description': gen_string('alphanumeric', 15)},
        {u'description': gen_string('numeric', 15)},
        {u'description': gen_string('latin1', 15)},
        {u'description': gen_string('utf8', 15)},
        {u'description': gen_string('html', 15)},
    )
    def test_positive_create_2(self, test_data):
        """@Test: Check if syncplan can be created with random description

        @Feature: Sync Plan

        @Assert: Sync plan is created and has random description

        """

        new_sync_plan = self._make_sync_plan(
            {u'description': test_data['description']})
        # Assert that description matches data passed
        self.assertEqual(
            new_sync_plan['description'],
            test_data['description'],
            "Descriptions don't match"
        )

    @data(
        {
            u'name': gen_string('alpha', 15),
            u'interval': u'hourly',
        },
        {
            u'name': gen_string('alphanumeric', 15),
            u'interval': u'hourly',
        },
        {
            u'name': gen_string('numeric', 15),
            u'interval': u'hourly'
        },
        {
            u'name': gen_string('latin1', 15),
            u'interval': u'hourly'
        },
        {
            u'name': gen_string('utf8', 15),
            u'interval': u'hourly'
        },
        {
            u'name': gen_string('html', 15),
            u'interval': u'hourly'
        },
        {
            u'name': gen_string('alpha', 15),
            u'interval': u'daily'
        },
        {
            u'name': gen_string('alphanumeric', 15),
            u'interval': u'daily'
        },
        {
            u'name': gen_string('numeric', 15),
            u'interval': u'daily'
        },
        {
            u'name': gen_string('latin1', 15),
            u'interval': u'daily'
        },
        {
            u'name': gen_string('utf8', 15),
            u'interval': u'daily'
        },
        {
            u'name': gen_string('html', 15),
            u'interval': u'daily'
        },
        {
            u'name': gen_string('alpha', 15),
            u'interval': u'weekly'
        },
        {
            u'name': gen_string('alphanumeric', 15),
            u'interval': u'weekly'
        },
        {
            u'name': gen_string('numeric', 15),
            u'interval': 'weekly'
        },
        {
            u'name': gen_string('latin1', 15),
            u'interval': u'weekly'
        },
        {
            u'name': gen_string('utf8', 15),
            u'interval': u'weekly'
        },
        {
            u'name': gen_string('html', 15),
            u'interval': u'weekly'
        },
    )
    def test_positive_create_3(self, test_data):
        """@Test: Check if syncplan can be created with varied intervals

        @Feature: Sync Plan

        @Assert: Sync plan is created and has selected interval

        """

        new_sync_plan = self._make_sync_plan(
            {u'name': test_data['name'],
             u'interval': test_data['interval']})
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
        {u'name': gen_string('alpha', 300)},
        {u'name': gen_string('alphanumeric', 300)},
        {u'name': gen_string('numeric', 300)},
        {u'name': gen_string('latin1', 300)},
        {u'name': gen_string('utf8', 300)},
        {u'name': gen_string('html', 300)},
    )
    def test_negative_create_1(self, test_data):
        """@Test: Check if syncplan can be created with random names

        @Feature: Sync Plan

        @Assert: Sync plan is created and has random name

        """
        with self.assertRaises(CLIFactoryError):
            self._make_sync_plan({u'name': test_data['name']})

    @data(
        {u'description': gen_string('alpha', 15)},
        {u'description': gen_string('alphanumeric', 15)},
        {u'description': gen_string('numeric', 15)},
        {u'description': gen_string('latin1', 15)},
        {u'description': gen_string('utf8', 15)},
        {u'description': gen_string('html', 15)},
    )
    def test_positive_update_1(self, test_data):
        """@Test: Check if syncplan description can be updated

        @Feature: Sync Plan

        @Assert: Sync plan is created and description is updated

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
                u'id': new_sync_plan['id'],
                u'description': test_data['description']
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
            {
                u'id': new_sync_plan['id'],
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
    def test_positive_update_2(self, test_data):
        """@Test: Check if syncplan interval be updated

        @Feature: Sync Plan

        @Assert: Sync plan interval is updated

        """

        new_sync_plan = self._make_sync_plan(
            {
                u'name': test_data['name'],
                u'interval': test_data['interval']
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
                u'id': new_sync_plan['id'],
                u'interval': test_data['new-interval']
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
            {
                u'id': new_sync_plan['id'],
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
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_update_3(self, test_data):
        """@Test: Check if syncplan sync date can be updated

        @Feature: Sync Plan

        @Assert: Sync plan is created and sync plan is updated

        """

        # Set the sync date to today/right now
        today = datetime.now()
        new_sync_plan = self._make_sync_plan({
            u'name': test_data['name'],
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
        result = SyncPlan.update({
            u'id': new_sync_plan['id'],
            u'sync-date': future_date.strftime("%Y-%m-%d %H:%M:%S"),
        })
        self.assertEqual(
            result.return_code,
            0,
            "Sync plan was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = SyncPlan.info({
            u'id': new_sync_plan['id'],
        })
        self.assertEqual(
            result.return_code,
            0,
            "Sync plan was not updated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertNotEqual(
            result.stdout['start-date'],
            new_sync_plan['start-date'],
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

    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_delete_1(self, test_data):
        """@Test: Check if syncplan can be created and deleted

        @Feature: Sync Plan

        @Assert: Sync plan is created and then deleted

        """

        new_sync_plan = self._make_sync_plan({u'name': test_data['name']})
        # Assert that name matches data passed
        self.assertEqual(
            new_sync_plan['name'],
            test_data['name'],
            "Names don't match"
        )

        # Delete it
        result = SyncPlan.delete({u'id': new_sync_plan['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Sync plan was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = SyncPlan.info(
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

    @skip_if_bug_open('bugzilla', 1261122)
    def test_bz1261122_enabled_state_visible(self):
        """@Test: Check if Enabled field is displayed in sync-plan info output

        @Feature: Sync Plan Info

        @Assert: Sync plan Enabled state is displayed

        """
        new_sync_plan = self._make_sync_plan()
        result = SyncPlan.info({'id': new_sync_plan['id']})
        self.assertIsNotNone(result.stdout.get('enabled'))
