# -*- encoding: utf-8 -*-
"""Unit tests for the ``products`` paths.

A full API reference for products can be found here:
http://theforeman.org/api/apidoc/v2/products.html

"""
from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from random import randint
from robottelo.common.constants import VALID_GPG_KEY_FILE
from robottelo.common.decorators import data, run_only_on
from robottelo.common.helpers import read_data_file
from robottelo.test import APITestCase


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
        product = entities.Product(**attrs).create()
        for name, value in attrs.items():
            self.assertEqual(getattr(product, name), value)

    @run_only_on('sat')
    def test_positive_create_2(self):
        """@Test: Create a product and provide a GPG key.

        @Assert: A product is created with the specified GPG key.

        @Feature: Product

        """
        # Create an organization, GPG key and product.
        #
        # product -----------↘
        #       `-→ gpg_key → organization
        #
        # Re-using an organization speeds up the test.
        org = entities.Organization().create()
        gpg_key = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=org,
        ).create()
        product = entities.Product(gpg_key=gpg_key, organization=org).create()
        self.assertEqual(product.gpg_key.id, gpg_key.id)


@run_only_on('sat')
@ddt
class ProductUpdateTestCase(APITestCase):
    """Tests for updating a product."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create a product."""
        cls.product = entities.Product().create()

    @data(
        (u'name', gen_string('alphanumeric', randint(1, 255))),
        (u'name', gen_string('alpha', randint(1, 255))),
        (u'name', gen_string('cjk', randint(1, 85))),
        (u'name', gen_string('latin1', randint(1, 255))),
        (u'name', gen_string('numeric', randint(1, 255))),
        (u'name', gen_string('utf8', randint(1, 85))),
        (u'description', gen_string('alphanumeric', randint(1, 255))),
        (u'description', gen_string('alpha', randint(1, 255))),
        (u'description', gen_string('cjk', randint(1, 85))),
        (u'description', gen_string('latin1', randint(1, 255))),
        (u'description', gen_string('numeric', randint(1, 255))),
        (u'description', gen_string('utf8', randint(1, 85))),
    )
    def test_positive_update_1(self, attrs):
        """@Test: Update a product with a new name or description.

        @Assert: The given attributes are used.

        @Feature: Product

        """
        setattr(self.product, attrs[0], attrs[1])
        self.product = self.product.update()
        self.assertEqual(getattr(self.product, attrs[0]), attrs[1])
