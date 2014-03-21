"""
Test class for Products UI
"""

from ddt import data, ddt
from nose.plugins.attrib import attr
from robottelo.ui.navigator import Navigator
from robottelo.ui.org import Org
from robottelo.ui.login import Login
from robottelo.ui.locators import common_locators
from robottelo.common.helpers import generate_name, generate_strings_list
from tests.ui.baseui import BaseUI


@ddt
class Products(BaseUI):
    """
    Implements Product tests in UI
    """

    org_name = None

    def setUp(self):
        super(Products, self).setUp()
        # Make sure to use the Class' org_name instance
        if Products.org_name is None:
            Products.org_name = generate_name(8, 8)
            login = Login(self.browser)
            nav = Navigator(self.browser)
            org = Org(self.browser)
            login.login(self.katello_user, self.katello_passwd)
            nav.go_to_org()
            org.create(Products.org_name)
            login.logout()

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list())
    def test_positive_create_0(self, prd_name):
        """
        @Feature: Content Product - Positive Create
        @Test: Create Content Product minimal input parameters
        @Assert: Product is created
        """

        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_negative_create_0(self, prd_name):
        """
        @Feature: Content Product - Negative Create too long
        @Test: Create Content Product with too long input parameters
        @Assert: Product is not created
        """

        locator = common_locators["common_haserror"]
        description = "test_negative_create_0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(Products.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        error = self.products.wait_until_element(locator)
        self.assertTrue(error)

    def test_negative_create_1(self):
        """
        @Feature: Content Product - Negative Create zero length
        @Test: Create Content Product without input parameter
        @Assert: Product is not created
        """

        locator = common_locators["common_invalid"]
        prd_name = ""
        description = "test_negative_create_1"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(Products.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        invalid = self.products.wait_until_element(locator)
        self.assertTrue(invalid)

    def test_negative_create_2(self):
        """
        @Feature: Content Product - Negative Create with whitespace
        @Test: Create Content Product with whitespace input parameter
        @Assert: Product is not created
        """

        locator = common_locators["common_invalid"]
        prd_name = "   "
        description = "test_negative_create_2"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(Products.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        invalid = self.products.wait_until_element(locator)
        self.assertTrue(invalid)

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list())
    def test_negative_create_3(self, prd_name):
        """
        @Feature: Content Product - Negative Create with same name
        @Test: Create Content Product with same name input parameter
        @Assert: Product is not created
        """

        locator = common_locators["common_haserror"]
        description = "test_negative_create_3"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(Products.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.navigator.go_to_select_org(Products.org_name)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(prd_name))
        self.products.create(prd_name, description)
        error = self.products.wait_until_element(locator)
        self.assertTrue(error)

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_0(self, prd_name):
        """
        @Feature: Content Product - Positive Update
        @Test: Update Content Product with minimal input parameters
        @Assert: Product is updated
        """

        new_prd_name = generate_name(8, 8)
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.products.update(prd_name, new_name=new_prd_name)
        self.assertIsNotNone(self.products.search(new_prd_name))

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list())
    def test_negative_update_0(self, prd_name):
        """
        @Feature: Content Product - Negative Update
        @Test: Update Content Product with too long input parameters
        @Assert: Product is not updated
        """

        locator = common_locators["common_haserror"]
        new_prd_name = generate_name(256)
        description = "test_negative_update_0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(Products.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.navigator.go_to_select_org(Products.org_name)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(prd_name))
        self.products.update(prd_name, new_name=new_prd_name)
        error = self.products.wait_until_element(locator)
        self.assertTrue(error)

    @attr('ui', 'prd', 'implemented')
    @data(*generate_strings_list())
    def test_remove_prd(self, prd_name):
        """
        @Feature: Content Product - Positive Delete
        @Test: Delete Content Product
        @Assert: Product is deleted
        """

        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.products.delete(prd_name, True)
        self.assertIsNone(self.products.search(prd_name))
