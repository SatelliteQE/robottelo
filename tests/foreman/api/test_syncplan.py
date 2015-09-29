# pylint: disable=invalid-name
"""Unit tests for the ``sync_plans`` paths.

A full API reference for sync plans can be found here:
http://www.katello.org/docs/api/apidoc/sync_plans.html

"""
from datetime import datetime, timedelta
from fauxfactory import gen_string
from nailgun import client, entities
from random import sample
from requests.exceptions import HTTPError
from robottelo.helpers import (
    get_server_credentials,
    get_server_url,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import run_only_on, skip_if_bug_open, stubbed
from robottelo.test import APITestCase


def valid_sync_dates():
    """Returns a tuple of valid sync dates."""
    return(
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
    )


def valid_sync_interval():
    """Returns a tuple of valid sync intervals."""
    return (u'hourly', u'daily', u'weekly')


class SyncPlanTestCase(APITestCase):
    """Miscellaneous tests for sync plans."""

    def test_get_routes(self):
        """@Test: Issue an HTTP GET response to both available routes.

        @Assert: The same response is returned.

        @Feature: SyncPlan

        Targets BZ 1132817.

        """
        org = entities.Organization().create()
        entities.SyncPlan(organization=org).create()
        response1 = client.get(
            '{0}/katello/api/v2/sync_plans'.format(get_server_url()),
            auth=get_server_credentials(),
            data={'organization_id': org.id},
            verify=False,
        )
        response2 = client.get(
            '{0}/katello/api/v2/organizations/{1}/sync_plans'.format(
                get_server_url(),
                org.id
            ),
            auth=get_server_credentials(),
            verify=False,
        )
        for response in (response1, response2):
            response.raise_for_status()
        self.assertEqual(
            response1.json()['results'],
            response2.json()['results'],
        )


@run_only_on('sat')
class SyncPlanCreateTestCase(APITestCase):
    """Tests specific to creating new sync plans."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        cls.org = entities.Organization().create()
        super(SyncPlanCreateTestCase, cls).setUpClass()

    def test_create_enabled_disabled_sync_plan(self):
        """@Test: Create sync plan with different 'enabled' field values.

        @Assert: A sync plan is created, 'enabled' field has correct value.

        @Feature: SyncPlan

        """
        for enabled in (False, True):
            with self.subTest(enabled):
                sync_plan = entities.SyncPlan(
                    enabled=enabled,
                    organization=self.org,
                ).create()
                self.assertEqual(sync_plan.enabled, enabled)

    def test_create_sync_plan_with_random_name(self, name):
        """@Test: Create a sync plan with a random name.

        @Assert: A sync plan is created with the specified name.

        @Feature: SyncPlan

        """
        for name in valid_data_list():
            with self.subTest(name):
                syncplan = entities.SyncPlan(
                    name=name,
                    organization=self.org
                ).create()
                self.assertEqual(syncplan.name, name)

    def test_create_sync_plan_with_random_description(self):
        """@Test: Create a sync plan with a random description.

        @Assert: A sync plan is created with the specified description.

        @Feature: SyncPlan

        """
        for description in valid_data_list():
            with self.subTest(description):
                sync_plan = entities.SyncPlan(
                    description=description,
                    organization=self.org,
                ).create()
                self.assertEqual(sync_plan.description, description)

    def test_create_sync_plan_with_random_interval(self):
        """@Test: Create a sync plan with a random interval.

        @Assert: A sync plan is created with the specified interval.

        @Feature: SyncPlan

        """
        for interval in valid_sync_interval:
            with self.subTest(interval):
                sync_plan = entities.SyncPlan(
                    interval=interval,
                    organization=self.org,
                ).create()
                self.assertEqual(sync_plan.interval, interval)

    def test_create_sync_plan_with_random_sync_date(self):
        """@Test: Create a sync plan and update its sync date.

        @Assert: A sync plan can be created with a random sync date.

        @Feature: SyncPlan

        """
        for syncdate in valid_sync_dates():
            with self.subTest(syncdate):
                sync_plan = entities.SyncPlan(
                    organization=self.org,
                    sync_date=syncdate,
                ).create()
                self.assertEqual(
                    syncdate.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    sync_plan.sync_date
                )

    def test_create_sync_plan_with_invalid_name_negative(self, name):
        """@Test: Create a sync plan with an invalid name.

        @Assert: A sync plan can not be created with the specified name.

        @Feature: SyncPlan

        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.SyncPlan(
                        name=name,
                        organization=self.org
                    ).create()

    def test_create_sync_plan_with_invalid_interval_negative(self, interval):
        """@Test: Create a sync plan with invalid interval specified.

        @Assert: A sync plan can not be created with invalid interval specified

        @Feature: SyncPlan

        """
        for interval in invalid_values_list():
            with self.subTest(interval):
                with self.assertRaises(HTTPError):
                    entities.SyncPlan(
                        interval=interval,
                        organization=self.org,
                    ).create()

    def test_create_sync_plan_with_empty_interval_negative(self):
        """@Test: Create a sync plan with no interval specified.

        @Assert: A sync plan can not be created with no interval specified.

        @Feature: SyncPlan

        """
        sync_plan = entities.SyncPlan(organization=self.org)
        sync_plan.create_missing()
        del sync_plan.interval
        with self.assertRaises(HTTPError):
            sync_plan.create(False)


@run_only_on('sat')
class SyncPlanUpdateTestCase(APITestCase):
    """Tests specific to updating a sync plan."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        cls.org = entities.Organization().create()
        super(SyncPlanUpdateTestCase, cls).setUpClass()

    def test_update_enabled_disabled_sync_plan(self):
        """@Test: Create sync plan and update it with opposite 'enabled' value.

        @Assert: Sync plan is updated with different 'enabled' value.

        @Feature: SyncPlan

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

    def test_update_sync_plan_with_random_name(self):
        """@Test: Create a sync plan and update its name.

        @Assert: A sync plan is created and its name can be updated with the
        specified name.

        @Feature: SyncPlan

        """
        sync_plan = entities.SyncPlan(organization=self.org).create()
        for name in valid_data_list():
            with self.subTest(name):
                sync_plan.name = name
                self.assertEqual(sync_plan.update(['name']).name, name)

    def test_update_sync_plan_with_random_description(self):
        """@Test: Create a sync plan and update its description.

        @Assert: A sync plan is created and its description can be updated with
        the specified description.

        @Feature: SyncPlan

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

    def test_update_sync_plan_with_random_interval(self):
        """@Test: Create a sync plan and update its interval.

        @Assert: A sync plan is created and its interval can be updated with
        the specified interval.

        @Feature: SyncPlan

        """
        for interval in valid_sync_interval:
            with self.subTest(interval):
                sync_plan = entities.SyncPlan(organization=self.org)
                result = sync_plan.get_fields()['interval']
                sync_plan.interval = sample(
                    set(result.choices) - set([interval]),
                    1
                )[0]
                sync_plan = sync_plan.create()
                sync_plan.interval = interval
                self.assertEqual(
                    sync_plan.update(['interval']).interval,
                    interval
                )

    def test_update_sync_plan_with_random_sync_date(self):
        """@Test: Updated sync plan's sync date.

        @Assert: Sync date is updated with the specified sync date.

        @Feature: SyncPlan

        """
        sync_plan = entities.SyncPlan(
            organization=self.org,
            sync_date=datetime.now() + timedelta(days=10),
            ).create()
        for syncdate in valid_sync_dates():
            with self.subTest(syncdate):
                sync_plan.sync_date = syncdate
                self.assertEqual(
                    syncdate.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    sync_plan.update(['sync_date']).sync_date
                )

    def test_update_sync_plan_with_invalid_name_negative(self):
        """@Test: Try to update a sync plan with an invalid name.

        @Assert: A sync plan can not be updated with the specified name.

        @Feature: SyncPlan

        """
        sync_plan = entities.SyncPlan(organization=self.org).create()
        for name in invalid_values_list():
            with self.subTest(name):
                sync_plan.name = name
                with self.assertRaises(HTTPError):
                    sync_plan.update(['name'])

    def test_update_sync_plan_with_invalid_interval_negative(self, interval):
        """@Test: Try to update a sync plan with invalid interval.

        @Assert: A sync plan can not be updated with empty interval specified.

        @Feature: SyncPlan

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
        cls.org = entities.Organization().create()
        super(SyncPlanProductTestCase, cls).setUpClass()

    @run_only_on('sat')
    def test_add_product(self):
        """@Test: Create a sync plan and add one product to it.

        @Assert: A sync plan can be created and one product can be added to it.

        @Feature: SyncPlan

        """
        syncplan = entities.SyncPlan(organization=self.org).create()
        product = entities.Product(organization=self.org).create()
        syncplan.add_products(data={'product_ids': [product.id]})
        syncplan = syncplan.read()
        self.assertEqual(len(syncplan.product), 1)
        self.assertEqual(syncplan.product[0].id, product.id)

    @run_only_on('sat')
    def test_add_products(self):
        """@Test: Create a sync plan and add two products to it.

        @Assert: A sync plan can be created and two products can be added to
        it.

        @Feature: SyncPlan

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

    @skip_if_bug_open('bugzilla', 1199150)
    @run_only_on('sat')
    def test_remove_product(self):
        """@Test: Create a sync plan with two products and then remove one
        product from it.

        @Assert: A sync plan can be created and one product can be removed from
        it.

        @Feature: SyncPlan

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

    @run_only_on('sat')
    def test_remove_products(self):
        """@Test: Create a sync plan with two products and then remove both
        products from it.

        @Assert: A sync plan can be created and both products can be removed
        from it.

        @Feature: SyncPlan

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

    @skip_if_bug_open('bugzilla', 1199150)
    @run_only_on('sat')
    def test_repeatedly_add_remove(self):
        """@Test: Repeatedly add and remove a product from a sync plan.

        @Assert: A task is returned which can be used to monitor the additions
        and removals.

        @Feature: SyncPlan

        """
        syncplan = entities.SyncPlan(organization=self.org).create()
        product = entities.Product(organization=self.org).create()
        for _ in range(5):
            syncplan.add_products(data={'product_ids': [product.id]})
            self.assertEqual(len(syncplan.read().product), 1)
            syncplan.remove_products(data={'product_ids': [product.id]})
            self.assertEqual(len(syncplan.read().product), 0)


@stubbed()
class SyncPlanSynchronizeTestCase(APITestCase):
    """Tests specific to synchronizing sync plans."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and products which can be re-used in
        tests."""
        cls.org = entities.Organization().create()
        cls.products = [
            entities.Product(organization=cls.org).create() for _ in range(2)
        ]
        super(SyncPlanSynchronizeTestCase, cls).setUpClass()

    @stubbed()
    @run_only_on('sat')
    def test_synchronize_sync_plan_with_one_product(self):
        """@Test: Create a sync plan with one product and sync it.

        @Assert: A sync plan is created with one product and product can be
        synchronized.

        @Feature: SyncPlan

        """

    @stubbed()
    @run_only_on('sat')
    def test_synchronize_sync_plan_with_two_products(self):
        """@Test: Create a sync plan with two products and sync them.

        @Assert: A sync plan is created with one product and products can be
        synchronized.

        @Feature: SyncPlan

        """


@run_only_on('sat')
class SyncPlanDeleteTestCase(APITestCase):
    """Tests specific to deleting sync plans."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        cls.org = entities.Organization().create()
        super(SyncPlanDeleteTestCase, cls).setUpClass()

    def test_delete_sync_plan_with_one_product(self):
        """@Test: Create a sync plan with one product and delete it.

        @Assert: A sync plan is created with one product and sync plan can be
        deleted.

        @Feature: SyncPlan

        """
        sync_plan = entities.SyncPlan(organization=self.org).create()
        product = entities.Product(organization=self.org).create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        sync_plan.delete()
        with self.assertRaises(HTTPError):
            sync_plan.read()

    def test_delete_sync_plan_with_two_products(self):
        """@Test: Create a sync plan with two products and delete them.

        @Assert: A sync plan is created with one product and sync plan can be
        deleted.

        @Feature: SyncPlan

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

    def test_delete_sync_plan_with_one_synced_product(self):
        """@Test: Create a sync plan with one synced product and delete it.

        @Assert: A sync plan is created with one synced product and sync plan
        can be deleted.

        @Feature: SyncPlan

        """
        sync_plan = entities.SyncPlan(organization=self.org).create()
        product = entities.Product(organization=self.org).create()
        entities.Repository(product=product).create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        product.sync()
        sync_plan.delete()
        with self.assertRaises(HTTPError):
            sync_plan.read()
