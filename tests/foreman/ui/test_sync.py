"""Test class for Custom Sync UI"""

from ddt import ddt
from nailgun import entities
from robottelo.common.constants import FAKE_1_YUM_REPO
from robottelo.common.decorators import data, run_only_on
from robottelo.common.helpers import generate_strings_list
from robottelo.common import manifests
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


@ddt
class Sync(UITestCase):
    """Implements Custom Sync tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        org_attrs = entities.Organization().create_json()
        cls.org_name = org_attrs['name']
        cls.org_id = org_attrs['id']

        super(Sync, cls).setUpClass()

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_sync_custom_repos(self, repository_name):
        """@Test: Create Content Custom Sync with minimal input parameters

        @Feature: Content Custom Sync - Positive Create

        @Assert: Whether Sync is successful

        """

        # Creates new product
        product_attrs = entities.Product(
            organization=self.org_id
        ).create_json()
        # Creates new repository
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id']
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(Sync.org_name)
            session.nav.go_to_sync_status()
            sync = self.sync.sync_custom_repos(product_attrs['name'],
                                               [repository_name])
            # syn.sync_custom_repos returns boolean values and not objects
            self.assertTrue(sync)

    def test_sync_rh_repos(self):
        """@Test: Create Content RedHat Sync with two repos.

        @Feature: Content RedHat Sync - Positive Create

        @Assert: Whether Syncing RedHat Repos is successful

        """

        repos = self.sync.create_repos_tree(RHCT)
        with open(manifests.clone(), 'rb') as manifest:
            entities.Subscription().upload(
                data={'organization_id': self.org_id},
                files={'content': manifest},
            )
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_red_hat_repositories()
            self.sync.enable_rh_repos(repos)
            session.nav.go_to_sync_status()
            sync = self.sync.sync_rh_repos(repos)
            # syn.sync_rh_repos returns boolean values and not objects
            self.assertTrue(sync)
