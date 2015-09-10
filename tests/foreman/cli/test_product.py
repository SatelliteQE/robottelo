# -*- encoding: utf-8 -*-
"""Test class for Product CLI"""
import time

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.factory import (
    CLIFactoryError,
    make_gpg_key,
    make_org,
    make_product,
    make_repository,
    make_sync_plan,
)
from robottelo.cli.product import Product
from robottelo.decorators import data, run_only_on
from robottelo.helpers import bz_bug_is_open, generate_strings_list
from robottelo.test import CLITestCase


@ddt
class TestProduct(CLITestCase):
    """Product CLI tests."""

    org = None

    def setUp(self):  # noqa
        """Tests for Lifecycle Environment via Hammer CLI"""

        super(TestProduct, self).setUp()

        if TestProduct.org is None:
            TestProduct.org = make_org(cached=True)

    @run_only_on('sat')
    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_create_1(self, test_name):
        """@Test: Check if product can be created with random names

        @Feature: Product

        @Assert: Product is created and has random name

        """
        product = make_product({
            u'name': test_name['name'],
            u'organization-id': self.org['id']
        })

        self.assertEqual(product['name'], test_name['name'])
        self.assertGreater(len(product['label']), 0)

    @run_only_on('sat')
    @data(
        {u'name': gen_string('alpha', 15),
         u'label': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15),
         u'label': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15),
         u'label': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15),
         u'label': gen_string('alpha', 15)},
        {u'name': gen_string('utf8', 15),
         u'label': gen_string('alphanumeric', 15)},
        {u'name': gen_string('html', 15),
         u'label': gen_string('numeric', 15)},
    )
    def test_positive_create_2(self, test_data):
        """@Test: Check if product can be created with random labels

        @Feature: Product

        @Assert: Product is created and has random label

        """
        product = make_product({
            u'name': test_data['name'],
            u'label': test_data['label'],
            u'organization-id': self.org['id']
        })

        self.assertEqual(product['name'], test_data['name'])
        self.assertEqual(product['label'], test_data['label'])

    @run_only_on('sat')
    @data(
        {u'name': gen_string('alpha', 15),
         u'description': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15),
         u'description': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15),
         u'description': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15),
         u'description': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15),
         u'description': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15),
         u'description': gen_string('html', 15)},
    )
    def test_positive_create_3(self, test_data):
        """@Test: Check if product can be created with random description

        @Feature: Product

        @Assert: Product is created and has random description

        """
        product = make_product({
            u'name': test_data['name'],
            u'description': test_data['description'],
            u'organization-id': self.org['id']
        })

        self.assertEqual(product['name'], test_data['name'])
        self.assertEqual(product['description'], test_data['description'])

    @run_only_on('sat')
    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_create_4(self, test_data):
        """@Test: Check if product can be created with gpg key

        @Feature: Product

        @Assert: Product is created and has gpg key

        """
        gpg_key = make_gpg_key(
            {u'organization-id': self.org['id']}
        )
        product = make_product({
            u'name': test_data['name'],
            u'gpg-key-id': gpg_key['id'],
            u'organization-id': self.org['id']
        })

        self.assertEqual(product['name'], test_data['name'])
        self.assertEqual(product['gpg']['gpg-key-id'], gpg_key['id'])

    @run_only_on('sat')
    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_create_5(self, test_data):
        """@Test: Check if product can be created with sync plan

        @Feature: Product

        @Assert: Product is created and has random sync plan

        """
        sync_plan = make_sync_plan({u'organization-id': self.org['id']})
        product = make_product({
            u'name': test_data['name'],
            u'organization-id': self.org['id'],
            u'sync-plan-id': sync_plan['id'],
        })

        self.assertEqual(product['name'], test_data['name'])
        self.assertEqual(product['sync-plan-id'], sync_plan['id'])

    @run_only_on('sat')
    @data(
        {u'name': gen_string('alpha', 300)},
        {u'name': gen_string('alphanumeric', 300)},
        {u'name': gen_string('numeric', 300)},
        {u'name': gen_string('latin1', 300)},
        {u'name': gen_string('utf8', 300)},
        {u'name': gen_string('html', 300)},
    )
    def test_negative_create_1(self, test_name):
        """@Test: Check that only valid names can be used

        @Feature: Product

        @Assert: Product is not created

        """

        with self.assertRaises(CLIFactoryError):
            make_product(
                {
                    u'name': test_name['name'],
                    u'organization-id': self.org['id']
                }
            )

    @run_only_on('sat')
    @data(
        {u'name': gen_string('latin1', 15),
         u'label': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15),
         u'label': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15),
         u'label': gen_string('html', 15)},
    )
    def test_negative_create_2(self, test_name):
        """@Test: Check that only valid labels can be used

        @Feature: Product

        @Assert: Product is not created

        """

        with self.assertRaises(CLIFactoryError):
            make_product(
                {
                    u'name': test_name['name'],
                    u'label': test_name['label'],
                    u'organization-id': self.org['id']
                }
            )

    @run_only_on('sat')
    @data(
        {u'description': gen_string('alpha', 15)},
        {u'description': gen_string('alphanumeric', 15)},
        {u'description': gen_string('numeric', 15)},
        {u'description': gen_string('latin1', 15)},
        {u'description': gen_string('utf8', 15)},
        {u'description': gen_string('html', 15)},
    )
    def test_positive_update_1(self, test_data):
        """@Test: Update the description of a product

        @Feature: Product

        @Assert: Product description is updated

        """
        product = make_product({
            u'organization-id': self.org['id'],
        })

        # Update the Descriptions
        result = Product.update({
            u'id': product['id'],
            u'description': test_data['description'],
        })

        # Fetch it
        result = Product.info({
            u'id': product['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['description'], test_data['description'])
        self.assertNotEqual(
            product['description'], result.stdout['description'])

    @run_only_on('sat')
    def test_positive_update_2(self):
        """@Test: Update product's gpg keys

        @Feature: Product

        @Assert: Product gpg key is updated

        """
        first_gpg_key = make_gpg_key(
            {u'organization-id': self.org['id']}
        )
        second_gpg_key = make_gpg_key(
            {u'organization-id': self.org['id']}
        )
        product = make_product({
            u'organization-id': self.org['id'],
            u'gpg-key-id': first_gpg_key['id'],
        })

        # Update the Descriptions
        result = Product.update({
            u'id': product['id'],
            u'gpg-key-id': second_gpg_key['id'],
        })

        # Fetch it
        result = Product.info({
            u'id': product['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['gpg']['gpg-key-id'],
            second_gpg_key['id'],
        )
        self.assertNotEqual(
            result.stdout['gpg']['gpg-key-id'],
            first_gpg_key['id'],
        )

    @run_only_on('sat')
    def test_positive_update_3(self):
        """@Test: Update product's sync plan

        @Feature: Product

        @Assert: Product sync plan is updated

        """
        first_sync_plan = make_sync_plan({
            u'organization-id': self.org['id'],
        })
        second_sync_plan = make_sync_plan({
            u'organization-id': self.org['id'],
        })
        product = make_product({
            u'organization-id': self.org['id'],
            u'sync-plan-id': first_sync_plan['id'],
        })

        # Update the Descriptions
        result = Product.update({
            u'id': product['id'],
            u'sync-plan-id': second_sync_plan['id'],
        })

        # Fetch it
        result = Product.info({
            u'id': product['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['sync-plan-id'],
            second_sync_plan['id'],
        )
        self.assertNotEqual(
            result.stdout['sync-plan-id'],
            first_sync_plan['id'],
        )

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_positive_update_4(self, prod_name):
        """@Test: Rename Product back to original name

        @Feature: Product

        @Assert: Product Renamed to original

        """
        prod = make_product({
            u'name': prod_name,
            u'organization-id': self.org['id'],
        })
        new_prod_name = gen_string('alpha', 8)
        # Update the product name
        Product.update({
            u'id': prod['id'],
            u'name': new_prod_name,
        })
        # Verify Updated
        result = Product.info({
            u'id': prod['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(result.stdout['name'], new_prod_name)
        # Now, Rename product to original
        Product.update({
            u'id': prod['id'],
            u'name': prod_name,
        })
        result = Product.info({
            u'id': prod['id'],
            u'organization-id': self.org['id'],
        })
        # Verify renamed back to Original name.
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(result.stdout['name'], prod_name)

    @run_only_on('sat')
    def test_positive_delete_1(self):
        """@Test: Check if product can be deleted

        @Feature: Product

        @Assert: Product is deleted

        """
        new_product = make_product({
            u'organization-id': self.org['id']
        })

        # Delete it
        result = Product.delete({u'id': new_product['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch it
        result = Product.info({
            u'id': new_product['id'],
            u'organization-id': self.org['id'],
        })
        if bz_bug_is_open(1219490):
            for _ in range(5):
                if result.return_code == 0:
                    time.sleep(5)
                    result = Product.info({
                        u'id': new_product['id'],
                        u'organization-id': self.org['id'],
                    })
                else:
                    break
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    def test_add_syncplan_1(self):
        """@Test: Check if product can be assigned a syncplan

        @Feature: Product

        @Assert: Product has syncplan

        """
        try:
            new_product = make_product({
                u'organization-id': self.org['id']
            })
            sync_plan = make_sync_plan({'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        result = Product.set_sync_plan({
            'sync-plan-id': sync_plan['id'],
            'id': new_product['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        result = Product.info({
            'id': new_product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(result.stdout['sync-plan-id'], sync_plan['id'])

    def test_remove_syncplan_1(self):
        """@Test: Check if product can be assigned a syncplan

        @Feature: Product

        @Assert: Product has syncplan

        """
        try:
            product = make_product({u'organization-id': self.org['id']})
            sync_plan = make_sync_plan({'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        result = Product.set_sync_plan({
            'sync-plan-id': sync_plan['id'],
            'id': product['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        result = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(result.stdout['sync-plan-id'], sync_plan['id'])
        result = Product.remove_sync_plan({
            'id': product['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        result = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(len(result.stdout['sync-plan-id']), 0)

    def test_product_synchronize_by_id(self):
        """@Test: Check if product can be synchronized.
        Searches for product and organization by their IDs

        @Feature: Product

        @Assert: Product was synchronized

        """
        try:
            org = make_org()
            product = make_product({'organization-id': org['id']})
            make_repository({'product-id': product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        result = Product.synchronize({
            'id': product['id'],
            'organization-id': org['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = Product.info({
            'id': product['id'],
            'organization-id': org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(u'Syncing Complete.', result.stdout['sync-state'])

    def test_product_synchronize_by_name(self):
        """@Test: Check if product can be synchronized.
        Searches for product and organization by their Names

        @Feature: Product

        @Assert: Product was synchronized

        """
        try:
            org = make_org()
            product = make_product({'organization-id': org['id']})
            make_repository({'product-id': product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        result = Product.synchronize({
            'name': product['name'],
            'organization': org['name'],
        })
        self.assertEqual(result.return_code, 0)

        result = Product.info({
            'id': product['id'],
            'organization-id': org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(u'Syncing Complete.', result.stdout['sync-state'])

    def test_product_synchronize_by_label(self):
        """@Test: Check if product can be synchronized.
        Searches for organization by its label

        @Feature: Product

        @Assert: Product was synchronized

        """
        try:
            org = make_org()
            product = make_product({'organization-id': org['id']})
            make_repository({'product-id': product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        result = Product.synchronize({
            'id': product['id'],
            'organization-label': org['label'],
        })
        self.assertEqual(result.return_code, 0)

        result = Product.info({
            'id': product['id'],
            'organization-id': org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(u'Syncing Complete.', result.stdout['sync-state'])
