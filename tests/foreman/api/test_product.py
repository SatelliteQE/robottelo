# -*- encoding: utf-8 -*-
"""Unit tests for the ``products`` paths.

A full API reference for products can be found here:
http://theforeman.org/api/apidoc/v2/products.html

"""
from fauxfactory import gen_string
from nailgun import entities
from random import randint
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import PRDS, REPOSET, VALID_GPG_KEY_FILE
from robottelo.decorators import run_only_on
from robottelo.helpers import read_data_file, generate_strings_list
from robottelo.test import APITestCase


def valid_name_desc_list():
    """Returns a tuple with random data for name/description"""
    return(
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


class ProductsTestCase(APITestCase):
    """Tests for ``katello/api/v2/products``."""

    @run_only_on('sat')
    def test_positive_create_1(self):
        """@Test: Create a product and provide a name or description.

        @Assert: A product is created with the provided attributes.

        @Feature: Product

        """
        for attr in valid_name_desc_list():
            with self.subTest(attr):
                product = entities.Product(**attr).create()
                for name, value in attr.items():
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
class ProductUpdateTestCase(APITestCase):
    """Tests for updating a product."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create a product."""
        super(ProductUpdateTestCase, cls).setUpClass()
        cls.product = entities.Product().create()

    def test_positive_update_1(self):
        """@Test: Update a product with a new name or description.

        @Assert: The given attributes are used.

        @Feature: Product

        """
        for attrs in valid_name_desc_list():
            with self.subTest(attrs):
                setattr(self.product, attrs.keys()[0], attrs.values()[0])
                self.product = self.product.update()
                self.assertEqual(
                    getattr(self.product, attrs.keys()[0]),
                    attrs.values()[0]
                )

    def test_positive_update_2(self):
        """@Test: Rename Product back to original name

        @Feature: Product

        @Assert: Product Renamed to original

        """
        for new_name in generate_strings_list():
            with self.subTest(new_name):
                old_name = self.product.name
                # Update new product name
                self.product.name = new_name
                self.assertEqual(
                    self.product.name,
                    self.product.update(['name']).name
                )
                # Rename product to old name and verify
                self.product.name = old_name
                self.assertEqual(
                    self.product.name,
                    self.product.update(['name']).name
                )


@run_only_on('sat')
class RepositorySetsTestCase(APITestCase):
    """Tests for ``katello/api/v2/products/<product_id>/repository_sets``."""

    def test_repositoryset_enable(self):
        """@Test: Enable repo from reposet

        @Feature: Repository-set

        @Assert: Repository was enabled

        """
        org = entities.Organization().create()
        with open(manifests.clone(), 'rb') as manifest:
            upload_manifest(org.id, manifest)
        product = entities.Product(
            name=PRDS['rhel'],
            organization=org,
        ).search()[0]
        reposet = entities.RepositorySet(
            name=REPOSET['rhva6'],
            product=product,
        ).search()[0]
        reposet.enable(data={'basearch': 'x86_64', 'releasever': '6Server'})
        repositories = reposet.available_repositories()['results']
        self.assertTrue([
            repo['enabled']
            for repo
            in repositories
            if (repo['substitutions']['basearch'] == 'x86_64' and
                repo['substitutions']['releasever'] == '6Server')
        ][0])

    def test_repositoryset_disable(self):
        """@Test: Disable repo from reposet

        @Feature: Repository-set

        @Assert: Repository was disabled

        """
        org = entities.Organization().create()
        with open(manifests.clone(), 'rb') as manifest:
            upload_manifest(org.id, manifest)
        product = entities.Product(
            name=PRDS['rhel'],
            organization=org,
        ).search()[0]
        reposet = entities.RepositorySet(
            name=REPOSET['rhva6'],
            product=product,
        ).search()[0]
        reposet.enable(data={'basearch': 'x86_64', 'releasever': '6Server'})
        reposet.disable(data={'basearch': 'x86_64', 'releasever': '6Server'})
        repositories = reposet.available_repositories()['results']
        self.assertFalse([
            repo['enabled']
            for repo
            in repositories
            if (repo['substitutions']['basearch'] == 'x86_64' and
                repo['substitutions']['releasever'] == '6Server')
        ][0])
