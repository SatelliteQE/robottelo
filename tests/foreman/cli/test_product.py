# -*- encoding: utf-8 -*-
"""Test class for Product CLI

:Requirement: Product

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Host-Content

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import time

from fauxfactory import gen_alphanumeric, gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_gpg_key,
    make_org,
    make_product,
    make_repository,
    make_sync_plan,
)
from robottelo.cli.package import Package
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.constants import FAKE_0_YUM_REPO, FAKE_0_YUM_REPO_PACKAGES_COUNT
from robottelo.datafactory import (
    generate_strings_list,
    valid_data_list,
    valid_labels_list,
    invalid_values_list,
)
from robottelo.decorators import (
    bz_bug_is_open,
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
    def test_positive_create_with_name(self):
        """Check if product can be created with random names

        :id: 252a2073-5094-4996-b157-bf7ff81f40af

        :expectedresults: Product is created and has random name

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                product = make_product({
                    u'name': name,
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(product['name'], name)
                self.assertGreater(len(product['label']), 0)

    @tier1
    def test_positive_create_with_label(self):
        """Check if product can be created with random labels

        :id: 07ff96b2-cc55-4d07-86a2-f20b77cc9b14

        :expectedresults: Product is created and has random label

        :CaseImportance: Critical
        """
        for label in valid_labels_list():
            with self.subTest(label):
                product_name = gen_alphanumeric()
                product = make_product({
                    u'label': label,
                    u'name': product_name,
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(product['name'], product_name)
                self.assertEqual(product['label'], label)

    @tier1
    def test_positive_create_with_description(self):
        """Check if product can be created with random description

        :id: 4b64dc60-ac08-4276-b31a-d3851ae064ba

        :expectedresults: Product is created and has random description

        :CaseImportance: Critical
        """
        for desc in valid_data_list():
            with self.subTest(desc):
                product_name = gen_alphanumeric()
                product = make_product({
                    u'description': desc,
                    u'name': product_name,
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(product['name'], product_name)
                self.assertEqual(product['description'], desc)

    @tier1
    def test_positive_create_with_gpg_key(self):
        """Check if product can be created with gpg key

        :id: 64f02b3b-f8c1-42c5-abb2-bf963ac24670

        :expectedresults: Product is created and has gpg key

        :CaseImportance: Critical
        """
        gpg_key = make_gpg_key({u'organization-id': self.org['id']})
        for name in valid_data_list():
            with self.subTest(name):
                product = make_product({
                    u'gpg-key-id': gpg_key['id'],
                    u'name': name,
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(product['name'], name)
                self.assertEqual(product['gpg']['gpg-key-id'], gpg_key['id'])

    @tier1
    def test_positive_create_with_sync_plan(self):
        """Check if product can be created with sync plan

        :id: c54ff608-9f59-4fd6-a45c-bd70ce656023

        :expectedresults: Product is created and has random sync plan

        :CaseImportance: Critical
        """
        sync_plan = make_sync_plan({
            u'organization-id': self.org['id']
        })
        for name in valid_data_list():
            with self.subTest(name):
                product = make_product({
                    u'name': name,
                    u'organization-id': self.org['id'],
                    u'sync-plan-id': sync_plan['id'],
                })
                self.assertEqual(product['name'], name)
                self.assertEqual(product['sync-plan-id'], sync_plan['id'])

    @tier1
    def test_negative_create_with_name(self):
        """Check that only valid names can be used

        :id: 2da26ab2-8d79-47ea-b4d2-defcd98a0649

        :expectedresults: Product is not created

        :CaseImportance: Critical
        """
        for invalid_name in invalid_values_list():
            with self.subTest(invalid_name):
                with self.assertRaises(CLIFactoryError):
                    make_product({
                        u'name': invalid_name,
                        u'organization-id': self.org['id'],
                    })

    @tier1
    def test_negative_create_with_label(self):
        """Check that only valid labels can be used

        :id: 7cf970aa-48dc-425b-ae37-1e15dfab0626

        :expectedresults: Product is not created

        :CaseImportance: Critical
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

    @tier1
    def test_positive_update_description(self):
        """Update the description of a product

        :id: 4b3b4c5b-3eaa-4b9c-93c6-6ee9d62061eb

        :expectedresults: Product description is updated

        :CaseImportance: Critical
        """
        product = make_product({u'organization-id': self.org['id']})
        for desc in valid_data_list():
            with self.subTest(desc):
                Product.update({
                    u'description': desc,
                    u'id': product['id'],
                })
                result = Product.info({
                    u'id': product['id'],
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(result['description'], desc)

    @tier1
    @upgrade
    def test_positive_update_gpg_key(self):
        """Update product's gpg keys

        :id: e7febd14-ac8b-424e-9ddf-bf0f63ebe430

        :expectedresults: Product gpg key is updated

        :CaseImportance: Critical
        """
        first_gpg_key = make_gpg_key({u'organization-id': self.org['id']})
        second_gpg_key = make_gpg_key({u'organization-id': self.org['id']})
        product = make_product({
            u'gpg-key-id': first_gpg_key['id'],
            u'organization-id': self.org['id'],
        })
        # Update the Descriptions
        Product.update({
            u'gpg-key-id': second_gpg_key['id'],
            u'id': product['id'],
        })
        # Fetch it
        product = Product.info({
            u'id': product['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(product['gpg']['gpg-key-id'], second_gpg_key['id'])
        self.assertNotEqual(product['gpg']['gpg-key-id'], first_gpg_key['id'])

    @tier1
    @upgrade
    def test_positive_update_sync_plan(self):
        """Update product's sync plan

        :id: 78cbde49-b6c8-41ab-8991-fcb4b648e79b

        :expectedresults: Product sync plan is updated

        :CaseImportance: Critical
        """
        first_sync_plan = make_sync_plan({u'organization-id': self.org['id']})
        second_sync_plan = make_sync_plan({u'organization-id': self.org['id']})
        product = make_product({
            u'organization-id': self.org['id'],
            u'sync-plan-id': first_sync_plan['id'],
        })
        # Update the Descriptions
        Product.update({
            u'id': product['id'],
            u'sync-plan-id': second_sync_plan['id'],
        })
        # Fetch it
        product = Product.info({
            u'id': product['id'],
            u'organization-id': self.org['id'],
        })
        self.assertEqual(product['sync-plan-id'], second_sync_plan['id'])
        self.assertNotEqual(product['sync-plan-id'], first_sync_plan['id'])

    @tier1
    def test_positive_update_name(self):
        """Rename Product back to original name

        :id: 4dec056b-8084-4372-bf7a-ce1db0c47cc9

        :expectedresults: Product Renamed to original

        :CaseImportance: Critical
        """
        for prod_name in generate_strings_list():
            with self.subTest(prod_name):
                prod = make_product({
                    u'name': prod_name,
                    u'organization-id': self.org['id'],
                })
                new_prod_name = gen_string('alpha', 8)
                # Update the product name
                Product.update({
                    u'id': prod['id'],
                    u'name': new_prod_name,
                })
                # Verify Updated
                prod = Product.info({
                    u'id': prod['id'],
                    u'organization-id': self.org['id'],
                })
                self.assertEqual(prod['name'], new_prod_name)
                # Now, Rename product to original
                Product.update({
                    u'id': prod['id'],
                    u'name': prod_name,
                })
                prod = Product.info({
                    u'id': prod['id'],
                    u'organization-id': self.org['id'],
                })
                # Verify renamed back to Original name.
                self.assertEqual(prod['name'], prod_name)

    @tier1
    def test_positive_delete_by_id(self):
        """Check if product can be deleted

        :id: 21bb8373-96d1-402c-973c-cf70d4b8244e

        :expectedresults: Product is deleted

        :CaseImportance: Critical
        """
        new_product = make_product({u'organization-id': self.org['id']})
        Product.delete({u'id': new_product['id']})
        with self.assertRaises(CLIReturnCodeError):
            Product.info({
                u'id': new_product['id'],
                u'organization-id': self.org['id'],
            })
            if bz_bug_is_open(1219490):
                for _ in range(5):
                    time.sleep(5)
                    Product.info({
                        u'id': new_product['id'],
                        u'organization-id': self.org['id'],
                    })

    @tier2
    def test_positive_add_sync_plan_by_id(self):
        """Check if a sync plan can be added to a product

        :id: 1517bc4b-5474-41c1-bc96-6e2130a2c2f4

        :expectedresults: Product has sync plan

        :CaseLevel: Integration
        """
        new_product = make_product({u'organization-id': self.org['id']})
        sync_plan = make_sync_plan({'organization-id': self.org['id']})
        Product.set_sync_plan({
            'id': new_product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        new_product = Product.info({
            'id': new_product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(new_product['sync-plan-id'], sync_plan['id'])

    @tier2
    @upgrade
    def test_positive_remove_sync_plan_by_id(self):
        """Check if a sync plan can be removed from a product

        :id: 0df2005c-158a-48cb-8a16-9a63923699fc

        :expectedresults: Product has sync plan

        :CaseLevel: Integration
        """
        product = make_product({u'organization-id': self.org['id']})
        sync_plan = make_sync_plan({'organization-id': self.org['id']})
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(product['sync-plan-id'], sync_plan['id'])
        Product.remove_sync_plan({'id': product['id']})
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(len(product['sync-plan-id']), 0)

    @tier2
    def test_positive_sync_by_id(self):
        """Check if product can be synchronized by its ID.

        :id: b0e436df-dd97-4fd2-a69f-3a2fb7a12c3c

        :expectedresults: Product is synchronized

        :CaseLevel: Integration
        """
        org = make_org()
        product = make_product({'organization-id': org['id']})
        make_repository({'product-id': product['id']})
        Product.synchronize({
            'id': product['id'],
            'organization-id': org['id'],
        })
        product = Product.info({
            'id': product['id'],
            'organization-id': org['id'],
        })
        self.assertEqual(u'Syncing Complete.', product['sync-state'])

    @tier2
    def test_positive_sync_by_name(self):
        """Check if product can be synchronized by its name.

        :id: 92058501-7786-4440-b612-6f7f79aa454e

        :expectedresults: Product is synchronized

        :CaseLevel: Integration
        """
        org = make_org()
        product = make_product({'organization-id': org['id']})
        make_repository({'product-id': product['id']})
        Product.synchronize({
            'name': product['name'],
            'organization': org['name'],
        })
        product = Product.info({
            'id': product['id'],
            'organization-id': org['id'],
        })
        self.assertEqual(u'Syncing Complete.', product['sync-state'])

    @tier2
    def test_positive_sync_by_label(self):
        """Check if product can be synchronized by its label.

        :id: 2e4e75dd-45f4-4013-ac74-7d4b38b0faec

        :expectedresults: Product is synchronized

        :CaseLevel: Integration
        """
        org = make_org()
        product = make_product({'organization-id': org['id']})
        make_repository({'product-id': product['id']})
        Product.synchronize({
            'id': product['id'],
            'organization-label': org['label'],
        })
        product = Product.info({
            'id': product['id'],
            'organization-id': org['id'],
        })
        self.assertEqual(u'Syncing Complete.', product['sync-state'])

    @tier2
    @upgrade
    def test_positive_package_count(self):
        """Check that packages count is correctly filtered by product id

        :id: 151f60a3-0b94-4658-8b0d-0d022f4f1d8f

        :expectedresults: Packages only from synced product returned

        :BZ: 1422552

        :CaseLevel: Integration
        """
        org = make_org()
        for _ in range(3):
            product = make_product({'organization-id': org['id']})
            repo = make_repository({
                'product-id': product['id'],
                'url': FAKE_0_YUM_REPO,
            })
            Product.synchronize({
                'id': product['id'],
                'organization-id': org['id'],
            })
            packages = Package.list({'product-id': product['id']})
            repo = Repository.info({'id': repo['id']})
            self.assertEqual(
                int(repo['content-counts']['packages']),
                len(packages)
            )
            self.assertEqual(len(packages), FAKE_0_YUM_REPO_PACKAGES_COUNT)
