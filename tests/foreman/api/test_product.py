# -*- encoding: utf-8 -*-
"""Unit tests for the ``products`` paths.

A full API reference for products can be found here:
http://theforeman.org/api/apidoc/v2/products.html

"""
from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from random import randint
from robottelo.common import manifests
from robottelo.common.constants import PRDS, REPOSET, VALID_GPG_KEY_FILE
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.helpers import read_data_file, generate_strings_list
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

    @data(*generate_strings_list())
    def test_positive_update_2(self, new_name):
        """@Test: Rename Product back to original name

        @Feature: Product

        @Assert: Product Renamed to original

        """
        old_name = self.product.name
        # Update new product name
        self.product.name = new_name
        self.assertEqual(self.product.name, self.product.update(['name']).name)
        # Rename product to old name and verify
        self.product.name = old_name
        self.assertEqual(self.product.name, self.product.update(['name']).name)


@run_only_on('sat')
class RepositorySetsTestCase(APITestCase):
    """Tests for ``katello/api/v2/products/<product_id>/repository_sets``."""

    def test_repositoryset_enable(self):
        """@Test: Enable repo from reposet

        @Feature: Repository-set

        @Assert: Repository was enabled

        """
        org = entities.Organization().create()
        org.upload_manifest(path=manifests.clone())
        prd_id = entities.Product().fetch_rhproduct_id(
            name=PRDS['rhel'],
            org_id=org.id,
        )
        product = entities.Product(id=prd_id)
        reposet_id = product.fetch_reposet_id(name=REPOSET['rhva6'])
        product.enable_rhrepo(
            base_arch='x86_64',
            release_ver='6Server',
            reposet_id=reposet_id,
        )
        repositories = product.repository_sets_available_repositories(
            reposet_id=reposet_id,
        )
        self.assertTrue([
            repo['enabled']
            for repo
            in repositories
            if (repo['substitutions']['basearch'] == 'x86_64' and
                repo['substitutions']['releasever'] == '6Server')
        ][0])

    @skip_if_bug_open('bugzilla', 1242017)
    def test_repositoryset_disable(self):
        """@Test: Disable repo from reposet

        @Feature: Repository-set

        @Assert: Repository was disabled

        """
        org = entities.Organization().create()
        org.upload_manifest(path=manifests.clone())
        prd_id = entities.Product().fetch_rhproduct_id(
            name=PRDS['rhel'],
            org_id=org.id,
        )
        product = entities.Product(id=prd_id)
        reposet_id = product.fetch_reposet_id(name=REPOSET['rhva6'])
        product.enable_rhrepo(
            base_arch='x86_64',
            release_ver='6Server',
            reposet_id=reposet_id,
        )
        product.disable_rhrepo(
            base_arch='x86_64',
            release_ver='6Server',
            reposet_id=reposet_id,
        )
        repositories = product.repository_sets_available_repositories(
            reposet_id=reposet_id,
        )
        self.assertFalse([
            repo['enabled']
            for repo
            in repositories
            if (repo['substitutions']['basearch'] == 'x86_64' and
                repo['substitutions']['releasever'] == '6Server')
        ][0])
