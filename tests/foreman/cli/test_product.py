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

from fauxfactory import gen_alphanumeric, gen_string
from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.defaults import Defaults
from robottelo.cli.factory import (
    CLIFactoryError,
    make_gpg_key,
    make_org,
    make_product,
    make_repository,
    make_sync_plan,
)
from robottelo.api.utils import wait_for_tasks
from robottelo.cli.package import Package
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.constants import FAKE_0_YUM_REPO, FAKE_0_YUM_REPO_PACKAGES_COUNT
from robottelo.datafactory import (
    valid_data_list,
    valid_labels_list,
    invalid_values_list,
)
from robottelo.decorators import (
    tier1,
    tier2,
    upgrade
)
from robottelo.test import CLITestCase


class ProductTestCase(CLITestCase):
    """Product CLI tests."""

    org = None

    # pylint: disable=unexpected-keyword-arg
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
        gpg_key = make_gpg_key({u'organization-id': self.org['id']})
        name = valid_data_list()[0]
        label = valid_labels_list()[0]
        sync_plan = make_sync_plan({
            u'organization-id': self.org['id']
        })
        product = make_product({
            u'description': desc,
            u'gpg-key-id': gpg_key['id'],
            u'label': label,
            u'name': name,
            u'organization-id': self.org['id'],
            u'sync-plan-id': sync_plan['id'],
        })
        self.assertEqual(product['name'], name)
        self.assertGreater(len(product['label']), 0)
        self.assertEqual(product['label'], label)
        self.assertEqual(product['description'], desc)
        self.assertEqual(product['gpg']['gpg-key-id'], gpg_key['id'])
        self.assertEqual(product['sync-plan-id'], sync_plan['id'])

        # update
        desc = valid_data_list()[0]
        new_gpg_key = make_gpg_key({u'organization-id': self.org['id']})
        new_sync_plan = make_sync_plan({u'organization-id': self.org['id']})
        new_prod_name = gen_string('alpha', 8)
        Product.update({
            u'description': desc,
            u'id': product['id'],
            u'gpg-key-id': new_gpg_key['id'],
            u'sync-plan-id': new_sync_plan['id'],
            u'name': new_prod_name,
        })
        product = Product.info({
            u'id': product['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(product['name'], new_prod_name)
        self.assertEqual(product['description'], desc)
        self.assertEqual(product['gpg']['gpg-key-id'], new_gpg_key['id'])
        self.assertNotEqual(product['gpg']['gpg-key-id'], gpg_key['id'])
        self.assertEqual(product['sync-plan-id'], new_sync_plan['id'])
        self.assertNotEqual(product['sync-plan-id'], sync_plan['id'])

        # synchronize
        repo = make_repository({
            'product-id': product['id'],
            'url': FAKE_0_YUM_REPO,
        })
        Product.synchronize({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        packages = Package.list({'product-id': product['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(
            int(repo['content-counts']['packages']),
            len(packages)
        )
        self.assertEqual(len(packages), FAKE_0_YUM_REPO_PACKAGES_COUNT)

        # delete
        Product.remove_sync_plan({'id': product['id']})
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(len(product['sync-plan-id']), 0)
        Product.delete({u'id': product['id']})
        wait_for_tasks(
            search_query='label = Actions::Katello::Product::Destroy'
                         ' and resource_id = {}'.format(product['id']),
            max_tries=10,
        )
        with self.assertRaises(CLIReturnCodeError):
            Product.info({
                u'id': product['id'],
                u'organization-id': self.org['id'],
            })

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
                    make_product({
                        u'name': invalid_name,
                        u'organization-id': self.org['id'],
                    })

    @tier2
    def test_negative_create_with_label(self):
        """Check that only valid labels can be used

        :id: 7cf970aa-48dc-425b-ae37-1e15dfab0626

        :expectedresults: Product is not created

        :CaseImportance: High
        """
        product_name = gen_alphanumeric()
        for invalid_label in (gen_string('latin1', 15), gen_string('utf8', 15),
                              gen_string('html', 15)):
            with self.subTest(invalid_label):
                with self.assertRaises(CLIFactoryError):
                    make_product({
                        u'label': invalid_label,
                        u'name': product_name,
                        u'organization-id': self.org['id'],
                    })

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
        default_product = make_product({
            u'name': default_product_name,
            u'organization-id': default_org['id'],
        })
        non_default_product = make_product({
            u'name': non_default_product_name,
            u'organization-id': non_default_org['id'],
        })
        for product in (default_product, non_default_product):
            make_repository({
                'product-id': product['id'],
                'url': FAKE_0_YUM_REPO,
            })

        Defaults.add({
            u'param-name': 'organization_id',
            u'param-value': default_org['id'],
        })
        result = ssh.command('hammer defaults list')
        self.assertTrue(default_org['id'] in "".join(result.stdout))
        try:
            # Verify --organization-id is not required to pass if defaults are set
            result = ssh.command('hammer product list')
            self.assertTrue(default_product_name in "".join(result.stdout))
            result = ssh.command('hammer repository list')
            self.assertTrue(default_product_name in "".join(result.stdout))

            # verify that defaults setting should not affect other entities
            product_list = Product.list({u'organization-id': non_default_org['id']})
            self.assertEquals(non_default_product_name, product_list[0]['name'])
            repository_list = Repository.list({u'organization-id': non_default_org['id']})
            self.assertEquals(non_default_product_name, repository_list[0]['product'])

        finally:
            Defaults.delete({u'param-name': 'organization_id'})
            result = ssh.command('hammer defaults list')
            self.assertTrue(default_org['id'] not in "".join(result.stdout))
