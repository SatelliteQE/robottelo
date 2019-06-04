# -*- encoding: utf-8 -*-
"""Test class for Products UI

:Requirement: Product

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.factory import make_product
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class ProductTestCase(UITestCase):
    """Implements Product tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(ProductTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.loc = entities.Location().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create Content Product providing different names and minimal
        input parameters

        :id: b73d9440-1f30-4fc5-ad7c-e1febe879cbc

        :expectedresults: Product is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for prd_name in generate_strings_list():
                with self.subTest(prd_name):
                    make_product(
                        session,
                        org=self.organization.name,
                        loc=self.loc.name,
                        name=prd_name,
                        description=gen_string('alphanumeric'),
                    )
                    self.assertIsNotNone(self.products.search(prd_name))

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Content Product with invalid names

        :id: 11efd16c-6471-4191-934f-79c7278c66e8

        :expectedresults: Product is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_product(
                        session,
                        org=self.organization.name,
                        loc=self.loc.name,
                        name=name,
                        description=gen_string('alphanumeric'),
                    )
                    self.assertIsNotNone(self.products.wait_until_element(
                        common_locators['common_invalid']))

    @tier1
    def test_negative_create_with_same_name(self):
        """Create Content Product with same name input parameter

        :id: 90ceee6e-0ccc-4065-87ba-42d36484f032

        :expectedresults: Product is not created

        :CaseImportance: Critical
        """
        prd_name = gen_string('alphanumeric')
        description = gen_string('alphanumeric')
        with Session(self) as session:
            make_product(
                session,
                org=self.organization.name,
                loc=self.loc.name,
                name=prd_name,
                description=description,
            )
            self.assertIsNotNone(self.products.search(prd_name))
            self.products.create(prd_name, description)
            self.assertIsNotNone(self.products.wait_until_element(
                common_locators['common_haserror']))

    @tier1
    def test_positive_update_name(self):
        """Update Content Product name with minimal input parameters

        :id: 2c0539b4-84e1-46c6-aaca-12fe3865da3d

        :expectedresults: Product is updated

        :CaseImportance: Critical
        """
        prd_name = gen_string('alpha')
        with Session(self) as session:
            make_product(
                session,
                org=self.organization.name,
                loc=self.loc.name,
                name=prd_name,
                description=gen_string('alphanumeric'),
            )
            self.assertIsNotNone(self.products.search(prd_name))
            for new_prd_name in generate_strings_list():
                with self.subTest(new_prd_name):
                    self.products.update(prd_name, new_name=new_prd_name)
                    self.assertIsNotNone(self.products.search(new_prd_name))
                    prd_name = new_prd_name  # for next iteration

    @tier1
    def test_positive_update_to_original_name(self):
        """Rename Product back to original name.

        :id: 6632effe-06ba-4690-b81d-4f5eae20b7b9

        :expectedresults: Product renamed to previous value.

        :CaseLevel: Integration
        """
        prd_name = gen_string('alphanumeric')
        new_prd_name = gen_string('alphanumeric')
        with Session(self) as session:
            make_product(
                session,
                org=self.organization.name,
                loc=self.loc.name,
                name=prd_name,
            )
            self.assertIsNotNone(self.products.search(prd_name))
            self.products.update(prd_name, new_name=new_prd_name)
            self.assertIsNotNone(self.products.search(new_prd_name))
            # Rename Product to original and verify
            self.products.update(new_prd_name, new_name=prd_name)
            self.assertIsNotNone(self.products.search(prd_name))

    @tier1
    def test_negative_update_with_too_long_name(self):
        """Update Content Product with too long input parameters

        :id: c6938675-4a2a-4bec-9315-b1c951b628bb

        :expectedresults: Product is not updated

        :CaseImportance: Critical
        """
        prd_name = gen_string('alpha')
        with Session(self) as session:
            make_product(
                session,
                org=self.organization.name,
                loc=self.loc.name,
                name=prd_name,
                description=gen_string('alphanumeric'),
            )
            self.assertIsNotNone(self.products.search(prd_name))
            self.products.update(prd_name, new_name=gen_string('alpha', 256))
            self.assertIsNotNone(self.products.wait_until_element(
                common_locators['alert.error']))

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete Content Product

        :id: cf80bafb-8581-483a-b5c1-3a162642c6c1

        :expectedresults: Product is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for prd_name in generate_strings_list():
                with self.subTest(prd_name):
                    make_product(
                        session,
                        org=self.organization.name,
                        loc=self.loc.name,
                        name=prd_name,
                        description=gen_string('alphanumeric'),
                    )
                    self.assertIsNotNone(self.products.search(prd_name))
                    self.products.delete(prd_name)
