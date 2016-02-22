# -*- encoding: utf-8 -*-
"""Test class for Sync Plan CLI"""

from datetime import datetime, timedelta
from fauxfactory import gen_string
from random import randint
from robottelo import manifests
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_org,
    make_product,
    make_repository,
    make_sync_plan,
)
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.cli.syncplan import SyncPlan
from robottelo.constants import PRDS, REPOS, REPOSET
from robottelo.datafactory import valid_data_list, invalid_values_list
from robottelo.decorators import skip_if_bug_open, stubbed, tier1, tier2, tier4
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase
from time import sleep


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

    def validate_repo_content(
            self, repo, content_types, after_sync=True, max_attempts=10):
        """Check whether corresponding content is present in repository before
        or after synchronization is performed

        :param repo: Repository instance to be validated
        :param content_types: List of repository content entities that should
            be validated (e.g. package, erratum, puppet_module)
        :param bool after_sync: Specify whether you perform validation before
            synchronization procedure is happened or after
        :param int max_attempts: Specify how many times to check for content
            presence. Delay between each attempt is 10 seconds. Default is 10
            attempts.

        """
        for _ in range(max_attempts):
            try:
                repo = Repository.info({'id': repo['id']})
                for content in content_types:
                    if after_sync:
                        self.assertGreater(
                            int(repo['content-counts'][content]), 0)
                    else:
                        self.assertFalse(int(repo['content-counts'][content]))
                break
            except AssertionError:
                sleep(30)
        else:
            raise AssertionError(
                'Repository contains invalid number of content entities')

    @tier1
    def test_positive_create_with_name(self):
        """Check if syncplan can be created with random names

        @Feature: Sync Plan

        @Assert: Sync plan is created and has random name
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_sync_plan = self._make_sync_plan({u'name': name})
                self.assertEqual(new_sync_plan['name'], name)

    @tier1
    def test_positive_create_with_description(self):
        """Check if syncplan can be created with random description

        @Feature: Sync Plan

        @Assert: Sync plan is created and has random description
        """
        for desc in valid_data_list():
            with self.subTest(desc):
                new_sync_plan = self._make_sync_plan({u'description': desc})
                self.assertEqual(new_sync_plan['description'], desc)

    @tier1
    def test_positive_create_with_interval(self):
        """Check if syncplan can be created with varied intervals

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
        """Check if syncplan can be created with random names

        @Feature: Sync Plan

        @Assert: Sync plan is created and has random name
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._make_sync_plan({u'name': name})

    @tier1
    def test_positive_update_description(self):
        """Check if syncplan description can be updated

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
        """Check if syncplan interval be updated

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
        """Check if syncplan sync date can be updated

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
        """Check if syncplan can be created and deleted

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
        """Check if Enabled field is displayed in sync-plan info output

        @Feature: Sync Plan Info

        @Assert: Sync plan Enabled state is displayed

        @BZ: 1261122
        """
        new_sync_plan = self._make_sync_plan()
        result = SyncPlan.info({'id': new_sync_plan['id']})
        self.assertIsNotNone(result.get('enabled'))

    # This Bugzilla bug is private. It is impossible to fetch info about it.
    @stubbed('Unstub when BZ1279539 is fixed')
    @tier1
    def test_negative_synchronize_custom_product_current_sync_date(self):
        """Verify product won't get synced immediately after adding association
        with a sync plan which has already been started

        @Feature: Sync Plan

        @Assert: Repository was not synchronized

        @BZ: 1279539
        """
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'organization-id': self.org['id'],
            'sync-date': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        })
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        with self.assertRaises(AssertionError):
            self.validate_repo_content(
                repo,
                ['errata', 'package-groups', 'packages'],
                max_attempts=5,
            )

    # This Bugzilla bug is private. It is impossible to fetch info about it.
    @stubbed('Unstub when BZ1279539 is fixed')
    @tier4
    def test_positive_synchronize_custom_product_current_sync_date(self):
        """Create a sync plan with current datetime as a sync date, add a
        custom product and verify the product gets synchronized on the next
        sync occurrence

        @Assert: Product is synchronized successfully.

        @Feature: SyncPlan

        @BZ: 1279539
        """
        interval = 60 * 60  # 'hourly' sync interval in seconds
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'interval': 'hourly',
            'organization-id': self.org['id'],
            'sync-date': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        })
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        # Associate sync plan with product
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        # Wait half of expected time
        sleep(interval / 2)
        # Verify product has not been synced yet
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Wait the rest of expected time
        sleep(interval / 2)
        # Verify product was synced successfully
        self.validate_repo_content(
            repo, ['errata', 'package-groups', 'packages'])

    @tier4
    def test_positive_synchronize_custom_product_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync one custom
        product with it automatically.

        @Assert: Product is synchronized successfully.

        @Feature: SyncPlan
        """
        delay = 10 * 60  # delay for sync date in seconds
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'organization-id': self.org['id'],
            'sync-date': (datetime.utcnow() + timedelta(seconds=delay))
                        .strftime("%Y-%m-%d %H:%M:%S"),
        })
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        # Verify product is not synced and doesn't have any content
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Associate sync plan with product
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        # Wait half of expected time
        sleep(delay/2)
        # Verify product has not been synced yet
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Wait the rest of expected time
        sleep(delay/2)
        # Verify product was synced successfully
        self.validate_repo_content(
            repo, ['errata', 'package-groups', 'packages'])

    @tier2
    def test_positive_synchronize_custom_products_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync multiple
        custom products with multiple repos automatically.

        @Assert: Products are synchronized successfully.

        @Feature: SyncPlan
        """
        delay = 10 * 60  # delay for sync date in seconds
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'organization-id': self.org['id'],
            'sync-date': (datetime.utcnow() + timedelta(seconds=delay))
                        .strftime("%Y-%m-%d %H:%M:%S"),
        })
        products = [
            make_product({'organization-id': self.org['id']})
            for _ in range(randint(3, 5))
        ]
        repos = [
            make_repository({'product-id': product['id']})
            for product in products
            for _ in range(randint(2, 3))
        ]
        # Verify products have not been synced yet
        for repo in repos:
            self.validate_repo_content(
                repo, ['errata', 'packages'], after_sync=False)
        # Associate sync plan with products
        for product in products:
            Product.set_sync_plan({
                'id': product['id'],
                'sync-plan-id': sync_plan['id'],
            })
        # Wait half of expected time
        sleep(delay/2)
        # Verify products has not been synced yet
        for repo in repos:
            self.validate_repo_content(
                repo, ['errata', 'packages'], after_sync=False)
        # Wait the rest of expected time
        sleep(delay/2)
        # Verify product was synced successfully
        for repo in repos:
            self.validate_repo_content(
                repo, ['errata', 'package-groups', 'packages'])

    # This Bugzilla bug is private. It is impossible to fetch info about it.
    @stubbed('Unstub when BZ1279539 is fixed')
    @tier4
    def test_positive_synchronize_rh_product_current_sync_date(self):
        """Create a sync plan with current datetime as a sync date, add a
        RH product and verify the product gets synchronized on the next sync
        occurrence

        @Assert: Product is synchronized successfully.

        @Feature: SyncPlan

        @BZ: 1279539
        """
        interval = 60 * 60  # 'hourly' sync interval in seconds
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            'file': manifest.filename,
            'organization-id': org['id'],
        })
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'interval': 'hourly',
            'organization-id': org['id'],
            'sync-date': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        })
        RepositorySet.enable({
            'name': REPOSET['rhva6'],
            'organization-id': org['id'],
            'product': PRDS['rhel'],
            'releasever': '6Server',
            'basearch': 'x86_64',
        })
        product = Product.info({
            'name': PRDS['rhel'],
            'organization-id': org['id'],
        })
        repo = Repository.info({
            'name': REPOS['rhva6']['name'],
            'product': product['name'],
            'organization-id': org['id'],
        })
        # Associate sync plan with product
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        # Wait half of expected time
        sleep(interval / 2)
        # Verify product has not been synced yet
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Wait the rest of expected time
        sleep(interval / 2)
        # Verify product was synced successfully
        self.validate_repo_content(repo, ['errata', 'packages'])

    @tier4
    def test_positive_synchronize_rh_product_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync one RH
        product with it automatically.

        @Assert: Product is synchronized successfully.

        @Feature: SyncPlan
        """
        delay = 10 * 60  # delay for sync date in seconds
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            'file': manifest.filename,
            'organization-id': org['id'],
        })
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'organization-id': org['id'],
            'sync-date': (datetime.utcnow() + timedelta(seconds=delay))
                        .strftime("%Y-%m-%d %H:%M:%S"),
        })
        RepositorySet.enable({
            'name': REPOSET['rhva6'],
            'organization-id': org['id'],
            'product': PRDS['rhel'],
            'releasever': '6Server',
            'basearch': 'x86_64',
        })
        product = Product.info({
            'name': PRDS['rhel'],
            'organization-id': org['id'],
        })
        repo = Repository.info({
            'name': REPOS['rhva6']['name'],
            'product': product['name'],
            'organization-id': org['id'],
        })
        # Verify product is not synced and doesn't have any content
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Associate sync plan with product
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        # Wait half of expected time
        sleep(delay/2)
        # Verify product has not been synced yet
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Wait the rest of expected time
        sleep(delay/2)
        # Verify product was synced successfully
        self.validate_repo_content(repo, ['errata', 'packages'])
