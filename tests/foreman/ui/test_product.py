# -*- encoding: utf-8 -*-
"""Test class for Products UI"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import run_only_on, tier1, tier2
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

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create Content Product providing different names and minimal
        input parameters

        @Feature: Content Product - Positive Create

        @Assert: Product is created
        """
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier2
    def test_positive_create_in_different_orgs(self):
        """Create Content Product with same name but in another org

        @Feature: Content Product - Positive Create

        @Assert: Product is created successfully in both organizations.
        """
        organization_2 = entities.Organization().create()
        with Session(self.browser) as session:
            for prd_name in generate_strings_list():
                with self.subTest(prd_name):
                    for org in [self.organization.name, organization_2.name]:
                        make_product(
                            session,
                            org=org,
                            loc=self.loc.name,
                            name=prd_name,
                            description=gen_string('alphanumeric'),
                        )
                        self.assertIsNotNone(self.products.search(prd_name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Content Product with invalid names

        @Feature: Content Product - Negative Create zero length

        @Assert: Product is not created
        """
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Create Content Product with same name input parameter

        @Feature: Content Product - Negative Create with same name

        @Assert: Product is not created
        """
        prd_name = gen_string('alphanumeric')
        description = gen_string('alphanumeric')
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update Content Product name with minimal input parameters

        @Feature: Content Product - Positive Update

        @Assert: Product is updated
        """
        prd_name = gen_string('alpha')
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier2
    def test_positive_update_to_original_name(self):
        """Rename Product back to original name.

        @Feature: Content Product - Positive Update

        @Assert: Product renamed to previous value.
        """
        prd_name = gen_string('alphanumeric')
        new_prd_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier1
    def test_negative_update_with_too_long_name(self):
        """Update Content Product with too long input parameters

        @Feature: Content Product - Negative Update

        @Assert: Product is not updated
        """
        prd_name = gen_string('alpha')
        with Session(self.browser) as session:
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

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete Content Product

        @Feature: Content Product - Positive Delete

        @Assert: Product is deleted
        """
        with Session(self.browser) as session:
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
