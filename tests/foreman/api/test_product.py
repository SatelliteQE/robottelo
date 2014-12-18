"""Unit tests for the ``products`` paths.

A full API reference for products can be found here:
http://theforeman.org/api/apidoc/v2/products.html

"""
from ddt import ddt
from fauxfactory import gen_string
from nailgun import client
from random import randint
from robottelo import entities
from robottelo.common.constants import VALID_GPG_KEY_FILE
from robottelo.common.decorators import data, run_only_on
from robottelo.common.helpers import get_server_credentials, read_data_file
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


@ddt
class ProductsTestCase(APITestCase):
    """Tests for ``katello/api/v2/products``."""

    @run_only_on('sat')
    @data(
        {u'name': gen_string('alphanumeric', randint(1, 255))},
        {u'name': gen_string('alpha', randint(1, 255))},
        {u'name': gen_string('cjk', randint(1, 85))},
        {u'name': gen_string('latin1', randint(1, 255))},
        {u'name': gen_string('numeric', randint(1, 255))},
        {u'name': gen_string('utf8', randint(1, 85))},
        {u'description': gen_string('alphanumeric', randint(1, 255))},
        {u'description': gen_string('alpha', randint(1, 255))},
        {u'description': gen_string('cjk', randint(1, 85))},
        {u'description': gen_string('latin1', randint(1, 255))},
        {u'description': gen_string('numeric', randint(1, 255))},
        {u'description': gen_string('utf8', randint(1, 85))},
    )
    def test_positive_create_1(self, attrs):
        """@Test: Create a product and provide a name or description.

        @Assert: A product is created with the provided attributes.

        @Feature: Product

        """
        prod_id = entities.Product(**attrs).create()['id']
        prod_attrs = entities.Product(id=prod_id).read_json()
        for name, value in attrs.items():
            self.assertIn(name, prod_attrs.keys())
            self.assertEqual(value, prod_attrs[name])

    @run_only_on('sat')
    def test_positive_create_2(self):
        """@Test: Create a product and provide a GPG key.

        @Assert: A product is created with the specified GPG key.

        @Feature: Product

        """
        # Create an organization, GPG key and product.
        #
        # * GPG key points to organization
        # * Product points to organization and GPG key
        #
        # Re-using an organization speeds up the test.
        org_attrs = entities.Organization().create()
        gpgkey_attrs = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=org_attrs['id']
        ).create()
        product_attrs = entities.Product(
            gpg_key=gpgkey_attrs['id'],
            organization=org_attrs['id']
        ).create()

        # GET the product and verify it's GPG key ID.
        attrs = entities.Product(id=product_attrs['id']).read_json()
        self.assertEqual(attrs['gpg_key_id'], gpgkey_attrs['id'])


@run_only_on('sat')
@ddt
class ProductUpdateTestCase(APITestCase):
    """Tests for updating a product."""

    @classmethod
    def setUpClass(cls):
        """Create a product."""
        cls.product_n = entities.Product(
            id=entities.Product().create()['id']
        )

    @data(
        {u'name': gen_string('alphanumeric', randint(1, 255))},
        {u'name': gen_string('alpha', randint(1, 255))},
        {u'name': gen_string('cjk', randint(1, 85))},
        {u'name': gen_string('latin1', randint(1, 255))},
        {u'name': gen_string('numeric', randint(1, 255))},
        {u'name': gen_string('utf8', randint(1, 85))},
        {u'description': gen_string('alphanumeric', randint(1, 255))},
        {u'description': gen_string('alpha', randint(1, 255))},
        {u'description': gen_string('cjk', randint(1, 85))},
        {u'description': gen_string('latin1', randint(1, 255))},
        {u'description': gen_string('numeric', randint(1, 255))},
        {u'description': gen_string('utf8', randint(1, 85))},
    )
    def test_positive_update_1(self, attrs):
        """@Test: Update a product with a new name or description.

        @Assert: The given attributes are used.

        @Feature: Product

        """
        client.put(
            self.product_n.path(),
            attrs,
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()
        new_attrs = self.product_n.read_json()
        for name, value in attrs.items():
            self.assertIn(name, new_attrs.keys())
            self.assertEqual(value, new_attrs[name])
