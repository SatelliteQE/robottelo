"""
Test class for Products UI
"""

from robottelo.common.helpers import generate_name
from tests.ui.baseui import BaseUI


class Products(BaseUI):
    """
    Implements Product tests in UI
    """

    org_name = generate_name(8, 8)

    def test_create_prd(self):
        """
        @Feature: Content Product - Positive Create
        @Test: Create Content Product minimal input parameters
        @Assert: Product is created
        """
        prd_name = generate_name(8, 8)
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.handle_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(prd_name))

    def test_update_prd(self):
        """
        @Feature: Content Product - Positive Update
        @Test: Update Content Product with minimal input parameters
        @Assert: Product is updated
        """
        prd_name = generate_name(8, 8)
        new_prd_name = generate_name(8, 8)
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.handle_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(prd_name))
        self.products.update(prd_name, new_name=new_prd_name)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(new_prd_name))

    def test_remove_prd(self):
        """
        @Feature: Content Product - Positive Delete
        @Test: Delete Content Product
        @Assert: Product is deleted
        """
        prd_name = generate_name(8, 8)
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.handle_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(prd_name))
        self.products.delete(prd_name, True)
        self.assertIsNone(self.products.search(prd_name))
