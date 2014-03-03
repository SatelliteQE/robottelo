"""
Test class for Template UI
"""


from robottelo.common.helpers import generate_name, generate_email_address
from tests.ui.baseui import BaseUI


class CommonUI(BaseUI):
    """
    Implements various common tests for UI
    """
    def create_org(self, org_name=None):
        """Creates Org"""
        org_name = org_name or generate_name(8, 8)
        self.navigator.go_to_org()  # go to org page
        self.org.create(org_name)
        self.navigator.go_to_select_org(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))

    def create_product(self, prd_name, description, provider,
                       create_provider=True, org=None):
        self.navigator.go_to_products()
        self.products.create(prd_name, description, provider,
                             create_provider=create_provider)
        if org:
            self.navigator.go_to_select_org(org)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(prd_name))

    def create_repo(self, repo_name, prd_name, repo_url):
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))

    def sync_repos(self, prd_name, repos):
        self.navigator.go_to_sync_status()
        self.sync.sync_custom_repos(prd_name, repos)
        self.assertIsNotNone(self.sync.assert_sync(prd_name, repos))

    def create_template(self, name, template_path, custom_really,
                        temp_type, snippet, os_list=None):
        """
        Method to creates new template with navigation
        """

        name = name or generate_name(6)
        temp_type = temp_type
        self.navigator.go_to_provisioning_templates()
        self.template.create(name, template_path, custom_really,
                             temp_type, snippet, os_list)
        self.navigator.go_to_provisioning_templates()
        self.assertIsNotNone(self.template.search(name))

    def create_user(self, name=None, password=None,
                    email=None, search_key=None):
        """
        Function to create a new User
        """

        name = name or generate_name(8)
        password = password or generate_name(8)
        email = email or generate_email_address()
        self.navigator.go_to_users()
        self.user.create(name, email, password, password)
        self.assertIsNotNone(self.user.search(name, search_key))
