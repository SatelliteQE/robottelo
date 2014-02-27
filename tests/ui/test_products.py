"""
Test class for Products UI
"""

from robottelo.common.helpers import generate_name
from tests.ui.commonui import CommonUI


class Products(CommonUI):
    """
    Implements Product tests in UI
    """

    def test_create_prd(self):
        """
        @Feature: Content Product - Positive Create
        @Test: Create Content Product minimal input parameters
        @Assert: Product is created
        """
        org_name = generate_name(8, 8)
        prd_name = generate_name(8, 8)
        description = "test 123"
        provider = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.create_product(prd_name, description, provider,
                            create_provider=True, org=org_name)

    def test_update_prd(self):
        """
        @Feature: Content Product - Positive Update
        @Test: Update Content Product with minimal input parameters
        @Assert: Product is updated
        """
        org_name = generate_name(8, 8)
        prd_name = generate_name(8, 8)
        new_prd_name = generate_name(8, 8)
        description = "test 123"
        provider = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.create_product(prd_name, description, provider,
                            create_provider=True, org=org_name)
        self.products.update(prd_name, new_name=new_prd_name)
        self.navigator.go_to_select_org(org_name)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(new_prd_name))

    def test_remove_prd(self):
        """
        @Feature: Content Product - Positive Delete
        @Test: Delete Content Product
        @Assert: Product is deleted
        """
        org_name = generate_name(8, 8)
        prd_name = generate_name(8, 8)
        description = "test 123"
        provider = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.create_product(prd_name, description, provider,
                            create_provider=True, org=org_name)
        self.products.delete(prd_name, True)
        self.assertIsNone(self.products.search(prd_name))
