"""Unit tests for the ``repositories`` paths."""
from datetime import datetime, timedelta
from ddt import ddt
from fauxfactory import gen_string
from robottelo import entities
from robottelo.common.decorators import (
    data, run_only_on, stubbed)
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


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


@ddt
class SyncPlanProductTestCase(APITestCase):
    """Tests specific to adding/removing products to ``Sync Plans``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and products which can be re-used in
        tests.

        """
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
    def test_add_one_product_to_sync_plan(self):
        """@Test: Create a Sync Plan and add one product to it.

        @Assert: A sync plan can be created and one product can be added to it.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    def test_add_two_producst_to_sync_plan(self):
        """@Test: Create a Sync Plan and add two products to it.

        @Assert: A sync plan can be created and two products can be added to
        it.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    def test_remove_one_product_to_sync_plan(self):
        """@Test: Create a Sync Plan with two products and then remove one
        product from it.

        @Assert: A sync plan can be created and one product can be removed from
        it.

        @Feature: Sync Plan

        """

    @stubbed()
    @run_only_on('sat')
    def test_remove_two_products_to_sync_plan(self):
        """@Test: Create a Sync Plan with two products and then remove both
        products from it.

        @Assert: A sync plan can be created and both products can be removed
        from it.

        @Feature: Sync Plan

        """


@ddt
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


@ddt
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
