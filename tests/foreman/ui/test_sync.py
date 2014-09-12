"""Test class for Custom Sync UI"""

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string, generate_strings_list
from robottelo.common.manifests import clone
from robottelo.common.ssh import upload_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_org
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


RHCT = [('rhel', 'rhct6', 'rhct65', 'repo_name',
         'Red Hat CloudForms Tools for RHEL 6 RPMs x86_64 6.5'),
        ('rhel', 'rhct6', 'rhct65', 'repo_arch', 'x86_64'),
        ('rhel', 'rhct6', 'rhct65', 'repo_ver', '6.5'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_name',
         'Red Hat CloudForms Tools for RHEL 6 RPMs x86_64 6Server'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_arch', 'x86_64'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_ver', '6Server')]


@ddt
class Sync(UITestCase):
    """Implements Custom Sync tests in UI"""

    org_name = None

    def setUp(self):
        super(Sync, self).setUp()
        # Make sure to use the Class' org_name instance
        if Sync.org_name is None:
            Sync.org_name = generate_string("alpha", 10)
            with Session(self.browser) as session:
                make_org(session, org_name=Sync.org_name)

    @attr('ui', 'sync', 'implemented')
    @data(*generate_strings_list())
    def test_sync_repos(self, repo_name):
        """@Test: Create Content Custom Sync with minimal input parameters

        @Feature: Content Custom Sync - Positive Create

        @Assert: Whether Sync is successful

        """
        prd_name = generate_string("alpha", 6)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        description = "test 123"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name, description)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_sync_status()
        sync = self.sync.sync_custom_repos(prd_name, [repo_name])
        # syn.sync_rh_repos returns boolean values and not objects
        self.assertTrue(sync)

    def test_sync_rhrepos(self):
        """@Test: Create Content RedHat Sync with two repos.

        @Feature: Content RedHat Sync - Positive Create

        @Assert: Whether Syncing RedHat Repos is successful

        """

        repos = self.sync.create_repos_tree(RHCT)
        alert_loc = common_locators['alert.success']
        path = clone()
        # upload_file function should take care of uploading to sauce labs.
        upload_file(path, remote_file=path)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_red_hat_subscriptions()
            self.subscriptions.upload(path)
            success_ele = session.nav.wait_until_element(alert_loc)
            self.assertTrue(success_ele)
            session.nav.go_to_red_hat_repositories()
            self.sync.enable_rh_repos(repos)
            session.nav.go_to_sync_status()
            sync = self.sync.sync_rh_repos(repos)
            # syn.sync_rh_repos returns boolean values and not objects
            self.assertTrue(sync)
