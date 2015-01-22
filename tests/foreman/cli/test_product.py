# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Product CLI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.cli.factory import (
    CLIFactoryError, make_gpg_key, make_org, make_product, make_sync_plan)
from robottelo.cli.product import Product
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.test import CLITestCase


@ddt
class TestProduct(CLITestCase):
    """Product CLI tests."""

    org = None

    def setUp(self):
        """Tests for Lifecycle Environment via Hammer CLI"""

        super(TestProduct, self).setUp()

        if TestProduct.org is None:
            TestProduct.org = make_org(cached=True)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1096320)
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

        @BZ: 1096320

        """

        new_product = make_product(
            {
                u'name': test_name['name'],
                u'organization-id': self.org['id']
            }
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['name'], new_product['name'], "Names don't match")
        self.assertGreater(
            len(result.stdout['label']), 0, "Label not automatically created"
        )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1096320)
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
    def test_positive_create_2(self, test_name):
        """@Test: Check if product can be created with random labels

        @Feature: Product

        @Assert: Product is created and has random label

        @BZ: 1096320

        """

        new_product = make_product(
            {
                u'name': test_name['name'],
                u'label': test_name['label'],
                u'organization-id': self.org['id']
            }
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['name'], new_product['name'], "Names don't match")
        self.assertEqual(
            result.stdout['label'], new_product['label'], "Labels don't match"
        )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1096320)
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
    def test_positive_create_3(self, test_name):
        """@Test: Check if product can be created with random description

        @Feature: Product

        @Assert: Product is created and has random description

        @BZ: 1096320

        """

        new_product = make_product(
            {
                u'name': test_name['name'],
                u'description': test_name['description'],
                u'organization-id': self.org['id']
            }
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['name'], new_product['name'], "Names don't match")
        self.assertEqual(
            result.stdout['description'],
            new_product['description'],
            "Descriptions don't match"
        )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1096320)
    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_create_4(self, test_name):
        """@Test: Check if product can be created with gpg key

        @Feature: Product

        @Assert: Product is created and has gpg key

        @BZ: 1096320

        """

        new_gpg_key = make_gpg_key(
            {u'organization-id': self.org['id']}
        )
        new_product = make_product(
            {
                u'name': test_name['name'],
                u'organization-id': self.org['id'],
                u'gpg-key-id': new_gpg_key['id'],
            }
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['name'], new_product['name'], "Names don't match")
        self.assertEqual(
            result.stdout['gpg']['gpg-key-id'],
            new_gpg_key['id'],
            "GPG Keys don't match")

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1096320)
    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_create_5(self, test_name):
        """@Test: Check if product can be created with sync plan

        @Feature: Product

        @Assert: Product is created and has random sync plan

        @BZ: 1096320

        """

        new_sync_plan = make_sync_plan({u'organization-id': self.org['id']})
        new_product = make_product(
            {
                u'name': test_name['name'],
                u'organization-id': self.org['id'],
                u'sync-plan-id': new_sync_plan['id'],
            }
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['name'], new_product['name'], "Names don't match")
        self.assertEqual(
            result.stdout['sync-plan-id'],
            new_sync_plan['id'],
            "Sync plans don't match")

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
    @skip_if_bug_open('bugzilla', 1096320)
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

        @BZ: 1096320

        """

        new_product = make_product(
            {
                u'organization-id': self.org['id']
            }
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Update the Descriptions
        result = Product.update(
            {u'id': new_product['id'],
             u'description': test_data['description']}
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['description'],
            test_data['description'],
            "Description was not updated"
        )
        self.assertNotEqual(
            result.stdout['description'],
            new_product['description'],
            "Descriptions should not match"
        )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1096320)
    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_update_2(self, test_name):
        """@Test: Update product's gpg keys

        @Feature: Product

        @Assert: Product gpg key is updated

        @BZ: 1096320

        """

        first_gpg_key = make_gpg_key(
            {u'organization-id': self.org['id']}
        )
        second_gpg_key = make_gpg_key(
            {u'organization-id': self.org['id']}
        )
        new_product = make_product(
            {
                u'name': test_name['name'],
                u'organization-id': self.org['id'],
            }
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # No gpg key yet
        self.assertEqual(
            len(result.stdout['gpg']['gpg-key-id']), 0, "No gpg key expected"
        )

        # Add first gpg key to product
        result = Product.update(
            {u'id': new_product['id'],
             u'gpg-key-id': first_gpg_key['id']}
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['gpg']['gpg-key-id'],
            first_gpg_key['id'],
            "GPG Keys don't match")
        self.assertNotEqual(
            result.stdout['gpg']['gpg-key-id'],
            second_gpg_key['id'],
            "GPG Keys should not match")

        # Remove first key by updating product to use second key
        result = Product.update(
            {u'id': new_product['id'],
             u'gpg-key-id': second_gpg_key['id']}
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['gpg']['gpg-key-id'],
            second_gpg_key['id'],
            "GPG Keys don't match"
        )
        self.assertNotEqual(
            result.stdout['gpg']['gpg-key-id'],
            first_gpg_key['id'],
            "GPG Keys should not match")

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1096320)
    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_update_3(self, test_name):
        """@Test: Update product's sync plan

        @Feature: Product

        @Assert: Product sync plan is updated

        @BZ: 1096320

        """

        first_sync_plan = make_sync_plan(
            {u'organization-id': self.org['id']}
        )
        second_sync_plan = make_sync_plan(
            {u'organization-id': self.org['id']}
        )
        new_product = make_product(
            {
                u'name': test_name['name'],
                u'organization-id': self.org['id'],
            }
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # No sync plan yet
        self.assertEqual(
            len(result.stdout['sync-plan-id']), 0, "No sync plan expected"
        )

        # Add first sync plan to product
        result = Product.update(
            {u'id': new_product['id'],
             u'sync-plan-id': first_sync_plan['id']}
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['sync-plan-id'],
            first_sync_plan['id'],
            "Sync plans don't match")
        self.assertNotEqual(
            result.stdout['sync-plan-id'],
            second_sync_plan['id'],
            "Sync plans should not match")

        # Remove first sync plan by updating product to use second plan
        result = Product.update(
            {u'id': new_product['id'],
             u'name': new_product['name'],
             u'sync-plan-id': second_sync_plan['id']}
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['sync-plan-id'],
            second_sync_plan['id'],
            "Sync plans don't match"
        )
        self.assertNotEqual(
            result.stdout['sync-plan-id'],
            first_sync_plan['id'],
            "Sync plans should not match")

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1096320)
    @data(
        {u'name': gen_string('alpha', 15)},
        {u'name': gen_string('alphanumeric', 15)},
        {u'name': gen_string('numeric', 15)},
        {u'name': gen_string('latin1', 15)},
        {u'name': gen_string('utf8', 15)},
        {u'name': gen_string('html', 15)},
    )
    def test_positive_delete_1(self, test_name):
        """@Test: Check if product can be deleted

        @Feature: Product

        @Assert: Product is deleted

        @BZ: 1096320

        """

        new_product = make_product(
            {
                u'name': test_name['name'],
                u'organization-id': self.org['id']
            }
        )

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['name'], new_product['name'], "Names don't match")
        self.assertGreater(
            len(result.stdout['label']), 0, "Label not automatically created"
        )

        # Delete it
        result = Product.delete({u'id': new_product['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = Product.info(
            {u'id': new_product['id'], u'organization-id': self.org['id']})
        self.assertNotEqual(
            result.return_code,
            0,
            "Product should not be found")
        self.assertGreater(
            len(result.stderr), 0, "Error was expected")

    def test_add_syncplan_1(self):
        """@Test: Check if product can be assigned a syncplan

        @Feature: Product

        @Assert: Product has syncplan

        """
        try:
            new_product = make_product(
                {
                    u'organization-id': self.org['id']
                }
            )
            sync_plan = make_sync_plan({'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        result = Product.set_sync_plan(
            {
                'sync-plan-id': sync_plan['id'],
                'id': new_product['id']
            }
        )
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            len(result.stderr), 0,
            "Running set_sync_plan should cause no errors.")
        result = Product.info({
            'id': new_product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            result.stderr, [],
            "Running product info should cause no errors.")
        self.assertEqual(
            result.stdout['sync-plan-id'], sync_plan['id'],
            "Info should have consistent sync ids.")

    def test_remove_syncplan_1(self):
        """@Test: Check if product can be assigned a syncplan

        @Feature: Product

        @Assert: Product has syncplan

        """
        try:
            product = make_product({u'organization-id': self.org['id']})
            sync_plan = make_sync_plan({'organization-id': self.org['id']})
            result = Product.set_sync_plan({
                'sync-plan-id': sync_plan['id'],
                'id': product['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(
            result.stderr, [],
            'Running set_sync_plan should cause no errors.'
        )
        result = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(
            result.stderr, [],
            'Running product info should cause no errors.'
        )
        self.assertEqual(
            result.stdout['sync-plan-id'], sync_plan['id'],
            'Info should have consistent sync ids.'
        )
        r_result = Product.remove_sync_plan({
            'id': product['id'],
        })
        self.assertEqual(
            r_result.stderr, [],
            'Running product remove_sync_plan should cause no errors.'
        )
        result = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(
            result.stderr, [],
            'Running product info should cause no errors.'
        )
        self.assertEqual(
            len(result.stdout['sync-plan-id']), 0,
            'Info should have no sync id.'
        )
