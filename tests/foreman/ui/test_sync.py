"""Test class for Custom Sync UI"""

from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import FAKE_1_YUM_REPO
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import run_only_on
from robottelo.test import UITestCase
from robottelo.ui.session import Session

RHCT = [('rhel', 'rhct6', 'rhct65', 'repo_name',
         'Red Hat CloudForms Tools for RHEL 6 RPMs x86_64 6.5'),
        ('rhel', 'rhct6', 'rhct65', 'repo_arch', 'x86_64'),
        ('rhel', 'rhct6', 'rhct65', 'repo_ver', '6.5'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_name',
         'Red Hat CloudForms Tools for RHEL 6 RPMs x86_64 6Server'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_arch', 'x86_64'),
        ('rhel', 'rhct6', 'rhct6S', 'repo_ver', '6Server')]


class Sync(UITestCase):
    """Implements Custom Sync tests in UI"""

    def setUp(self):  # noqa
        super(Sync, self).setUp()
        self.organization = entities.Organization().create()

    @run_only_on('sat')
    def test_sync_custom_repos(self):
        """@Test: Create Content Custom Sync with minimal input parameters

        @Feature: Content Custom Sync - Positive Create

        @Assert: Whether Sync is successful

        """
        # Creates new product
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repository_name in generate_strings_list():
                with self.subTest(repository_name):
                    # Creates new repository through API
                    entities.Repository(
                        name=repository_name,
                        url=FAKE_1_YUM_REPO,
                        product=product,
                    ).create()
                    session.nav.go_to_select_org(self.organization.name)
                    session.nav.go_to_sync_status()
                    sync = self.sync.sync_custom_repos(
                        product.name, [repository_name]
                    )
                    # sync.sync_custom_repos returns boolean value
                    self.assertTrue(sync)

    def test_sync_rh_repos(self):
        """@Test: Create Content RedHat Sync with two repos.

        @Feature: Content RedHat Sync - Positive Create

        @Assert: Whether Syncing RedHat Repos is successful

        """
        repos = self.sync.create_repos_tree(RHCT)
        with open(manifests.clone(), 'rb') as manifest:
            upload_manifest(self.organization.id, manifest)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_red_hat_repositories()
            self.sync.enable_rh_repos(repos)
            session.nav.go_to_sync_status()
            sync = self.sync.sync_rh_repos(repos)
            # syn.sync_rh_repos returns boolean values and not objects
            self.assertTrue(sync)
