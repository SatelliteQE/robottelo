# -*- encoding: utf-8 -*-
"""Test class for Product CLI

:Requirement: Product

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_integer
from fauxfactory import gen_string
from fauxfactory import gen_url

from robottelo import ssh
from robottelo.api.utils import wait_for_tasks
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.defaults import Defaults
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_gpg_key
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.factory import make_sync_plan
from robottelo.cli.http_proxy import HttpProxy
from robottelo.cli.package import Package
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.constants import FAKE_0_YUM_REPO
from robottelo.constants import FAKE_0_YUM_REPO_PACKAGES_COUNT
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_labels_list
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.test import CLITestCase


class ProductTestCase(CLITestCase):
    """Product CLI tests."""

    org = None

    def setUp(self):
        """Tests for Lifecycle Environment via Hammer CLI"""

        super(ProductTestCase, self).setUp()

        if ProductTestCase.org is None:
            ProductTestCase.org = make_org(cached=True)

    @tier1
    @upgrade
    def test_positive_CRUD(self):
        """Check if product can be created, updated, synchronized and deleted

        :id: 9d7b5ec8-59d0-4371-b5d2-d43145e4e2db

        :expectedresults: Product is created, updated, synchronized and deleted

        :BZ: 1422552

        :CaseImportance: Critical
        """
        desc = valid_data_list()[0]
        gpg_key = make_gpg_key({'organization-id': self.org['id']})
        name = valid_data_list()[0]
        label = valid_labels_list()[0]
        sync_plan = make_sync_plan({'organization-id': self.org['id']})
        product = make_product(
            {
                'description': desc,
                'gpg-key-id': gpg_key['id'],
                'label': label,
                'name': name,
                'organization-id': self.org['id'],
                'sync-plan-id': sync_plan['id'],
            }
        )
        self.assertEqual(product['name'], name)
        self.assertGreater(len(product['label']), 0)
        self.assertEqual(product['label'], label)
        self.assertEqual(product['description'], desc)
        self.assertEqual(product['gpg']['gpg-key-id'], gpg_key['id'])
        self.assertEqual(product['sync-plan-id'], sync_plan['id'])

        # update
        desc = valid_data_list()[0]
        new_gpg_key = make_gpg_key({'organization-id': self.org['id']})
        new_sync_plan = make_sync_plan({'organization-id': self.org['id']})
        new_prod_name = gen_string('alpha', 8)
        Product.update(
            {
                'description': desc,
                'id': product['id'],
                'gpg-key-id': new_gpg_key['id'],
                'sync-plan-id': new_sync_plan['id'],
                'name': new_prod_name,
            }
        )
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertEqual(product['name'], new_prod_name)
        self.assertEqual(product['description'], desc)
        self.assertEqual(product['gpg']['gpg-key-id'], new_gpg_key['id'])
        self.assertNotEqual(product['gpg']['gpg-key-id'], gpg_key['id'])
        self.assertEqual(product['sync-plan-id'], new_sync_plan['id'])
        self.assertNotEqual(product['sync-plan-id'], sync_plan['id'])

        # synchronize
        repo = make_repository({'product-id': product['id'], 'url': FAKE_0_YUM_REPO})
        Product.synchronize({'id': product['id'], 'organization-id': self.org['id']})
        packages = Package.list({'product-id': product['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(int(repo['content-counts']['packages']), len(packages))
        self.assertEqual(len(packages), FAKE_0_YUM_REPO_PACKAGES_COUNT)

        # delete
        Product.remove_sync_plan({'id': product['id']})
        product = Product.info({'id': product['id'], 'organization-id': self.org['id']})
        self.assertEqual(len(product['sync-plan-id']), 0)
        Product.delete({'id': product['id']})
        wait_for_tasks(
            search_query='label = Actions::Katello::Product::Destroy'
            ' and resource_id = {}'.format(product['id']),
            max_tries=10,
        )
        with self.assertRaises(CLIReturnCodeError):
            Product.info({'id': product['id'], 'organization-id': self.org['id']})

    @tier2
    def test_negative_create_with_name(self):
        """Check that only valid names can be used

        :id: 2da26ab2-8d79-47ea-b4d2-defcd98a0649

        :expectedresults: Product is not created

        :CaseImportance: High
        """
        for invalid_name in invalid_values_list():
            with self.subTest(invalid_name):
                with self.assertRaises(CLIFactoryError):
                    make_product({'name': invalid_name, 'organization-id': self.org['id']})

    @tier2
    def test_negative_create_with_label(self):
        """Check that only valid labels can be used

        :id: 7cf970aa-48dc-425b-ae37-1e15dfab0626

        :expectedresults: Product is not created

        :CaseImportance: High
        """
        product_name = gen_alphanumeric()
        for invalid_label in (
            gen_string('latin1', 15),
            gen_string('utf8', 15),
            gen_string('html', 15),
        ):
            with self.subTest(invalid_label):
                with self.assertRaises(CLIFactoryError):
                    make_product(
                        {
                            'label': invalid_label,
                            'name': product_name,
                            'organization-id': self.org['id'],
                        }
                    )

    @run_in_one_thread
    @tier2
    def test_product_list_with_default_settings(self):
        """Listing product of an organization apart from default organization using hammer
         does not return output if a defaults settings are applied on org.

        :id: d5c5edac-b19c-4277-92fe-28d9b9fa43ef

        :BZ: 1745575

        :expectedresults: product/reporsitory list should work as expected.

        """
        default_product_name = gen_string('alpha')
        non_default_product_name = gen_string('alpha')
        default_org = self.org
        non_default_org = make_org()
        default_product = make_product(
            {'name': default_product_name, 'organization-id': default_org['id']}
        )
        non_default_product = make_product(
            {'name': non_default_product_name, 'organization-id': non_default_org['id']}
        )
        for product in (default_product, non_default_product):
            make_repository({'product-id': product['id'], 'url': FAKE_0_YUM_REPO})

        Defaults.add({'param-name': 'organization_id', 'param-value': default_org['id']})
        result = ssh.command('hammer defaults list')
        self.assertTrue(default_org['id'] in "".join(result.stdout))
        try:
            # Verify --organization-id is not required to pass if defaults are set
            result = ssh.command('hammer product list')
            self.assertTrue(default_product_name in "".join(result.stdout))
            result = ssh.command('hammer repository list')
            self.assertTrue(default_product_name in "".join(result.stdout))

            # verify that defaults setting should not affect other entities
            product_list = Product.list({'organization-id': non_default_org['id']})
            self.assertEquals(non_default_product_name, product_list[0]['name'])
            repository_list = Repository.list({'organization-id': non_default_org['id']})
            self.assertEquals(non_default_product_name, repository_list[0]['product'])

        finally:
            Defaults.delete({'param-name': 'organization_id'})
            result = ssh.command('hammer defaults list')
            self.assertTrue(default_org['id'] not in "".join(result.stdout))

    @tier2
    def test_positive_assign_http_proxy_to_products(self):
        """Assign http_proxy to Products and check whether http-proxy is
         used during sync.

        :id: 6af7b2b8-15d5-4d9f-9f87-e76b404a966f

        :expectedresults: HTTP Proxy is assigned to all repos present
            in Products and sync operation uses assigned http-proxy.

        :CaseImportance: Critical
        """
        # create HTTP proxies
        http_proxy_url_a = '{}:{}'.format(
            gen_url(scheme='https'), gen_integer(min_value=10, max_value=9999)
        )
        http_proxy_url_b = '{}:{}'.format(
            gen_url(scheme='http'), gen_integer(min_value=10, max_value=9999)
        )
        http_proxy_a = HttpProxy.create(
            {
                'name': gen_string('alpha', 15),
                'url': http_proxy_url_a,
                'organization-id': self.org['id'],
            }
        )
        http_proxy_b = HttpProxy.create(
            {
                'name': gen_string('alpha', 15),
                'url': http_proxy_url_b,
                'organization-id': self.org['id'],
            }
        )
        proxy_fqdn = http_proxy_b['url'].split(":")[1].strip("//")
        repo_fqdn = FAKE_0_YUM_REPO.split("/")[2]
        # Create products and repositories
        product_a = make_product({'organization-id': self.org['id']})
        product_b = make_product({'organization-id': self.org['id']})
        repo_a1 = make_repository(
            {'product-id': product_a['id'], 'url': FAKE_0_YUM_REPO, 'http-proxy-policy': 'none'}
        )
        repo_a2 = make_repository(
            {
                'product-id': product_a['id'],
                'url': FAKE_0_YUM_REPO,
                'http-proxy-policy': 'use_selected_http_proxy',
                'http-proxy-id': http_proxy_a['id'],
            }
        )
        repo_b1 = make_repository(
            {'product-id': product_b['id'], 'url': FAKE_0_YUM_REPO, 'http-proxy-policy': 'none'}
        )
        repo_b2 = make_repository({'product-id': product_b['id'], 'url': FAKE_0_YUM_REPO})
        # Add http_proxy to products
        Product.update_proxy(
            {
                'ids': '{},{}'.format(product_a['id'], product_b['id']),
                'http-proxy-policy': 'use_selected_http_proxy',
                'http-proxy-id': http_proxy_b['id'],
            }
        )
        repo_a1 = Repository.info({'id': repo_a1['id']})
        repo_a2 = Repository.info({'id': repo_a2['id']})
        repo_b1 = Repository.info({'id': repo_b1['id']})
        repo_b2 = Repository.info({'id': repo_b2['id']})
        assert repo_a1['http-proxy']['http-proxy-policy'] == "use_selected_http_proxy"
        assert repo_a2['http-proxy']['http-proxy-policy'] == "use_selected_http_proxy"
        assert repo_b1['http-proxy']['http-proxy-policy'] == "use_selected_http_proxy"
        assert repo_b2['http-proxy']['http-proxy-policy'] == "use_selected_http_proxy"
        assert repo_a1['http-proxy']['id'] == http_proxy_b['id']
        assert repo_a2['http-proxy']['id'] == http_proxy_b['id']
        assert repo_b1['http-proxy']['id'] == http_proxy_b['id']
        assert repo_b2['http-proxy']['id'] == http_proxy_b['id']
        # check if proxy fqdn is present in log during sync
        with self.assertRaises(CLIReturnCodeError):
            Product.synchronize({'id': product_a['id'], 'organization-id': self.org['id']})
        result = ssh.command(
            'grep -F "HTTP connection (1): {}" /var/log/messages'.format(proxy_fqdn)
        )
        assert result.return_code == 0
        # Add http_proxy to products
        Product.update_proxy(
            {'ids': '{},{}'.format(product_a['id'], product_b['id']), 'http-proxy-policy': 'none'}
        )
        repo_a1 = Repository.info({'id': repo_a1['id']})
        repo_a2 = Repository.info({'id': repo_a2['id']})
        repo_b1 = Repository.info({'id': repo_b1['id']})
        repo_b2 = Repository.info({'id': repo_b2['id']})
        assert repo_a1['http-proxy']['http-proxy-policy'] == "none"
        assert repo_a2['http-proxy']['http-proxy-policy'] == "none"
        assert repo_b1['http-proxy']['http-proxy-policy'] == "none"
        assert repo_b2['http-proxy']['http-proxy-policy'] == "none"
        # verify that proxy fqdn is not present in log during sync.
        Product.synchronize({'id': product_a['id'], 'organization-id': self.org['id']})
        result = ssh.command(
            'tail -n 50 /var/log/messages | grep -F "HTTP connection (1): {}"'.format(repo_fqdn)
        )
        assert result.return_code == 0
        result = ssh.command('tail -n 50 /var/log/messages | grep -F "{}"'.format(proxy_fqdn))
        assert result.return_code == 1
