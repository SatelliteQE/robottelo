# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Product CLI
"""

from ddt import data
from ddt import ddt
from robottelo.cli.factory import make_gpg_key, make_org, make_product
from robottelo.cli.product import Product
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.helpers import generate_string
from nose.plugins.attrib import attr
from tests.cli.basecli import BaseCLI

import unittest


@ddt
class TestProduct(BaseCLI):
    """
    Product CLI tests.
    """

    org = None

    def setUp(self):
        """
        Tests for Lifecycle Environment via Hammer CLI
        """

        super(TestProduct, self).setUp()

        if TestProduct.org is None:
            TestProduct.org = make_org()

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'product')
    def test_positive_create_1(self, test_name):
        """
        @Test: Check if product can be created with random names
        @Feature: Product
        @Assert: Product is created and has random name
        """

        new_product = make_product(
            {
                'name': test_name['name'],
                'organization-id': self.org['label']
            }
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
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

    @data(
        {'name': generate_string('alpha', 15),
         'label': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15),
         'label': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15),
         'label': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15),
         'label': generate_string('alpha', 15)},
        {'name': generate_string('utf8', 15),
         'label': generate_string('alphanumeric', 15)},
        {'name': generate_string('html', 15),
         'label': generate_string('numeric', 15)},
    )
    @attr('cli', 'product')
    def test_positive_create_2(self, test_name):
        """
        @Test: Check if product can be created with random labels
        @Feature: Product
        @Assert: Product is created and has random label
        """

        new_product = make_product(
            {
                'name': test_name['name'],
                'label': test_name['label'],
                'organization-id': self.org['label']
            }
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
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

    @data(
        {'name': generate_string('alpha', 15),
         'description': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15),
         'description': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15),
         'description': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15),
         'description': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15),
         'description': generate_string('utf8', 15)},
        {'name': generate_string('html', 15),
         'description': generate_string('html', 15)},
    )
    @attr('cli', 'product')
    def test_positive_create_3(self, test_name):
        """
        @Test: Check if product can be created with random description
        @Feature: Product
        @Assert: Product is created and has random description
        """

        new_product = make_product(
            {
                'name': test_name['name'],
                'description': test_name['description'],
                'organization-id': self.org['label']
            }
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
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

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'product')
    def test_positive_create_4(self, test_name):
        """
        @Test: Check if product can be created with gpg key
        @Feature: Product
        @Assert: Product is created and has gpg key
        """

        new_gpg_key = make_gpg_key(
            {'organization-id': self.org['label']}
        )
        new_product = make_product(
            {
                'name': test_name['name'],
                'organization-id': self.org['label'],
                'gpg-key-id': new_gpg_key['id'],
            }
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['name'], new_product['name'], "Names don't match")
        self.assertEqual(
            result.stdout['gpg-key-id'],
            new_gpg_key['id'],
            "GPG Keys don't match")

    @unittest.skip(NOT_IMPLEMENTED)
    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'product')
    def test_positive_create_5(self, test_name):
        """
        @Test: Check if product can be created with sync plan
        @Feature: Product
        @Assert: Product is created and has random sync plan
        """

        pass

    @data(
        {'name': generate_string('alpha', 300)},
        {'name': generate_string('alphanumeric', 300)},
        {'name': generate_string('numeric', 300)},
        {'name': generate_string('latin1', 300)},
        {'name': generate_string('utf8', 300)},
        {'name': generate_string('html', 300)},
    )
    @attr('cli', 'product')
    def test_negative_create_1(self, test_name):
        """
        @Test: Check that only valid names can be used
        @Feature: Product
        @Assert: Product is not created
        """

        with self.assertRaises(Exception):
            make_product(
                {
                    'name': test_name['name'],
                    'organization-id': self.org['label']
                }
            )

    @data(
        {'name': generate_string('latin1', 15),
         'label': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15),
         'label': generate_string('utf8', 15)},
        {'name': generate_string('html', 15),
         'label': generate_string('html', 15)},
    )
    @attr('cli', 'product')
    def test_negative_create_2(self, test_name):
        """
        @Test: Check that only valid labels can be used
        @Feature: Product
        @Assert: Product is not created
        """

        with self.assertRaises(Exception):
            make_product(
                {
                    'name': test_name['name'],
                    'label': test_name['label'],
                    'organization-id': self.org['label']
                }
            )

    @data(
        {'description': generate_string('alpha', 15)},
        {'description': generate_string('alphanumeric', 15)},
        {'description': generate_string('numeric', 15)},
        {'description': generate_string('latin1', 15)},
        {'description': generate_string('utf8', 15)},
        {'description': generate_string('html', 15)},
    )
    @attr('cli', 'product')
    def test_positive_update_1(self, test_data):
        """
        @Test: Update the description of a product
        @Feature: Product
        @Assert: Product description is updated
        """

        new_product = make_product(
            {
                'organization-id': self.org['label']
            }
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Update the Descriptions
        result = Product.update(
            {'id': new_product['id'],
             'name': new_product['name'],
             'description': test_data['description']}
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
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

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'product')
    def test_positive_update_2(self, test_data):
        """
        @Test: Update the label of a product
        @Feature: Product
        @Assert: Product label is updated
        """

        new_product = make_product(
            {
                'name': test_data['name'],
                'organization-id': self.org['label']
            }
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        new_label = generate_string('alpha', 20)

        # Update the label
        result = Product.update(
            {'id': new_product['id'],
             'name': new_product['name'],
             'label': new_label}
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['label'],
            new_label,
            "Description was not updated"
        )
        self.assertNotEqual(
            result.stdout['label'],
            new_product['label'],
            "Labels should not match"
        )

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'product')
    def test_positive_update_3(self, test_name):
        """
        @Test: Update product's gpg keys
        @Feature: Product
        @Assert: Product gpg key is updated
        """

        first_gpg_key = make_gpg_key(
            {'organization-id': self.org['label']}
        )
        second_gpg_key = make_gpg_key(
            {'organization-id': self.org['label']}
        )
        new_product = make_product(
            {
                'name': test_name['name'],
                'organization-id': self.org['label'],
            }
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        # No gpg key yet
        self.assertEqual(
            len(result.stdout['gpg-key-id']), 0, "No gpg key expected"
        )

        # Add first gpg key to product
        result = Product.update(
            {'id': new_product['id'],
             'name': new_product['name'],
             'gpg-key-id': first_gpg_key['id']}
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['gpg-key-id'],
            first_gpg_key['id'],
            "GPG Keys don't match")
        self.assertNotEqual(
            result.stdout['gpg-key-id'],
            second_gpg_key['id'],
            "GPG Keys don't match")

        # Remove first key by updating product to use second key
        result = Product.update(
            {'id': new_product['id'],
             'name': new_product['name'],
             'gpg-key-id': second_gpg_key['id']}
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['gpg-key-id'],
            second_gpg_key['id'],
            "GPG Keys don't match"
        )
        self.assertNotEqual(
            result.stdout['gpg-key-id'],
            first_gpg_key['id'],
            "GPG Keys don't match")

    @unittest.skip(NOT_IMPLEMENTED)
    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'product')
    def test_positive_update_4(self, test_name):
        """
        @Test: Update product's sync plan
        @Feature: Product
        @Assert: Product sync plan is updated
        """

        pass

    @data(
        {'name': generate_string('alpha', 15)},
        {'name': generate_string('alphanumeric', 15)},
        {'name': generate_string('numeric', 15)},
        {'name': generate_string('latin1', 15)},
        {'name': generate_string('utf8', 15)},
        {'name': generate_string('html', 15)},
    )
    @attr('cli', 'product')
    def test_positive_delete_1(self, test_name):
        """
        @Test: Check if product can be deleted
        @Feature: Product
        @Assert: Product is deleted
        """

        new_product = make_product(
            {
                'name': test_name['name'],
                'organization-id': self.org['label']
            }
        )

        # Fetch it
        result = Product.info({'id': new_product['id']})
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
        result = Product.delete({'id': new_product['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Product was not deleted")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch it
        result = Product.info({'id': new_product['id']})
        self.assertNotEqual(
            result.return_code,
            0,
            "Product should not be found")
        self.assertGreater(
            len(result.stderr), 0, "Error was expected")
