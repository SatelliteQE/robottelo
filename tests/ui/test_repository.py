"""
Test class for Repository UI
"""

from robottelo.common.helpers import generate_name
from tests.ui.commonui import CommonUI


class Repos(CommonUI):
    """
    Implements Repos tests in UI
    """

    def test_create_repo(self):
        """
        @Feature: Content Repos - Positive Create
        @Test: Create Content Repos with minimal input parameters
        @Assert: Repos is created
        """
        org_name = generate_name(8, 8)
        prd_name = generate_name(8, 8)
        repo_name = generate_name(8, 8)
        repo_url = "https://fake/url"
        description = "test 123"
        provider = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.create_product(prd_name, description, provider,
                            create_provider=True, org=org_name)
        self.create_repo(repo_name, prd_name, repo_url)

    def test_remove_repo(self):
        """
        @Feature: Content Repos - Positive Delete
        @Test: Create Content Repos with minimal input parameters
        @Assert: Repos is Deleted
        """
        org_name = generate_name(8, 8)
        prd_name = generate_name(8, 8)
        repo_name = generate_name(8, 8)
        repo_url = "https://fake/url"
        description = "test 123"
        provider = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.create_product(prd_name, description, provider,
                            create_provider=True, org=org_name)
        self.create_repo(repo_name, prd_name, repo_url)
        self.repository.delete(repo_name)
        self.assertIsNone(self.repository.search(repo_name))
