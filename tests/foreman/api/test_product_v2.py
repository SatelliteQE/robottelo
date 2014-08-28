"""Unit tests for the ``products`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/products.html

"""
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.constants import VALID_GPG_KEY_FILE
from robottelo.common.helpers import get_server_credentials, read_data_file
from robottelo import entities, orm
from unittest import TestCase
import ddt
import httplib


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
        # Create an organization and product
        org_attrs = entities.Organization().create()
        product_attrs = entities.Product(
            name=name,
            organization=org_attrs['id']
        ).create()

        path = entities.Product(id=product_attrs['id']).path()

        # GET the product and verify it's name.
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        self.assertEqual(response['name'], name)

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
        # Create an organization gpg_key
        org_attrs = entities.Organization().create()
        gpgkey_attrs = entities.GPGKey(
            name=key_name,
            content=key_content,
            organization=org_attrs['id']
        ).create()

        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=name,
            gpg_key=gpgkey_attrs['id'],
            organization=org_attrs['id']
        ).create()

        path = entities.Product(id=product_attrs['id']).path()

        # GET the product and verify it's name and gpg_key id.
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        self.assertEqual(response['name'], name)
        self.assertEqual(response['gpg_key_id'], gpgkey_attrs['id'])

    @ddt.data(
        orm.StringField(str_type=('alphanumeric',)).get_value(),
        orm.StringField(str_type=('alpha',)).get_value(),
        orm.StringField(str_type=('numeric',)).get_value(),
    )
    def test_positive_delete_1(self, name):
        """@Test: Create a Product and delete it

        @Feature: Products

        @Assert: Product is deleted and HTTP 404 is returned

        """
        # Create an organization and product
        org_attrs = entities.Organization().create()
        product_attrs = entities.Product(
            name=name,
            organization=org_attrs['id']
        ).create()

        path = entities.Product(id=product_attrs['id']).path()

        # GET the product and verify it's name.
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        self.assertEqual(response['name'], name)

        # Delete the product, GET it, and assert that an HTTP 404 is returned.
        entities.Product(id=product_attrs['id']).delete()
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.NOT_FOUND
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )

    @ddt.data(
        {u'name': orm.StringField(str_type=('alphanumeric',)).get_value(),
         u'new_name': orm.StringField(str_type=('alphanumeric',)).get_value()},
        {u'name': orm.StringField(str_type=('numeric',)).get_value(),
         u'new_name': orm.StringField(str_type=('numeric',)).get_value()},
        {u'name': orm.StringField(str_type=('alpha',)).get_value(),
         u'new_name': orm.StringField(str_type=('alpha',)).get_value()}
    )
    def test_positive_update_1(self, test_data):
        """@Test: Create a product and update its name

        @Feature: Products

        @Assert: Product name should be updated

        """
        # Create an organization and product
        org_attrs = entities.Organization().create()
        product_attrs = entities.Product(
            name=test_data['name'],
            organization=org_attrs['id']
        ).create()

        path = entities.Product(id=product_attrs['id']).path()

        product_copy = product_attrs.copy()
        product_copy['name'] = test_data['new_name']

        response = client.put(
            path,
            product_copy,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            response.status_code,
            status_code,
            status_code_error(path, status_code, response),
        )
        # Fetch the updated product
        updated_attrs = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        # Assert that name is updated
        self.assertNotEqual(
            updated_attrs['name'],
            product_attrs['name'],
        )
