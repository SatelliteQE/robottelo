"""
Test class for Products UI
"""

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string, generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_org, make_loc, make_product
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class Products(UITestCase):
    """
    Implements Product tests in UI
    """

    org_name = None
    loc_name = None

    def setUp(self):
        super(Products, self).setUp()
        # Make sure to use the Class' org_name instance
        if Products.org_name and Products.loc_name is None:
            Products.org_name = generate_string("alpha", 8)
            Products.loc_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=Products.org_name)
                make_loc(session, name=Products.loc_name)

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list())
    def test_positive_create_0(self, prd_name):
        """
        @Test: Create Content Product minimal input parameters
        @Feature: Content Product - Positive Create
        @Assert: Product is created
        """

        description = "test 123"
        with Session(self.browser) as session:
            make_product(session, self.org_name, self.loc_name, name=prd_name,
                         description=description)
            self.assertIsNotNone(self.products.search(prd_name))

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list())
    def test_positive_create_1(self, prd_name):
        """
        @Test: Create Content Product with same name but in another org
        @Feature: Content Product - Positive Create
        @Assert: Product is created
        """

        description = "test 123"
        org2_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_product(session, org=self.org_name, loc=self.loc_name,
                         name=prd_name, description=description)
            self.assertIsNotNone(self.products.search(prd_name))
            make_product(session, org=org2_name, loc=self.loc_name,
                         name=prd_name, description=description)
            self.assertIsNotNone(self.products.search(prd_name))

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_negative_create_0(self, prd_name):
        """
        @Test: Create Content Product with too long input parameters
        @Feature: Content Product - Negative Create too long
        @Assert: Product is not created
        """

        locator = common_locators["common_haserror"]
        description = "test_negative_create_0"
        with Session(self.browser) as session:
            make_product(session, org=self.org_name, loc=self.loc_name,
                         name=prd_name, description=description)
            error = session.nav.wait_until_element(locator)
            self.assertIsNotNone(error)

    def test_negative_create_1(self):
        """
        @Test: Create Content Product without input parameter
        @Feature: Content Product - Negative Create zero length
        @Assert: Product is not created
        """

        locator = common_locators["common_invalid"]
        prd_name = ""
        description = "test_negative_create_1"
        with Session(self.browser) as session:
            make_product(session, org=self.org_name, loc=self.loc_name,
                         name=prd_name, description=description)
            invalid = self.products.wait_until_element(locator)
            self.assertIsNotNone(invalid)

    def test_negative_create_2(self):
        """
        @Test: Create Content Product with whitespace input parameter
        @Feature: Content Product - Negative Create with whitespace
        @Assert: Product is not created
        """

        locator = common_locators["common_invalid"]
        prd_name = "   "
        description = "test_negative_create_2"
        with Session(self.browser) as session:
            make_product(session, org=self.org_name, loc=self.loc_name,
                         name=prd_name, description=description)
            invalid = self.products.wait_until_element(locator)
            self.assertIsNotNone(invalid)

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list())
    def test_negative_create_3(self, prd_name):
        """
        @Test: Create Content Product with same name input parameter
        @Feature: Content Product - Negative Create with same name
        @Assert: Product is not created
        """

        locator = common_locators["common_haserror"]
        description = "test_negative_create_3"
        with Session(self.browser) as session:
            make_product(session, org=self.org_name, loc=self.loc_name,
                         name=prd_name, description=description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.products.create(prd_name, description)
        error = self.products.wait_until_element(locator)
        self.assertIsNotNone(error)

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_0(self, prd_name):
        """
        @Test: Update Content Product with minimal input parameters
        @Feature: Content Product - Positive Update
        @Assert: Product is updated
        """

        new_prd_name = generate_string("alpha", 8)
        description = "test 123"
        with Session(self.browser) as session:
            make_product(session, org=self.org_name, loc=self.loc_name,
                         name=prd_name, description=description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.products.update(prd_name, new_name=new_prd_name)
        self.assertIsNotNone(self.products.search(new_prd_name))

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list())
    def test_negative_update_0(self, prd_name):
        """
        @Test: Update Content Product with too long input parameters
        @Feature: Content Product - Negative Update
        @Assert: Product is not updated
        """

        locator = common_locators["common_haserror"]
        new_prd_name = generate_string("alpha", 256)
        description = "test_negative_update_0"
        with Session(self.browser) as session:
            make_product(session, org=self.org_name, loc=self.loc_name,
                         name=prd_name, description=description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.products.update(prd_name, new_name=new_prd_name)
        error = self.products.wait_until_element(locator)
        self.assertIsNotNone(error)

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list())
    def test_remove_prd(self, prd_name):
        """
        @Test: Delete Content Product
        @Feature: Content Product - Positive Delete
        @Assert: Product is deleted
        """

        description = "test 123"
        with Session(self.browser) as session:
            make_product(session, org=self.org_name, loc=self.loc_name,
                         name=prd_name, description=description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.products.delete(prd_name, True)
        self.assertIsNone(self.products.search(prd_name))
