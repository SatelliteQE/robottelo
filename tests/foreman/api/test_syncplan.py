"""Unit tests for the ``repositories`` paths."""
from datetime import datetime, timedelta
from ddt import ddt
from fauxfactory import gen_string
from nailgun import client
from robottelo.common.helpers import get_server_credentials, get_server_url
from robottelo import entities
from robottelo.common.decorators import (
    data,
    run_only_on,
    skip_if_bug_open,
    stubbed,
)
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


class SyncPlanTestCase(APITestCase):
    """Miscellaneous tests for sync plans."""

    def test_get_routes(self):
        """@Test: Issue an HTTP GET response to both available routes.

        @Assert: The same response is returned.

        @Feature: SyncPlan

        Targets BZ 1132817.

        """
        org_id = entities.Organization().create_json()['id']
        entities.SyncPlan(organization=org_id).create_json()['id']
        response1 = client.get(
            '{0}/katello/api/v2/sync_plans'.format(get_server_url()),
            auth=get_server_credentials(),
            data={'organization_id': org_id},
            verify=False,
        )
        response2 = client.get(
            '{0}/katello/api/v2/organizations/{1}/sync_plans'.format(
                get_server_url(),
                org_id
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


@stubbed()
@ddt
class SyncPlanCreateTestCase(APITestCase):
    """Tests specific to creating new ``Sync Plans``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        cls.org_id = entities.Organization().create_json()['id']
        super(SyncPlanCreateTestCase, cls).setUpClass()

    @stubbed()
    @run_only_on('sat')
    def test_create_disabled_sync_plan(self):
        """@Test: Create a disabled Sync Plan.

        @Assert: A disabled sync plan is created.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_create_sync_plan_with_random_name(self, name):
        """@Test: Create a Sync Plan with a random name.

        @Assert: A sync plan is created with the specified name.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_create_sync_plan_with_random_description(self, description):
        """@Test: Create a Sync Plan with a random description.

        @Assert: A sync plan is created with the specified description.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    @data(
        u'hourly',
        u'daily',
        u'weekly',
    )
    def test_create_sync_plan_with_random_interval(self, interval):
        """@Test: Create a Sync Plan with a random interval.

        @Assert: A sync plan is created with the specified interval.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    @data(
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
    def test_create_sync_plan_with_random_sync_date(self, syncdate):
        """@Test: Create a Sync Plan and update its sync date.

        @Assert: A sync plan can be created with a random sync date.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    @data(
        gen_string('alpha', 300),
        gen_string('alphanumeric', 300),
        gen_string('numeric', 300),
        gen_string('latin1', 300),
        gen_string('utf8', 300),
        gen_string('html', 300),
    )
    def test_create_sync_plan_with_invalid_random_name(self, name):
        """@Test: Create a Sync Plan with an invalid name.

        @Assert: A sync plan can not be created with the specified name.

        @Feature: Sync Plan

        """


@stubbed()
@ddt
class SyncPlanUpdateTestCase(APITestCase):
    """Tests specific to updating a ``Sync Plan``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        cls.org_id = entities.Organization().create_json()['id']
        super(SyncPlanUpdateTestCase, cls).setUpClass()

    @stubbed()
    @run_only_on('sat')
    def test_update_enabled_sync_plan(self):
        """@Test: Create a enabled Sync Plan then disable it.

        @Assert: An enabled sync plan is created and updated to be disabled.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    def test_update_disabled_sync_plan(self):
        """@Test: Create a disabled Sync Plan then enable it.

        @Assert: A disabled sync plan is created and updated to be enabled.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_update_sync_plan_with_random_name(self, name):
        """@Test: Create a Sync Plan and update its name.

        @Assert: A sync plan is created and its name can be updated with the
        specified name.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_update_sync_plan_with_random_description(self, description):
        """@Test: Create a Sync Plan and update its description.

        @Assert: A sync plan is created and its description can be updated with
        the specified description.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    @data(
        u'hourly',
        u'daily',
        u'weekly',
    )
    def test_update_sync_plan_with_random_interval(self, interval):
        """@Test: Create a Sync Plan and update its interval.

        @Assert: A sync plan is created and its interval can be updated with
        the specified interval.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    @data(
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
    def test_update_sync_plan_with_random_sync_date(self, syncdate):
        """@Test: Create a Sync Plan and update its sync date.

        @Assert: A sync plan can be created and its sync date can be updated
        with the specified sync date.

        @Feature: Sync Plan

        """


class SyncPlanProductTestCase(APITestCase):
    """Tests specific to adding/removing products to ``Sync Plans``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and products which can be re-used in
        tests.

        """
        cls.org_id = entities.Organization().create_json()['id']
        super(SyncPlanProductTestCase, cls).setUpClass()

    @run_only_on('sat')
    def test_add_product(self):
        """@Test: Create a Sync Plan and add one product to it.

        @Assert: A sync plan can be created and one product can be added to it.

        @Feature: Sync Plan

        """
        syncplan_id = entities.SyncPlan(
            organization=self.org_id
        ).create_json()['id']
        product_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']
        syncplan = entities.SyncPlan(id=syncplan_id, organization=self.org_id)

        syncplan.add_products([product_id])
        syncplan_products = syncplan.read_json()['products']
        self.assertEqual(len(syncplan_products), 1)
        self.assertEqual(syncplan_products[0]['id'], product_id)

    @run_only_on('sat')
    def test_add_products(self):
        """@Test: Create a Sync Plan and add two products to it.

        @Assert: A sync plan can be created and two products can be added to
        it.

        @Feature: Sync Plan

        """
        syncplan_id = entities.SyncPlan(
            organization=self.org_id
        ).create_json()['id']
        product_ids = tuple(
            entities.Product(organization=self.org_id).create_json()['id']
            for _ in range(2)
        )
        syncplan = entities.SyncPlan(id=syncplan_id, organization=self.org_id)

        syncplan.add_products(product_ids)
        syncplan_products = syncplan.read_json()['products']
        self.assertEqual(len(syncplan_products), 2)
        self.assertEqual(
            set(product_ids),
            set((syncplan_products[0]['id'], syncplan_products[1]['id'])),
        )

    @skip_if_bug_open('bugzilla', 1199150)
    @run_only_on('sat')
    def test_remove_product(self):
        """@Test: Create a Sync Plan with two products and then remove one
        product from it.

        @Assert: A sync plan can be created and one product can be removed from
        it.

        @Feature: Sync Plan

        """
        syncplan_id = entities.SyncPlan(
            organization=self.org_id
        ).create_json()['id']
        product_ids = tuple(
            entities.Product(organization=self.org_id).create_json()['id']
            for _ in range(2)
        )
        syncplan = entities.SyncPlan(id=syncplan_id, organization=self.org_id)

        syncplan.add_products(product_ids)
        self.assertEqual(len(syncplan.read_json()['products']), 2)
        syncplan.remove_products([product_ids[0]])
        syncplan_products = syncplan.read_json()['products']
        self.assertEqual(len(syncplan_products), 1)
        self.assertEqual(syncplan_products[0]['id'], product_ids[1])

    @run_only_on('sat')
    def test_remove_products(self):
        """@Test: Create a Sync Plan with two products and then remove both
        products from it.

        @Assert: A sync plan can be created and both products can be removed
        from it.

        @Feature: Sync Plan

        """
        syncplan_id = entities.SyncPlan(
            organization=self.org_id
        ).create_json()['id']
        product_ids = tuple(
            entities.Product(organization=self.org_id).create_json()['id']
            for _ in range(2)
        )
        syncplan = entities.SyncPlan(id=syncplan_id, organization=self.org_id)

        syncplan.add_products(product_ids)
        self.assertEqual(len(syncplan.read_json()['products']), 2)
        syncplan.remove_products(product_ids)
        self.assertEqual(len(syncplan.read_json()['products']), 0)

    @skip_if_bug_open('bugzilla', 1199150)
    @run_only_on('sat')
    def test_repeatedly_add_remove(self):
        """@Test: Repeatedly add and remove a product from a sync plan.

        @Assert: A task is returned which can be used to monitor the additions
        and removals.

        @Feature: Sync Plan

        """
        syncplan_id = entities.SyncPlan(
            organization=self.org_id
        ).create_json()['id']
        product_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']
        syncplan = entities.SyncPlan(id=syncplan_id, organization=self.org_id)

        for _ in range(5):
            syncplan.add_products([product_id])
            self.assertEqual(len(syncplan.read_json()['products']), 1)
            syncplan.remove_products([product_id])
            self.assertEqual(len(syncplan.read_json()['products']), 0)


@stubbed()
class SyncPlanSynchronizeTestCase(APITestCase):
    """Tests specific to synchronizing ``Sync Plans``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and products which can be re-used in
        tests."""
        cls.org_id = entities.Organization().create_json()['id']
        cls.prod1_id = entities.Product(
            organization=cls.org_id
        ).create_json()['id']
        cls.prod2_id = entities.Product(
            organization=cls.org_id
        ).create_json()['id']
        super(SyncPlanSynchronizeTestCase, cls).setUpClass()

    @stubbed()
    @run_only_on('sat')
    def test_synchronize_sync_plan_with_one_product(self):
        """@Test: Create a Sync Plan with one product and sync it.

        @Assert: A sync plan is created with one product and product can be
        synchronized.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    def test_synchronize_sync_plan_with_two_products(self):
        """@Test: Create a Sync Plan with two products and sync them.

        @Assert: A sync plan is created with one product and products can be
        synchronized.

        @Feature: Sync Plan

        """


@stubbed()
class SyncPlanDeleteTestCase(APITestCase):
    """Tests specific to deleting ``Sync Plans``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        cls.org_id = entities.Organization().create_json()['id']
        super(SyncPlanDeleteTestCase, cls).setUpClass()

    @stubbed()
    @run_only_on('sat')
    def test_delete_sync_plan_with_one_product(self):
        """@Test: Create a Sync Plan with one product and delete it.

        @Assert: A sync plan is created with one product and sync plan can be
        deleted.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    def test_delete_sync_plan_with_two_products(self):
        """@Test: Create a Sync Plan with two products and delete them.

        @Assert: A sync plan is created with one product and sync plan can be
        deleted.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    def test_delete_sync_plan_with_one_synced_product(self):
        """@Test: Create a Sync Plan with one synced product and delete it.

        @Assert: A sync plan is created with one synced product and sync plan
        can be deleted.

        @Feature: Sync Plan

        """
