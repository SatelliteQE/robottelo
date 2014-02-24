"""
Test class for Custom Sync UI
"""

from robottelo.common.helpers import generate_name
from robottelo.common.constants import DEFAULT_ORG, FAKE_URL
from tests.ui.baseui import BaseUI


class Sync(BaseUI):
    """
    Implements Custom Sync tests in UI
    """

    def test_sync_repos(self):
        """
        @Feature: Content Custom Sync - Positive Create
        @Test: Create Content Custom Sync with minimal input parameters
        @Assert: Whether Sync is successful
        """
        prd_name = generate_name(8, 8)
        repo_name = generate_name(8, 8)
        repo_url = FAKE_URL['zoo']
        description = "test 123"
        provider = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_products()
        self.products.create(prd_name, description, provider,
                             create_provider=True)
        self.navigator.go_to_select_org(DEFAULT_ORG)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_sync_status()
        self.sync.sync_custom_repos(prd_name, [repo_name])
        self.assertIsNotNone(self.sync.assert_sync(prd_name, [repo_name]))
