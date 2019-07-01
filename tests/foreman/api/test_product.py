# -*- encoding: utf-8 -*-
"""Unit tests for the ``products`` paths.

An API reference for products can be found on your Satellite:
http://<sat6>/apidoc/v2/products.html

:Requirement: Product

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts-Content

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.constants import (
    FAKE_1_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
)
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import (
    skip_if_bug_open,
    tier1,
    tier2,
    upgrade
)
from robottelo.helpers import read_data_file
from robottelo.test import APITestCase


class ProductTestCase(APITestCase):
    """Tests for ``katello/api/v2/products``."""

    @classmethod
    def setUpClass(cls):
        """Set up organization for tests."""
        super(ProductTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create a product providing different valid names

        :id: 3d873b73-6919-4fda-84df-0e26bdf0c1dc

        :expectedresults: A product is created with expected name.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                product = entities.Product(
                    name=name, organization=self.org).create()
                self.assertEqual(name, product.name)

    @tier1
    def test_positive_create_with_label(self):
        """Create a product providing label which is different from its name

        :id: 95cf8e05-fd09-422e-bf6f-8b1dde762976

        :expectedresults: A product is created with expected label.

        :CaseImportance: Critical
        """
        label = gen_string('alphanumeric')
        product = entities.Product(label=label, organization=self.org).create()
        self.assertEqual(label, product.label)
        self.assertNotEqual(label, product.name)

    @tier1
    def test_positive_create_with_description(self):
        """Create a product providing different descriptions

        :id: f3e2df77-6711-440b-800a-9cebbbec36c5

        :expectedresults: A product is created with expected description.

        :CaseImportance: Critical
        """
        for desc in valid_data_list():
            with self.subTest(desc):
                product = entities.Product(
                    description=desc, organization=self.org).create()
                self.assertEqual(desc, product.description)

    @tier2
    def test_positive_create_with_gpg(self):
        """Create a product and provide a GPG key.

        :id: 57331c1f-15dd-4c9f-b8fc-3010847b2975

        :expectedresults: A product is created with the specified GPG key.

        :CaseLevel: Integration
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

    @tier1
    def test_negative_create_with_name(self):
        """Create a product providing invalid names only

        :id: 76531f53-09ff-4ee9-89b9-09a697526fb1

        :expectedresults: A product is not created

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Product(name=name).create()

    @tier1
    def test_negative_create_with_same_name(self):
        """Create a product providing a name of already existent entity

        :id: 039269c5-607a-4b70-91dd-b8fed8e50cc6

        :expectedresults: A product is not created

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        entities.Product(name=name, organization=self.org).create()
        with self.assertRaises(HTTPError):
            entities.Product(name=name, organization=self.org).create()

    @tier1
    def test_negative_create_with_label(self):
        """Create a product providing invalid label

        :id: 30b1a737-07f1-4786-b68a-734e57c33a62

        :expectedresults: A product is not created

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.Product(label=gen_string('utf8')).create()

    @tier1
    def test_positive_update_name(self):
        """Update product name to another valid name.

        :id: 1a9f6e0d-43fb-42e2-9dbd-e880f03b0297

        :expectedresults: Product name can be updated.

        :CaseImportance: Critical
        """
        product = entities.Product(organization=self.org).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                product.name = new_name
                product = product.update(['name'])
                self.assertEqual(new_name, product.name)

    @tier1
    def test_positive_update_description(self):
        """Update product description to another valid one.

        :id: c960c326-2e9f-4ee7-bdec-35a705305067

        :expectedresults: Product description can be updated.

        :CaseImportance: Critical
        """
        product = entities.Product(organization=self.org).create()
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                product.description = new_desc
                product = product.update(['description'])
                self.assertEqual(new_desc, product.description)

    @tier1
    def test_positive_update_name_to_original(self):
        """Rename Product back to original name

        :id: 3075f17f-4475-4b64-9fbd-1e41ced9142d

        :expectedresults: Product Renamed to original

        :CaseImportance: Critical
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

    @upgrade
    @tier2
    def test_positive_update_gpg(self):
        """Create a product and update its GPGKey

        :id: 3b08f155-a0d6-4987-b281-dc02e8d5a03e

        :expectedresults: The updated product points to a new GPG key.

        :CaseLevel: Integration
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

    @skip_if_bug_open('bugzilla', 1310422)
    @tier2
    def test_positive_update_organization(self):
        """Create a product and update its organization

        :id: b298957a-2cdb-4f17-a934-098612f3b659

        :expectedresults: The updated product points to a new organization

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.org).create()
        # Update the product and make it point to a new organization.
        new_org = entities.Organization().create()
        product.organization = new_org
        product = product.update()
        self.assertEqual(product.organization.id, new_org.id)

    @tier1
    def test_negative_update_name(self):
        """Attempt to update product name to invalid one

        :id: 3eb61fa8-3524-4872-8f1b-4e88004f66f5

        :expectedresults: Product is not updated

        :CaseImportance: Critical
        """
        product = entities.Product(organization=self.org).create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.Product(
                        id=product.id,
                        name=new_name,
                    ).update(['name'])

    @tier1
    def test_negative_update_label(self):
        """Attempt to update product label to another one.

        :id: 065cd673-8d10-46c7-800c-b731b06a5359

        :expectedresults: Product is not updated and error is raised

        :CaseImportance: Critical
        """
        product = entities.Product(organization=self.org).create()
        product.label = gen_string('alpha')
        with self.assertRaises(HTTPError):
            product.update(['label'])

    @tier1
    def test_positive_delete(self):
        """Create product and then delete it.

        :id: 30df95f5-0a4e-41ee-a99f-b418c5c5f2f3

        :expectedresults: Product is successfully deleted.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                product = entities.Product(name=name).create()
                product.delete()
                with self.assertRaises(HTTPError):
                    entities.Product(id=product.id).read()

    @tier1
    def test_positive_sync(self):
        """Sync product (repository within a product)

        :id: 860e00a1-c370-4bd0-8987-449338071d56

        :expectedresults: Repository within a product is successfully synced.

        :CaseImportance: Critical
        """
        product = entities.Product().create()
        rpm_repo = entities.Repository(
            product=product,
            content_type='yum',
            url=FAKE_1_YUM_REPO
        ).create()
        self.assertEqual(rpm_repo.read().content_counts['rpm'], 0)
        product.sync()
        self.assertGreaterEqual(rpm_repo.read().content_counts['rpm'], 1)

    @tier2
    @upgrade
    def test_positive_sync_several_repos(self):
        """Sync product (all repositories within a product)

        :id: 07918442-b72f-4db5-96b6-975564f3663a

        :expectedresults: All repositories within a product are successfully
            synced.

        :CaseLevel: Integration

        :BZ: 1389543
        """
        product = entities.Product().create()
        rpm_repo = entities.Repository(
            product=product,
            content_type='yum',
            url=FAKE_1_YUM_REPO
        ).create()
        puppet_repo = entities.Repository(
            product=product,
            content_type='puppet',
            url=FAKE_1_PUPPET_REPO
        ).create()
        self.assertEqual(rpm_repo.read().content_counts['rpm'], 0)
        self.assertEqual(puppet_repo.read().content_counts['puppet_module'], 0)
        product.sync()
        self.assertGreaterEqual(rpm_repo.read().content_counts['rpm'], 1)
        self.assertGreaterEqual(
            puppet_repo.read().content_counts['puppet_module'], 1)
