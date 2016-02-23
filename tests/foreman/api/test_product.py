# -*- encoding: utf-8 -*-
"""Unit tests for the ``products`` paths.

A full API reference for products can be found here:
http://theforeman.org/api/apidoc/v2/products.html
"""
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.constants import VALID_GPG_KEY_BETA_FILE, VALID_GPG_KEY_FILE
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import run_only_on, skip_if_bug_open, tier1, tier2
from robottelo.helpers import read_data_file
from robottelo.test import APITestCase


class ProductTestCase(APITestCase):
    """Tests for ``katello/api/v2/products``."""

    @classmethod
    def setUpClass(cls):
        """Set up organization for tests."""
        super(ProductTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create a product providing different valid names

        @Assert: A product is created with expected name.

        @Feature: Product
        """
        for name in valid_data_list():
            with self.subTest(name):
                product = entities.Product(
                    name=name, organization=self.org).create()
                self.assertEqual(name, product.name)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_label(self):
        """Create a product providing label which is different from its name

        @Assert: A product is created with expected label.

        @Feature: Product
        """
        label = gen_string('alphanumeric')
        product = entities.Product(label=label, organization=self.org).create()
        self.assertEqual(label, product.label)
        self.assertNotEqual(label, product.name)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_description(self):
        """Create a product providing different descriptions

        @Assert: A product is created with expected description.

        @Feature: Product
        """
        for desc in valid_data_list():
            with self.subTest(desc):
                product = entities.Product(
                    description=desc, organization=self.org).create()
                self.assertEqual(desc, product.description)

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_gpg(self):
        """Create a product and provide a GPG key.

        @Assert: A product is created with the specified GPG key.

        @Feature: Product
        """
        # Create an organization, GPG key and product.
        #
        # product -----------↘
        #       `-→ gpg_key → organization
        gpg_key = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=self.org,
        ).create()
        product = entities.Product(
            gpg_key=gpg_key, organization=self.org).create()
        self.assertEqual(product.gpg_key.id, gpg_key.id)

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_name(self):
        """Create a product providing invalid names only

        @Assert: A product is not created

        @Feature: Product
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Product(name=name).create()

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Create a product providing a name of already existent entity

        @Assert: A product is not created

        @Feature: Product
        """
        name = gen_string('alphanumeric')
        entities.Product(name=name, organization=self.org).create()
        with self.assertRaises(HTTPError):
            entities.Product(name=name, organization=self.org).create()

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_label(self):
        """Create a product providing invalid label

        @Assert: A product is not created

        @Feature: Product
        """
        with self.assertRaises(HTTPError):
            entities.Product(label=gen_string('utf8')).create()

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update product name to another valid name.

        @Assert: Product name can be updated.

        @Feature: Product
        """
        product = entities.Product(organization=self.org).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                product.name = new_name
                product = product.update(['name'])
                self.assertEqual(new_name, product.name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_description(self):
        """Update product description to another valid one.

        @Assert: Product description can be updated.

        @Feature: Product
        """
        product = entities.Product(organization=self.org).create()
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                product.description = new_desc
                product = product.update(['description'])
                self.assertEqual(new_desc, product.description)

    @run_only_on('sat')
    @tier1
    def test_positive_update_name_to_original(self):
        """Rename Product back to original name

        @Feature: Product

        @Assert: Product Renamed to original
        """
        product = entities.Product(organization=self.org).create()
        new_name = gen_string('alpha')
        old_name = product.name
        # Update new product name
        product.name = new_name
        self.assertEqual(
            product.name,
            product.update(['name']).name
        )
        # Rename product to old name and verify
        product.name = old_name
        self.assertEqual(
            product.name,
            product.update(['name']).name
        )

    @run_only_on('sat')
    @tier2
    def test_positive_update_gpg(self):
        """Create a product and update its GPGKey

        @Assert: The updated product points to a new GPG key.

        @Feature: Product
        """
        # Create a product and make it point to a GPG key.
        gpg_key_1 = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=self.org,
        ).create()
        product = entities.Product(
            gpg_key=gpg_key_1, organization=self.org).create()

        # Update the product and make it point to a new GPG key.
        gpg_key_2 = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_BETA_FILE),
            organization=self.org,
        ).create()
        product.gpg_key = gpg_key_2
        product = product.update()
        self.assertEqual(product.gpg_key.id, gpg_key_2.id)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1310422)
    @tier2
    def test_positive_update_organization(self):
        """Create a product and update its organization

        @Assert: The updated product points to a new organization

        @Feature: Product
        """
        product = entities.Product(organization=self.org).create()
        # Update the product and make it point to a new organization.
        new_org = entities.Organization().create()
        product.organization = new_org
        product = product.update()
        self.assertEqual(product.organization.id, new_org.id)

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Attempt to update product name to invalid one

        @Assert: Product is not updated

        @Feature: Product
        """
        product = entities.Product(organization=self.org).create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.Product(
                        id=product.id,
                        name=new_name,
                    ).update(['name'])

    @run_only_on('sat')
    @tier1
    def test_negative_update_label(self):
        """Attempt to update product label to another one.

        @Assert: Product is not updated and error is raised

        @Feature: Product
        """
        product = entities.Product(organization=self.org).create()
        product.label = gen_string('alpha')
        with self.assertRaises(HTTPError):
            product.update(['label'])

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Create product and then delete it.

        @Assert: Product is successfully deleted.

        @Feature: Product
        """
        for name in valid_data_list():
            with self.subTest(name):
                product = entities.Product(name=name).create()
                product.delete()
                with self.assertRaises(HTTPError):
                    entities.Product(id=product.id).read()
