"""Test class for Products UI"""

from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from robottelo.decorators import data, run_only_on, skip_if_bug_open
from robottelo.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_product
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class Products(UITestCase):
    """Implements Product tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        cls.organization = entities.Organization().create()
        cls.loc = entities.Location().create()

        super(Products, cls).setUpClass()

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_positive_create_basic(self, prd_name):
        """@Test: Create Content Product minimal input parameters

        @Feature: Content Product - Positive Create

        @Assert: Product is created

        """
        with Session(self.browser) as session:
            make_product(
                session,
                org=self.organization.name,
                loc=self.loc.name,
                name=prd_name,
                description=gen_string('alphanumeric'),
            )
            self.assertIsNotNone(self.products.search(prd_name))

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_positive_create_in_different_orgs(self, prd_name):
        """@Test: Create Content Product with same name but in another org

        @Feature: Content Product - Positive Create

        @Assert: Product is created successfully in both the orgs.

        """
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
                force_context=True,
            )
            self.assertIsNotNone(self.products.search(prd_name))

    @run_only_on('sat')
    @data(*generate_strings_list(len1=256))
    def test_negative_create_too_long_name(self, prd_name):
        """@Test: Create Content Product with too long input parameters

        @Feature: Content Product - Negative Create too long

        @Assert: Product is not created

        """
        with Session(self.browser) as session:
            make_product(
                session,
                org=self.organization.name,
                loc=self.loc.name,
                name=prd_name,
                description=gen_string('alphanumeric'),
            )
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators['common_haserror']))

    @run_only_on('sat')
    @data('', '  ')
    def test_negative_create_with_blank_name(self, name):
        """@Test: Create Content Product without input parameter

        @Feature: Content Product - Negative Create zero length

        @Assert: Product is not created

        """
        with Session(self.browser) as session:
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
    @data(*generate_strings_list())
    def test_negative_create_with_same_name(self, prd_name):
        """@Test: Create Content Product with same name input parameter

        @Feature: Content Product - Negative Create with same name

        @Assert: Product is not created

        """
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
    @data(*generate_strings_list())
    def test_positive_update_basic(self, new_prd_name):
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
            self.products.update(prd_name, new_name=new_prd_name)
            self.assertIsNotNone(self.products.search(new_prd_name))

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_positive_update_to_original_name(self, prd_name):
        """@Test: Rename Product back to original name.

        @Feature: Content Product - Positive Update

        @Assert: Product Renamed to original.

        """
        new_prd_name = gen_string('alpha')
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

    @skip_if_bug_open('redmine', 7845)
    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_remove_prd(self, prd_name):
        """@Test: Delete Content Product

        @Feature: Content Product - Positive Delete

        @Assert: Product is deleted

        """
        with Session(self.browser) as session:
            make_product(
                session,
                org=self.organization.name,
                loc=self.loc.name,
                name=prd_name,
                description=gen_string('alphanumeric'),
            )
            self.assertIsNotNone(self.products.search(prd_name))
            self.products.delete(prd_name)
            self.assertIsNone(self.products.search(prd_name))
