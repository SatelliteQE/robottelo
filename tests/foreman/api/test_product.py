"""Unit tests for the ``products`` paths.

An API reference for products can be found on your Satellite:
http://<sat6>/apidoc/v2/products.html

:Requirement: Product

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import re

import pytest
from fauxfactory import gen_integer
from fauxfactory import gen_string
from fauxfactory import gen_url
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo import manifests
from robottelo import ssh
from robottelo.api.utils import upload_manifest
from robottelo.config import settings
from robottelo.constants import VALID_GPG_KEY_BETA_FILE
from robottelo.constants import VALID_GPG_KEY_FILE
from robottelo.constants.repos import FAKE_1_PUPPET_REPO
from robottelo.constants.repos import FAKE_1_YUM_REPO
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import skip_if
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.helpers import read_data_file
from robottelo.test import APITestCase


class ProductTestCase(APITestCase):
    """Tests for ``katello/api/v2/products``."""

    @classmethod
    def setUpClass(cls):
        """Set up organization for tests."""
        super().setUpClass()
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
                product = entities.Product(name=name, organization=self.org).create()
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
                product = entities.Product(description=desc, organization=self.org).create()
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
            content=read_data_file(VALID_GPG_KEY_FILE), organization=self.org
        ).create()
        product = entities.Product(gpg_key=gpg_key, organization=self.org).create()
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
        self.assertEqual(product.name, product.update(['name']).name)
        # Rename product to old name and verify
        product.name = old_name
        self.assertEqual(product.name, product.update(['name']).name)

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
            content=read_data_file(VALID_GPG_KEY_FILE), organization=self.org
        ).create()
        product = entities.Product(gpg_key=gpg_key_1, organization=self.org).create()

        # Update the product and make it point to a new GPG key.
        gpg_key_2 = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_BETA_FILE), organization=self.org
        ).create()
        product.gpg_key = gpg_key_2
        product = product.update()
        self.assertEqual(product.gpg_key.id, gpg_key_2.id)

    @pytest.mark.skip_if_open("BZ:1310422")
    @tier2
    def test_positive_update_organization(self):
        """Create a product and update its organization

        :id: b298957a-2cdb-4f17-a934-098612f3b659

        :expectedresults: The updated product points to a new organization

        :CaseLevel: Integration

        :BZ: 1310422
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
                    entities.Product(id=product.id, name=new_name).update(['name'])

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
    @skip_if(not settings.repos_hosting_url)
    def test_positive_sync(self):
        """Sync product (repository within a product)

        :id: 860e00a1-c370-4bd0-8987-449338071d56

        :expectedresults: Repository within a product is successfully synced.

        :CaseImportance: Critical
        """
        product = entities.Product().create()
        rpm_repo = entities.Repository(
            product=product, content_type='yum', url=FAKE_1_YUM_REPO
        ).create()
        self.assertEqual(rpm_repo.read().content_counts['rpm'], 0)
        product.sync()
        self.assertGreaterEqual(rpm_repo.read().content_counts['rpm'], 1)

    @tier2
    @upgrade
    @skip_if(not settings.repos_hosting_url)
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
            product=product, content_type='yum', url=FAKE_1_YUM_REPO
        ).create()
        puppet_repo = entities.Repository(
            product=product, content_type='puppet', url=FAKE_1_PUPPET_REPO
        ).create()
        self.assertEqual(rpm_repo.read().content_counts['rpm'], 0)
        self.assertEqual(puppet_repo.read().content_counts['puppet_module'], 0)
        product.sync()
        self.assertGreaterEqual(rpm_repo.read().content_counts['rpm'], 1)
        self.assertGreaterEqual(puppet_repo.read().content_counts['puppet_module'], 1)

    @tier2
    def test_positive_filter_product_list(self):
        """Filter products based on param 'custom/redhat_only'

        :id: e61fb63a-4552-4915-b13d-23ab80138249

        :expectedresults: Able to list the products based on defined filter.

        :CaseLevel: Integration

        :BZ: 1667129
        """
        product = entities.Product(organization=self.org.id).create()
        # Manifest upload to create RH Product
        with manifests.clone() as manifest:
            upload_manifest(self.org.id, manifest.content)

        custom_products = entities.Product(organization=self.org.id).search(query={'custom': True})
        rh_products = entities.Product(organization=self.org.id).search(
            query={'redhat_only': True, 'per_page': 1000}
        )

        assert len(custom_products) == 1
        assert product.name == custom_products[0].name
        assert 'Red Hat Beta' not in (prod.name for prod in custom_products)
        assert len(rh_products) > 1
        assert 'Red Hat Beta' in (prod.name for prod in rh_products)
        assert product.name not in (prod.name for prod in rh_products)

    @tier2
    def test_positive_assign_http_proxy_to_products(self):
        """Assign http_proxy to Products and check whether http-proxy is
         used during sync.

        :id: c9d23aa1-3325-4abd-a1a6-d5e75c12b08a

        :expectedresults: HTTP Proxy is assigned to all repos present
            in Products and sync operation uses assigned http-proxy.

        :CaseImportance: Critical
        """
        # create HTTP proxies
        http_proxy_url_a = '{}:{}'.format(
            gen_url(scheme='https'), gen_integer(min_value=10, max_value=9999)
        )
        http_proxy_a = entities.HTTPProxy(
            name=gen_string('alpha', 15), url=http_proxy_url_a, organization=[self.org.id]
        ).create()
        http_proxy_url_b = '{}:{}'.format(
            gen_url(scheme='https'), gen_integer(min_value=10, max_value=9999)
        )
        http_proxy_b = entities.HTTPProxy(
            name=gen_string('alpha', 15), url=http_proxy_url_b, organization=[self.org.id]
        ).create()
        proxy_fqdn = re.split(r'[:]', http_proxy_b.url)[1].strip("//")
        # Create products and repositories
        product_a = entities.Product(organization=self.org).create()
        product_b = entities.Product(organization=self.org).create()
        repo_a1 = entities.Repository(product=product_a, http_proxy_policy='none').create()
        repo_a2 = entities.Repository(
            product=product_a,
            http_proxy_policy='use_selected_http_proxy',
            http_proxy_id=http_proxy_a.id,
        ).create()
        repo_b1 = entities.Repository(product=product_b, http_proxy_policy='none').create()
        repo_b2 = entities.Repository(
            product=product_b, http_proxy_policy='global_default_http_proxy'
        ).create()
        # Add http_proxy to products
        entities.ProductBulkAction().http_proxy(
            data={
                "ids": [product_a.id, product_b.id],
                "http_proxy_policy": "use_selected_http_proxy",
                "http_proxy_id": http_proxy_b.id,
            }
        )
        assert repo_a1.read().http_proxy_policy == "use_selected_http_proxy"
        assert repo_a2.read().http_proxy_policy == "use_selected_http_proxy"
        assert repo_b1.read().http_proxy_policy == "use_selected_http_proxy"
        assert repo_b2.read().http_proxy_policy == "use_selected_http_proxy"
        assert repo_a1.read().http_proxy_id == http_proxy_b.id
        assert repo_a2.read().http_proxy_id == http_proxy_b.id
        assert repo_b1.read().http_proxy_id == http_proxy_b.id
        assert repo_b2.read().http_proxy_id == http_proxy_b.id
        # check if proxy fqdn is present in log during sync
        product_a.sync({'async': True})
        result = ssh.command(f'grep -F {proxy_fqdn} /var/log/messages')
        assert result.return_code == 0
