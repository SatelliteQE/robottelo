"""
Test class for Repository UI
"""

from ddt import data, ddt
from nose.plugins.attrib import attr
from robottelo.ui.navigator import Navigator
from robottelo.ui.org import Org
from robottelo.ui.login import Login
from robottelo.common.helpers import generate_name, generate_strings_list
from tests.ui.baseui import BaseUI


@ddt
class Repos(BaseUI):
    """
    Implements Repos tests in UI
    """

    org_name = None

    def setUp(self):
        super(Repos, self).setUp()
        # Make sure to use the Class' org_name instance
        if Repos.org_name is None:
            Repos.org_name = generate_name(8, 8)
            login = Login(self.browser)
            nav = Navigator(self.browser)
            org = Org(self.browser)
            login.login(self.katello_user, self.katello_passwd)
            nav.go_to_org()
            org.create(Repos.org_name)
            login.logout()

    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_create_repo(self, repo_name):
        """
        @Feature: Content Repos - Positive Create
        @Test: Create Content Repos with minimal input parameters
        @Assert: Repos is created
        """

        prd_name = generate_name(8, 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(Repos.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))

    @attr('ui', 'repo', 'implemented')
    @data(*generate_strings_list())
    def test_remove_repo(self, repo_name):
        """
        @Feature: Content Repos - Positive Delete
        @Test: Create Content Repos with minimal input parameters
        @Assert: Repos is Deleted
        """

        prd_name = generate_name(8, 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(Repos.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.navigator.go_to_select_org(Repos.org_name)
        self.navigator.go_to_products()
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.repository.delete(repo_name)
        self.assertIsNone(self.repository.search(repo_name))
