# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for Products UI"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import run_only_on
from robottelo.test import UITestCase
from robottelo.ui.factory import make_product
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class Products(UITestCase):
    """Implements Product tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(Products, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.loc = entities.Location().create()

    @run_only_on('sat')
    def test_positive_create_basic(self):
        """@Test: Create Content Product minimal input parameters

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
    def test_positive_create_in_different_orgs(self):
        """@Test: Create Content Product with same name but in another org

        @Feature: Content Product - Positive Create

        @Assert: Product is created successfully in both the orgs.

        """
        for prd_name in generate_strings_list():
            with self.subTest(prd_name):
                # Note 1: the second org is created before logging in to
                # browser session otherwise this new org will not show up in
                # org dropdown
                # Note 2: Also note that the session is logged out and logged
                # back in for every iteration unlike other subTest()
                # implementations mainly for re-populating the org dropdown
                org2 = entities.Organization().create()
                with Session(self.browser) as session:
                    make_product(
                        session,
                        org=self.organization.name,
                        loc=self.loc.name,
                        name=prd_name,
                        description=gen_string('alphanumeric'),
                    )
                    self.assertIsNotNone(self.products.search(prd_name))
                    make_product(
                        session,
                        org=org2.name,
                        loc=self.loc.name,
                        name=prd_name,
                        description=gen_string('alphanumeric'),
                    )
                    self.assertIsNotNone(self.products.search(prd_name))

    @run_only_on('sat')
    def test_negative_create_with_invalid_name(self):
        """@Test: Create Content Product with invalid names

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
    def test_negative_create_with_same_name(self):
        """@Test: Create Content Product with same name input parameter

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
    def test_positive_update_basic(self):
        """@Test: Update Content Product with minimal input parameters

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
    def test_positive_update_to_original_name(self):
        """@Test: Rename Product back to original name.

        @Feature: Content Product - Positive Update

        @Assert: Product Renamed to original.

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
    def test_negative_update_with_too_long_name(self):
        """@Test: Update Content Product with too long input parameters

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
    def test_remove_prd(self):
        """@Test: Delete Content Product

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
                    # Note: refresh is used here because sometimes selenium
                    # is too fast to check the deleted object and it fails
                    self.browser.refresh()
                    self.assertIsNone(self.products.search(prd_name))
