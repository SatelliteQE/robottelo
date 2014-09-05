"""Unit tests for the ``products`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/products.html

"""
from robottelo.api import client
from robottelo.common.constants import VALID_GPG_KEY_FILE
from robottelo.common.helpers import get_server_credentials, read_data_file
from robottelo import entities, orm
from unittest import TestCase
import ddt


@ddt.ddt
class ProductsTestCase(TestCase):
    """Tests for ``katello/api/v2/products``."""

    @ddt.data(
        orm.StringField(str_type=('alphanumeric',)).get_value(),
        orm.StringField(str_type=('alpha',)).get_value(),
        orm.StringField(str_type=('numeric',)).get_value(),
    )
    def test_positive_create_1(self, name):
        """@Test: Create a product

        @Feature: Products

        @Assert: Product is created with specified name

        """
        prod_id = entities.Product(name=name).create()['id']
        prod_attrs = entities.Product(id=prod_id).read_json()
        self.assertEqual(prod_attrs['name'], name)

    @ddt.data(
        orm.StringField(str_type=('alphanumeric',)).get_value(),
        orm.StringField(str_type=('alpha',)).get_value(),
        orm.StringField(str_type=('numeric',)).get_value(),
    )
    def test_positive_create_2(self, name):
        """@Test: Create a product with gpg_key

        @Feature: Products

        @Assert: Product is created with gpg_key

        """
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        key_name = orm.StringField(str_type=('alphanumeric',)).get_value()

        # Create an organization, GPG key and product.
        #
        # * GPG key points to organization
        # * Product points to organization and GPG key
        #
        org_attrs = entities.Organization().create()
        gpgkey_attrs = entities.GPGKey(
            name=key_name,
            content=key_content,
            organization=org_attrs['id']
        ).create()
        product_attrs = entities.Product(
            name=name,
            gpg_key=gpgkey_attrs['id'],
            organization=org_attrs['id']
        ).create()

        # GET the product and verify it's name and gpg_key id.
        response = entities.Product(id=product_attrs['id']).read_json()
        self.assertEqual(response['name'], name)
        self.assertEqual(response['gpg_key_id'], gpgkey_attrs['id'])

    @ddt.data(
        orm.StringField(str_type=('alpha',)).get_value(),
        orm.StringField(str_type=('alphanumeric',)).get_value(),
        orm.StringField(str_type=('numeric',)).get_value(),
    )
    def test_positive_update_1(self, name):
        """@Test: Create a product and update its name

        @Feature: Products

        @Assert: Product name has been updated

        """
        # Create a product and update its name.
        prod_id = entities.Product().create()['id']
        client.put(
            entities.Product(id=prod_id).path(),
            {u'name': name},
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()

        # Fetch the updated product and assert that name has been updated.
        prod_attrs = entities.Product(id=prod_id).read_json()
        self.assertEqual(prod_attrs['name'], name)
