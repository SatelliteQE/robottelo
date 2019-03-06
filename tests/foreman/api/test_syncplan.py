"""Unit tests for the ``sync_plans`` paths.

A full API reference for sync plans can be found here:
http://www.katello.org/docs/api/apidoc/sync_plans.html


:Requirement: Syncplan

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime, timedelta
from fauxfactory import gen_string, gen_choice
from nailgun import client, entities
from robottelo import manifests
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    wait_for_tasks,
    wait_for_syncplan_tasks
)
from robottelo.config import settings
from robottelo.constants import PRDS, REPOS, REPOSET, SYNC_INTERVAL
from robottelo.datafactory import (
    filtered_datapoint,
    invalid_values_list,
    valid_data_list,
    valid_cron_expressions
)
from requests.exceptions import HTTPError
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    tier1,
    tier2,
    tier3,
    tier4,
    upgrade
)
from robottelo.test import APITestCase
from time import sleep


@filtered_datapoint
def valid_sync_dates():
    """Returns a list of valid sync dates."""
    return [
        # Today
        datetime.now(),
        # 5 minutes from now
        datetime.now() + timedelta(seconds=300),
        # 5 days from now
        datetime.now() + timedelta(days=5),
        # Yesterday
        datetime.now() - timedelta(days=1),
        # 5 minutes ago
        datetime.now() - timedelta(seconds=300),
    ]


@filtered_datapoint
def valid_sync_interval():
    """Returns a list of valid sync intervals."""
    return [u'hourly', u'daily', u'weekly', u'custom cron']


class SyncPlanTestCase(APITestCase):
    """Miscellaneous tests for sync plans."""

    @tier1
    def test_positive_get_routes(self):
        """Issue an HTTP GET response to both available routes.

        :id: 9e40ea7f-71ea-4ced-94ba-cde03620c654

        :expectedresults: The same response is returned.

        Targets BZ 1132817.

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        entities.SyncPlan(organization=org).create()
        response1 = client.get(
            '{0}/katello/api/v2/sync_plans'.format(settings.server.get_url()),
            auth=settings.server.get_credentials(),
            data={'organization_id': org.id},
            verify=False,
        )
        response2 = client.get(
            '{0}/katello/api/v2/organizations/{1}/sync_plans'.format(
                settings.server.get_url(),
                org.id
            ),
            auth=settings.server.get_credentials(),
            verify=False,
        )
        for response in (response1, response2):
            response.raise_for_status()
        self.assertEqual(
            response1.json()['results'],
            response2.json()['results'],
        )


class SyncPlanCreateTestCase(APITestCase):
    """Tests specific to creating new sync plans."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(SyncPlanCreateTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @run_only_on('sat')
    @tier1
    def test_positive_create_enabled_disabled(self):
        """Create sync plan with different 'enabled' field values.

        :id: df5837e7-3d0f-464a-bd67-86b423c16eb4

        :expectedresults: A sync plan is created, 'enabled' field has correct
            value.

        :CaseImportance: Critical
        """
        for enabled in (False, True):
            with self.subTest(enabled):
                sync_plan = entities.SyncPlan(
                    enabled=enabled,
                    organization=self.org,
                ).create()
                self.assertEqual(sync_plan.enabled, enabled)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create a sync plan with a random name.

        :id: c1263134-0d7c-425a-82fd-df5274e1f9ba

        :expectedresults: A sync plan is created with the specified name.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                syncplan = entities.SyncPlan(
                    name=name,
                    organization=self.org
                ).create()
                self.assertEqual(syncplan.name, name)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_description(self):
        """Create a sync plan with a random description.

        :id: 3e5745e8-838d-44a5-ad61-7e56829ad47c

        :expectedresults: A sync plan is created with the specified
            description.

        :CaseImportance: Critical
        """
        for description in valid_data_list():
            with self.subTest(description):
                sync_plan = entities.SyncPlan(
                    description=description,
                    organization=self.org,
                ).create()
                self.assertEqual(sync_plan.description, description)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_interval(self):
        """Create a sync plan with a random interval.

        :id: d160ed1c-b698-42dc-be0b-67ac693c7840

        :expectedresults: A sync plan is created with the specified interval.

        :CaseImportance: Critical
        """
        for interval in valid_sync_interval():
            sync_plan = entities.SyncPlan(
                description=gen_string('alpha'),
                organization=self.org,
                interval=interval
            )
            if interval == SYNC_INTERVAL['custom']:
                sync_plan.cron_expression = gen_choice((valid_cron_expressions()))
            sync_plan = sync_plan.create()
            self.assertEqual(sync_plan.interval, interval)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_sync_date(self):
        """Create a sync plan and update its sync date.

        :id: bdb6e0a9-0d3b-4811-83e2-2140b7bb62e3

        :expectedresults: A sync plan can be created with a random sync date.

        :CaseImportance: Critical
        """
        for syncdate in valid_sync_dates():
            with self.subTest(syncdate):
                sync_plan = entities.SyncPlan(
                    organization=self.org,
                    sync_date=syncdate,
                ).create()
                self.assertEqual(
                    syncdate.strftime('%Y/%m/%d %H:%M:%S +0000'),
                    sync_plan.sync_date
                )

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create a sync plan with an invalid name.

        :id: a3a0f844-2f81-4f87-9f68-c25506c29ce2

        :expectedresults: A sync plan can not be created with the specified
            name.

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.SyncPlan(
                        name=name,
                        organization=self.org
                    ).create()

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_interval(self):
        """Create a sync plan with invalid interval specified.

        :id: f5844526-9f58-4be3-8a96-3849a465fc02

        :expectedresults: A sync plan can not be created with invalid interval
            specified

        :CaseImportance: Critical
        """
        for interval in invalid_values_list():
            with self.subTest(interval):
                with self.assertRaises(HTTPError):
                    entities.SyncPlan(
                        interval=interval,
                        organization=self.org,
                    ).create()

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_empty_interval(self):
        """Create a sync plan with no interval specified.

        :id: b4686463-69c8-4538-b040-6fb5246a7b00

        :expectedresults: A sync plan can not be created with no interval
            specified.

        :CaseImportance: Critical
        """
        sync_plan = entities.SyncPlan(organization=self.org)
        sync_plan.create_missing()
        del sync_plan.interval
        with self.assertRaises(HTTPError):
            sync_plan.create(False)


class SyncPlanUpdateTestCase(APITestCase):
    """Tests specific to updating a sync plan."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(SyncPlanUpdateTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @run_only_on('sat')
    @tier1
    def test_positive_update_enabled(self):
        """Create sync plan and update it with opposite 'enabled' value.

        :id: 325c0ef5-c0e8-4cb9-b85e-87eb7f42c2f8

        :expectedresults: Sync plan is updated with different 'enabled' value.

        :CaseImportance: Critical
        """
        for enabled in (False, True):
            with self.subTest(enabled):
                sync_plan = entities.SyncPlan(
                    enabled=not enabled,
                    organization=self.org,
                ).create()
                sync_plan.enabled = enabled
                self.assertEqual(
                    sync_plan.update(['enabled']).enabled,
                    enabled
                )

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Create a sync plan and update its name.

        :id: dbfadf4f-50af-4aa8-8d7d-43988dc4528f

        :expectedresults: A sync plan is created and its name can be updated
            with the specified name.

        :CaseImportance: Critical
        """
        sync_plan = entities.SyncPlan(organization=self.org).create()
        for name in valid_data_list():
            with self.subTest(name):
                sync_plan.name = name
                self.assertEqual(sync_plan.update(['name']).name, name)

    @tier1
    @run_only_on('sat')
    def test_positive_update_description(self):
        """Create a sync plan and update its description.

        :id: 4769fe9c-9eec-40c8-b015-1e3d7e570bec

        :expectedresults: A sync plan is created and its description can be
            updated with the specified description.

        :CaseImportance: Critical
        """
        sync_plan = entities.SyncPlan(
            description=gen_string('alpha'),
            organization=self.org,
        ).create()
        for description in valid_data_list():
            with self.subTest(description):
                sync_plan.description = description
                self.assertEqual(
                    sync_plan.update(['description']).description,
                    description
                )

    @tier1
    @run_only_on('sat')
    def test_positive_update_interval(self):
        """Create a sync plan and update its interval.

        :id: cf2eddf8-b4db-430e-a9b0-83c626b45068

        :expectedresults: A sync plan is created and its interval can be
            updated with the specified interval.

        :CaseImportance: Critical
        """
        for interval in valid_sync_interval():
            sync_plan = entities.SyncPlan(
                description=gen_string('alpha'),
                organization=self.org,
                interval=interval
            )
            if interval == SYNC_INTERVAL['custom']:
                sync_plan.cron_expression = gen_choice(valid_cron_expressions())
            sync_plan = sync_plan.create()

            valid_intervals = valid_sync_interval()
            valid_intervals.remove(interval)
            new_interval = gen_choice(valid_intervals)
            sync_plan.interval = new_interval
            if new_interval == SYNC_INTERVAL['custom']:
                sync_plan.cron_expression = gen_choice(valid_cron_expressions())
                sync_plan = sync_plan.update(['interval', 'cron_expression'])
            else:
                sync_plan = sync_plan.update(['interval'])
            self.assertEqual(sync_plan.interval, new_interval)

    @tier1
    @run_only_on('sat')
    def test_positive_update_interval_custom_cron(self):
        """Create a sync plan and update its interval to custom cron.

        :id: 26c58319-cae0-4b0c-b388-2a1fe3f22344

        :expectedresults: A sync plan is created and its interval can be
            updated to custom cron.

        :CaseImportance: Critical
        """
        for interval in valid_sync_interval():
            if interval != SYNC_INTERVAL['custom']:
                sync_plan = entities.SyncPlan(
                    description=gen_string('alpha'),
                    organization=self.org,
                    interval=interval
                ).create()

                sync_plan.interval = SYNC_INTERVAL['custom']
                sync_plan.cron_expression = gen_choice(valid_cron_expressions())
                self.assertEqual(
                    sync_plan.update(['interval', 'cron_expression']).interval,
                    SYNC_INTERVAL['custom']
                )

    @run_only_on('sat')
    @tier1
    def test_positive_update_sync_date(self):
        """Updated sync plan's sync date.

        :id: fad472c7-01b4-453b-ae33-0845c9e0dfd4

        :expectedresults: Sync date is updated with the specified sync date.

        :CaseImportance: Critical
        """
        sync_plan = entities.SyncPlan(
            organization=self.org,
            sync_date=datetime.now() + timedelta(days=10),
            ).create()
        for syncdate in valid_sync_dates():
            with self.subTest(syncdate):
                sync_plan.sync_date = syncdate
                self.assertEqual(
                    syncdate.strftime('%Y/%m/%d %H:%M:%S +0000'),
                    sync_plan.update(['sync_date']).sync_date
                )

    @tier1
    @run_only_on('sat')
    def test_negative_update_name(self):
        """Try to update a sync plan with an invalid name.

        :id: ae502053-9d3c-4cad-aee4-821f846ceae5

        :expectedresults: A sync plan can not be updated with the specified
            name.

        :CaseImportance: Critical
        """
        sync_plan = entities.SyncPlan(organization=self.org).create()
        for name in invalid_values_list():
            with self.subTest(name):
                sync_plan.name = name
                with self.assertRaises(HTTPError):
                    sync_plan.update(['name'])

    @tier1
    @run_only_on('sat')
    def test_negative_update_interval(self):
        """Try to update a sync plan with invalid interval.

        :id: 8c981174-6f55-49c0-8baa-40e5c3fc598c

        :expectedresults: A sync plan can not be updated with empty interval
            specified.

        :CaseImportance: Critical
        """
        sync_plan = entities.SyncPlan(organization=self.org).create()
        for interval in invalid_values_list():
            with self.subTest(interval):
                sync_plan.interval = interval
                with self.assertRaises(HTTPError):
                    sync_plan.update(['interval'])


class SyncPlanProductTestCase(APITestCase):
    """Tests specific to adding/removing products to sync plans."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and products which can be re-used in
        tests.
        """
        super(SyncPlanProductTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier2
    @run_only_on('sat')
    def test_positive_add_product(self):
        """Create a sync plan and add one product to it.

        :id: 036dea02-f73d-4fc1-9c41-5515b6659c79

        :expectedresults: A sync plan can be created and one product can be
            added to it.

        :CaseLevel: Integration
        """
        syncplan = entities.SyncPlan(organization=self.org).create()
        product = entities.Product(organization=self.org).create()
        syncplan.add_products(data={'product_ids': [product.id]})
        syncplan = syncplan.read()
        self.assertEqual(len(syncplan.product), 1)
        self.assertEqual(syncplan.product[0].id, product.id)

    @tier2
    @run_only_on('sat')
    def test_positive_add_products(self):
        """Create a sync plan and add two products to it.

        :id: 2a80ecad-2245-46d8-bbc6-0b802e68d50c

        :expectedresults: A sync plan can be created and two products can be
            added to it.

        :CaseLevel: Integration
        """
        syncplan = entities.SyncPlan(organization=self.org).create()
        products = [
            entities.Product(organization=self.org).create() for _ in range(2)
        ]
        syncplan.add_products(data={
            'product_ids': [product.id for product in products],
        })
        syncplan = syncplan.read()
        self.assertEqual(len(syncplan.product), 2)
        self.assertEqual(
            set((product.id for product in products)),
            set((product.id for product in syncplan.product)),
        )

    @tier2
    @skip_if_bug_open('bugzilla', 1199150)
    @run_only_on('sat')
    def test_positive_remove_product(self):
        """Create a sync plan with two products and then remove one
        product from it.

        :id: 987a0d94-ceb7-4115-9770-2297e60a63fa

        :expectedresults: A sync plan can be created and one product can be
            removed from it.

        :CaseLevel: Integration
        """
        syncplan = entities.SyncPlan(organization=self.org).create()
        products = [
            entities.Product(organization=self.org).create() for _ in range(2)
        ]
        syncplan.add_products(data={
            'product_ids': [product.id for product in products],
        })
        self.assertEqual(len(syncplan.read().product), 2)
        syncplan.remove_products(data={'product_ids': [products[0].id]})
        syncplan = syncplan.read()
        self.assertEqual(len(syncplan.product), 1)
        self.assertEqual(syncplan.product[0].id, products[1].id)

    @tier2
    @run_only_on('sat')
    @upgrade
    def test_positive_remove_products(self):
        """Create a sync plan with two products and then remove both
        products from it.

        :id: eed8c239-8ba3-4dbd-aa6b-c289cd4efd47

        :expectedresults: A sync plan can be created and both products can be
            removed from it.

        :CaseLevel: Integration
        """
        syncplan = entities.SyncPlan(organization=self.org).create()
        products = [
            entities.Product(organization=self.org).create() for _ in range(2)
        ]
        syncplan.add_products(data={
            'product_ids': [product.id for product in products],
        })
        self.assertEqual(len(syncplan.read().product), 2)
        syncplan.remove_products(data={
            'product_ids': [product.id for product in products],
        })
        self.assertEqual(len(syncplan.read().product), 0)

    @tier2
    @skip_if_bug_open('bugzilla', 1199150)
    @run_only_on('sat')
    def test_positive_repeatedly_add_remove(self):
        """Repeatedly add and remove a product from a sync plan.

        :id: b67536ba-3a36-4bb7-a405-0e12081d5a7e

        :expectedresults: A task is returned which can be used to monitor the
            additions and removals.

        :CaseLevel: Integration
        """
        syncplan = entities.SyncPlan(organization=self.org).create()
        product = entities.Product(organization=self.org).create()
        for _ in range(5):
            syncplan.add_products(data={'product_ids': [product.id]})
            self.assertEqual(len(syncplan.read().product), 1)
            syncplan.remove_products(data={'product_ids': [product.id]})
            self.assertEqual(len(syncplan.read().product), 0)

    @run_only_on('sat')
    @tier2
    def test_positive_add_remove_products_custom_cron(self):
        """Create a sync plan with two products having custom_cron interval
         and then remove both products from it.

         :id: 5ce34eaa-3574-49ba-ab02-aa25515394aa

         :expectedresults: A sync plan can be created and both products can be
            removed from it.
         :CaseLevel: Integration
        """
        cron_expression = gen_choice(valid_cron_expressions())

        syncplan = entities.SyncPlan(organization=self.org,
                                     interval='custom cron',
                                     cron_expression=cron_expression
                                     ).create()
        products = [
            entities.Product(organization=self.org).create() for _ in range(2)
        ]
        syncplan.add_products(data={
            'product_ids': [product.id for product in products],
        })
        self.assertEqual(len(syncplan.read().product), 2)
        syncplan.remove_products(data={
            'product_ids': [product.id for product in products],
        })
        self.assertEqual(len(syncplan.read().product), 0)


class SyncPlanSynchronizeTestCase(APITestCase):
    """Tests specific to synchronizing sync plans."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(SyncPlanSynchronizeTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @staticmethod
    def validate_task_status(repo_id, max_tries=10, repo_backend_id=None):
        """Wait for Pulp and foreman_tasks to complete or timeout

        :param repo_id: Repository Id to identify the correct task
        :param max_tries: Max tries to poll for the task creation
        :param repo_backend_id: Backend identifier of repository to filter the
            pulp tasks
        """
        if repo_backend_id:
            wait_for_syncplan_tasks(repo_backend_id)
        wait_for_tasks(
            search_query='resource_type = Katello::Repository'
                         ' and owner.login = foreman_admin'
                         ' and resource_id = {}'.format(repo_id),
            max_tries=max_tries
        )

    def validate_repo_content(self, repo, content_types, after_sync=True):
        """Check whether corresponding content is present in repository before
        or after synchronization is performed

        :param repo: Repository entity instance to be validated
        :param content_types: List of repository content entities that
            should be validated (e.g. package, erratum, puppet_module)
        :param bool after_sync: Specify whether you perform validation before
            synchronization procedure is happened or after
        """
        repo = repo.read()
        for content in content_types:
            if after_sync:
                self.assertIsNotNone(
                    repo.last_sync, 'Repository unexpectedly was not synced.')
                self.assertGreater(
                    repo.content_counts[content],
                    0,
                    'Repository contains invalid number of content entities.'
                )
            else:
                self.assertIsNone(
                    repo.last_sync, 'Repository was unexpectedly synced.')
                self.assertFalse(
                    repo.content_counts[content],
                    'Repository contains invalid number of content entities.'
                )

    @tier4
    def test_negative_synchronize_custom_product_past_sync_date(self):
        """Verify product won't get synced immediately after adding association
        with a sync plan which has already been started

        :id: 263a6a79-8236-4757-bf9e-8d9091ba2a11

        :expectedresults: Product was not synchronized

        :BZ: 1279539

        :CaseLevel: System
        """
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(product=product).create()
        # Verify product is not synced and doesn't have any content
        with self.assertRaises(AssertionError):
            self.validate_task_status(repo.id, max_tries=2)
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Create and Associate sync plan with product
        sync_plan = entities.SyncPlan(
            organization=self.org,
            enabled=True,
            sync_date=datetime.utcnow(),
        ).create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        # Verify product was not synced right after it was added to sync plan
        with self.assertRaises(AssertionError):
            self.validate_task_status(repo.id, max_tries=2)
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)

    @tier4
    def test_positive_synchronize_custom_product_past_sync_date(self):
        """Create a sync plan with past datetime as a sync date, add a
        custom product and verify the product gets synchronized on the next
        sync occurrence

        :id: 0495cb39-2f15-4b6e-9828-1e9517c5c826

        :expectedresults: Product is synchronized successfully.

        :BZ: 1279539

        :CaseLevel: System
        """
        interval = 60 * 60  # 'hourly' sync interval in seconds
        delay = 4 * 60
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(product=product).create()
        # Create and Associate sync plan with product
        sync_plan = entities.SyncPlan(
            organization=self.org,
            enabled=True,
            interval=u'hourly',
            sync_date=datetime.utcnow() - timedelta(seconds=interval - delay),
        ).create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        # Verify product is not synced and doesn't have any content
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was not synced'.format(delay/4, product.name))
        sleep(delay/4)
        with self.assertRaises(AssertionError):
            self.validate_task_status(repo.id, max_tries=2)
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Wait until the next recurrence
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was synced'.format(delay, product.name))
        sleep(delay * 3/4)
        # Update with the current UTC time
        sync_plan.sync_date = datetime.utcnow() + timedelta(seconds=delay)
        sync_plan.update(['sync_date'])
        # Verify product was synced successfully
        self.validate_task_status(repo.id,
                                  repo_backend_id=repo.backend_identifier
                                  )
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'])

    @tier4
    @skip_if_bug_open('bugzilla', 1655595)
    def test_positive_synchronize_custom_product_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync one custom
        product with it automatically.

        :id: b70a0c50-7335-4285-b24c-edfc1187f034

        :expectedresults: Product is synchronized successfully.

        :CaseLevel: System
        """
        delay = 4 * 60  # delay for sync date in seconds
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(product=product).create()
        # Verify product is not synced and doesn't have any content
        with self.assertRaises(AssertionError):
            self.validate_task_status(repo.id, max_tries=2)
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Create and Associate sync plan with product
        sync_plan = entities.SyncPlan(
            organization=self.org,
            enabled=True,
            sync_date=datetime.utcnow() + timedelta(seconds=delay),
        ).create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        # Wait half of expected time
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was not synced'.format(delay/4, product.name))
        sleep(delay/4)
        # Verify product has not been synced yet
        with self.assertRaises(AssertionError):
            self.validate_task_status(repo.id, max_tries=2)
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Wait the rest of expected time
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was synced'.format(delay, product.name))
        sleep(delay * 3/4)
        # Update with the current UTC time
        sync_plan.sync_date = datetime.utcnow() + timedelta(seconds=delay)
        sync_plan.update(['sync_date'])
        # Verify product was synced successfully
        self.validate_task_status(repo.id,
                                  repo_backend_id=repo.backend_identifier
                                  )
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'])

    @tier4
    @upgrade
    @skip_if_bug_open('bugzilla', 1655595)
    def test_positive_synchronize_custom_products_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync multiple
        custom products with multiple repos automatically.

        :id: e646196e-3951-4297-8c3c-1494d9895347

        :expectedresults: Products are synchronized successfully.

        :CaseLevel: System
        """
        delay = 6 * 60  # delay for sync date in seconds
        products = [
            entities.Product(organization=self.org).create()
            for _ in range(3)
        ]
        repos = [
            entities.Repository(product=product).create()
            for product in products
            for _ in range(2)
        ]
        # Verify products have not been synced yet
        for repo in repos:
            with self.assertRaises(AssertionError):
                self.validate_task_status(repo.id)
        # Create and Associate sync plan with products
        sync_plan = entities.SyncPlan(
            organization=self.org,
            enabled=True,
            sync_date=datetime.utcnow() + timedelta(seconds=delay),
        ).create()
        sync_plan.add_products(data={
            'product_ids': [product.id for product in products]})
        # Wait half of expected time
        self.logger.info('Waiting {0} seconds to check products'
                         ' were not synced'.format(delay/4))
        sleep(delay/4)
        # Verify products has not been synced yet
        for repo in repos:
            with self.assertRaises(AssertionError):
                self.validate_task_status(repo.id, max_tries=2)
        # Wait the rest of expected time
        self.logger.info('Waiting {0} seconds to check products'
                         ' were synced'.format(delay))
        sleep(delay * 3/4)
        # Update with the current UTC time
        sync_plan.sync_date = datetime.utcnow() + timedelta(seconds=delay)
        sync_plan.update(['sync_date'])
        # Verify product was synced successfully
        for repo in repos:
            self.validate_task_status(repo.id,
                                      repo_backend_id=repo.backend_identifier
                                      )
            self.validate_repo_content(
                repo, ['erratum', 'package', 'package_group'])

    @run_in_one_thread
    @tier4
    def test_positive_synchronize_rh_product_past_sync_date(self):
        """Create a sync plan with past datetime as a sync date, add a
        RH product and verify the product gets synchronized on the next sync
        occurrence

        :id: 080c316d-4a06-4ee9-b5f6-1b210d8d0593

        :expectedresults: Product is synchronized successfully.

        :BZ: 1279539

        :CaseLevel: System
        """
        interval = 60 * 60  # 'hourly' sync interval in seconds
        delay = 4 * 60
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            entities.Subscription().upload(
                data={'organization_id': org.id},
                files={'content': manifest.content},
            )
        repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhst7']['name'],
            reposet=REPOSET['rhst7'],
            releasever=None,
        )
        product = entities.Product(
            name=PRDS['rhel'],
            organization=org,
        ).search()[0]
        repo = entities.Repository(id=repo_id).read()
        sync_plan = entities.SyncPlan(
            organization=org,
            enabled=True,
            interval=u'hourly',
            sync_date=datetime.utcnow() - timedelta(seconds=interval - delay),
        ).create()
        # Associate sync plan with product
        sync_plan.add_products(data={'product_ids': [product.id]})
        # Verify product has not been synced yet
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was not synced'.format(delay/4, product.name))
        sleep(delay/4)
        with self.assertRaises(AssertionError):
            self.validate_task_status(repo.id, max_tries=2)
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Wait until the next recurrence
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was synced'.format(delay, product.name))
        sleep(delay * 3/4)
        # Update with the current UTC time
        sync_plan.sync_date = datetime.utcnow() - timedelta(
            seconds=interval - delay)
        sync_plan.update(['sync_date'])
        # Verify product was synced successfully
        self.validate_task_status(repo.id,
                                  repo_backend_id=repo.backend_identifier
                                  )
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'])

    @run_in_one_thread
    @tier4
    @upgrade
    @skip_if_bug_open('bugzilla', 1655595)
    def test_positive_synchronize_rh_product_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync one RH
        product with it automatically.

        :id: 6697a00f-2181-4c2b-88eb-2333268d780b

        :expectedresults: Product is synchronized successfully.

        :CaseLevel: System
        """
        delay = 4 * 60  # delay for sync date in seconds
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            entities.Subscription().upload(
                data={'organization_id': org.id},
                files={'content': manifest.content},
            )
        repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhst7']['name'],
            reposet=REPOSET['rhst7'],
            releasever=None,
        )
        product = entities.Product(
            name=PRDS['rhel'],
            organization=org,
        ).search()[0]
        repo = entities.Repository(id=repo_id).read()
        sync_plan = entities.SyncPlan(
            organization=org,
            enabled=True,
            interval=u'hourly',
            sync_date=datetime.utcnow() + timedelta(seconds=delay),
        ).create()
        # Create and Associate sync plan with product
        sync_plan.add_products(data={'product_ids': [product.id]})
        # Verify product is not synced and doesn't have any content
        with self.assertRaises(AssertionError):
            self.validate_task_status(repo.id, max_tries=2)
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Wait half of expected time
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was not synced'.format(delay/4, product.name))
        sleep(delay/4)
        # Verify product has not been synced yet
        with self.assertRaises(AssertionError):
            self.validate_task_status(repo.id, max_tries=2)
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Wait the rest of expected time
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was synced'.format(delay, product.name))
        sleep(delay * 3/4)
        # Update with the current UTC time
        sync_plan.sync_date = datetime.utcnow() + timedelta(seconds=delay)
        sync_plan.update(['sync_date'])
        # Verify product was synced successfully
        self.validate_task_status(repo.id,
                                  repo_backend_id=repo.backend_identifier
                                  )
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'])

    @tier3
    def test_positive_synchronize_custom_product_daily_recurrence(self):
        """Create a daily sync plan with current datetime as a sync date,
        add a custom product and verify the product gets synchronized on
        the next sync occurrence

        :id: d60e33a0-f75c-498e-9e6f-0a2025295a9d

        :expectedresults: Product is synchronized successfully.

        :CaseLevel: System
        """
        delay = 4 * 60
        start_date = datetime.utcnow() - timedelta(days=1)\
            + timedelta(seconds=delay)
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(product=product).create()
        # Create and Associate sync plan with product
        sync_plan = entities.SyncPlan(
            organization=self.org,
            enabled=True,
            interval=u'hourly',
            sync_date=start_date,
        ).create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        # Verify product is not synced and doesn't have any content
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was not synced'.format(delay/4, product.name))
        sleep(delay/4)
        with self.assertRaises(AssertionError):
            self.validate_task_status(repo.id, max_tries=2)
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Wait the rest of expected time
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was synced'.format(delay, product.name))
        sleep(delay * 3/4)
        # Re-calculate and Update with the current UTC time
        start_date = datetime.utcnow() - timedelta(days=1)\
            + timedelta(seconds=delay)
        sync_plan.sync_date = start_date
        sync_plan.update(['sync_date'])
        # Verify product was synced successfully
        self.validate_task_status(repo.id,
                                  repo_backend_id=repo.backend_identifier
                                  )
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'])

    @skip_if_bug_open('bugzilla', '1396647')
    @tier3
    def test_positive_synchronize_custom_product_weekly_recurrence(self):
        """Create a weekly sync plan with a past datetime as a sync date,
        add a custom product and verify the product gets synchronized on
        the next sync occurrence

        :id: ef52dd8e-756e-429c-8c30-b3e7db2b6d61

        :expectedresults: Product is synchronized successfully.

        :BZ: 1396647

        :CaseLevel: System
        """
        delay = 4 * 60
        start_date = datetime.utcnow() - timedelta(weeks=1) \
            + timedelta(seconds=delay)
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(product=product).create()
        # Create and Associate sync plan with product
        sync_plan = entities.SyncPlan(
            organization=self.org,
            enabled=True,
            interval=u'weekly',
            sync_date=start_date,
        ).create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        # Verify product is not synced and doesn't have any content
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was not synced'.format(delay/4, product.name))
        sleep(delay/4)
        with self.assertRaises(AssertionError):
            self.validate_task_status(repo.id, max_tries=2)
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Wait the rest of expected time
        self.logger.info('Waiting {0} seconds to check product {1}'
                         ' was synced'.format(delay, product.name))
        sleep(delay * 3/4)
        # Re-calculate and Update with the current UTC time
        start_date = datetime.utcnow() - timedelta(weeks=1) \
            + timedelta(seconds=delay)
        sync_plan.sync_date = start_date
        sync_plan.update(['sync_date'])
        # Verify product was synced successfully
        self.validate_task_status(repo.id,
                                  repo_backend_id=repo.backend_identifier
                                  )
        self.validate_repo_content(
            repo, ['erratum', 'package', 'package_group'])


class SyncPlanDeleteTestCase(APITestCase):
    """Tests specific to deleting sync plans."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(SyncPlanDeleteTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier2
    @run_only_on('sat')
    def test_positive_delete_one_product(self):
        """Create a sync plan with one product and delete it.

        :id: e565c464-33e2-4bca-8eca-15d5a7d4b155

        :expectedresults: A sync plan is created with one product and sync plan
            can be deleted.

        :CaseLevel: Integration
        """
        sync_plan = entities.SyncPlan(organization=self.org).create()
        product = entities.Product(organization=self.org).create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        sync_plan.delete()
        with self.assertRaises(HTTPError):
            sync_plan.read()

    @tier2
    @run_only_on('sat')
    def test_positive_delete_products(self):
        """Create a sync plan with two products and delete them.

        :id: f21bd57f-369e-4acd-a492-5532349a3804

        :expectedresults: A sync plan is created with one product and sync plan
            can be deleted.

        :CaseLevel: Integration
        """
        sync_plan = entities.SyncPlan(organization=self.org).create()
        products = [
            entities.Product(organization=self.org).create() for _ in range(2)
        ]
        sync_plan.add_products(data={
            'product_ids': [product.id for product in products],
        })
        sync_plan.delete()
        with self.assertRaises(HTTPError):
            sync_plan.read()

    @tier2
    @run_only_on('sat')
    @upgrade
    def test_positive_delete_synced_product(self):
        """Create a sync plan with one synced product and delete it.

        :id: 195d8fec-1fa0-42ab-84a5-32dd81a285ca

        :expectedresults: A sync plan is created with one synced product and
            sync plan can be deleted.

        :CaseLevel: Integration
        """
        sync_plan = entities.SyncPlan(organization=self.org).create()
        product = entities.Product(organization=self.org).create()
        entities.Repository(product=product).create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        product.sync()
        sync_plan.delete()
        with self.assertRaises(HTTPError):
            sync_plan.read()

    @tier2
    @run_only_on('sat')
    @upgrade
    def test_positive_delete_synced_product_custom_cron(self):
        """Create a sync plan with custom cron with one synced
        product and delete it.

        :id: f13936f5-7522-43b8-a986-26795637cde9

        :expectedresults: A sync plan is created with one synced product and
            sync plan can be deleted.

        :CaseLevel: Integration
        """
        sync_plan = entities.SyncPlan(
            organization=self.org,
            interval='custom cron',
            cron_expression=gen_choice((valid_cron_expressions()))).create()
        product = entities.Product(organization=self.org).create()
        entities.Repository(product=product).create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        product.sync()
        product = product.read()
        self.assertEqual(product.sync_plan.id, sync_plan.id)
        sync_plan.delete()
        product = product.read()
        self.assertIsNone(product.sync_plan)
        with self.assertRaises(HTTPError):
            sync_plan.read()
