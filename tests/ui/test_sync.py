"""
Test class for Custom Sync UI
"""

import unittest
from ddt import data, ddt
from nose.plugins.attrib import attr
from robottelo.common.helpers import generate_name, generate_strings_list
from tests.ui.baseui import BaseUI


RHCT = [('rhel', 'rhct6', 'rhct65', 'repo_name',
         'Red Hat CloudForms Tools for RHEL 6 RPMs x86_64 6.5'),
        ('rhel', 'rhct6', 'rhct65', 'repo_arch', 'x86_64'),
        ('rhel', 'rhct6', 'rhct65', 'repo_ver', '6.5'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_name',
         'Red Hat CloudForms Tools for RHEL 6 RPMs x86_64 6Server'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_arch', 'x86_64'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_ver', '6Server')]


@ddt
class Sync(BaseUI):
    """
    Implements Custom Sync tests in UI
    """

    org_name = generate_name(8, 8)

    @attr('ui', 'sync', 'implemented')
    @data(*generate_strings_list())
    def test_sync_repos(self, repo_name):
        """
        @Feature: Content Custom Sync - Positive Create
        @Test: Create Content Custom Sync with minimal input parameters
        @Assert: Whether Sync is successful
        """
        prd_name = generate_name(8, 8)
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
        self.navigator.go_to_sync_status()
        sync = self.sync.sync_custom_repos(prd_name, [repo_name])
        self.assertIsNotNone(sync)

    @unittest.skip("Test needs to create manifests using stageportal stuff")
    def test_sync_rhrepos(self):
        """
        @Feature: Content RedHat Sync - Positive Create
        @Test: Create Content RedHat Sync with two repos.
        @Assert: Whether Syncing RedHat Repos is successful
        """

        repos = self.sync.create_repos_tree(RHCT)
        self.login.login(self.katello_user, self.katello_passwd)
        # TODO: Create manifests and import using stageportal stuff.
        self.navigator.go_to_red_hat_repositories()
        self.sync.enable_rh_repos(repos)
        self.navigator.go_to_sync_status()
        sync = self.sync.sync_rh_repos(repos)
        self.assertIsNotNone(sync)
