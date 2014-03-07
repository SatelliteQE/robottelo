"""
Test class for Repository UI
"""

from robottelo.common.helpers import generate_name
from tests.ui.baseui import BaseUI


class Repos(BaseUI):
    """
    Implements Repos tests in UI
    """

    org_name = generate_name(8, 8)

    def test_create_repo(self):
        """
        @Feature: Content Repos - Positive Create
        @Test: Create Content Repos with minimal input parameters
        @Assert: Repos is created
        """

        prd_name = generate_name(8, 8)
        repo_name = generate_name(8, 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.handle_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))

    def test_remove_repo(self):
        """
        @Feature: Content Repos - Positive Delete
        @Test: Create Content Repos with minimal input parameters
        @Assert: Repos is Deleted
        """

        prd_name = generate_name(8, 8)
        repo_name = generate_name(8, 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.handle_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.repository.delete(repo_name)
        self.assertIsNone(self.repository.search(repo_name))
