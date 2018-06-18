"""Test class for Custom Sync UI

:Requirement: Sync

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import (
    ATOMIC_HOST_TREE,
    FAKE_1_YUM_REPO,
    FEDORA23_OSTREE_REPO,
    PRDS,
    REPOS,
    REPO_TAB,
)
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier4,
    upgrade
)
from robottelo.decorators.host import skip_if_os
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


class SyncTestCase(UITestCase):
    """Implements Custom Sync tests in UI"""

    def setUp(self):  # noqa
        super(SyncTestCase, self).setUp()
        self.organization = entities.Organization().create()

    @run_only_on('sat')
    @tier1
    def test_positive_sync_custom_repo(self):
        """Create Content Custom Sync with minimal input parameters

        :id: 00fb0b04-0293-42c2-92fa-930c75acee89

        :expectedresults: Sync procedure is successful

        :CaseImportance: Critical
        """
        # Creates new product
        product = entities.Product(organization=self.organization).create()
        with Session(self) as session:
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

    @run_in_one_thread
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_sync_rh_repos(self):
        """Create Content RedHat Sync with two repos.

        :id: e30f6509-0b65-4bcc-a522-b4f3089d3911

        :expectedresults: Sync procedure for RedHat Repos is successful

        :CaseLevel: Integration
        """
        with manifests.clone() as manifest:
            upload_manifest(self.organization.id, manifest.content)
        with Session(self) as session:
            repos = self.sync.create_repos_tree(RHCT)
            session.nav.go_to_select_org(self.organization.name)
            self.sync.enable_rh_repos(repos, REPO_TAB['rpms'])
            session.nav.go_to_sync_status()
            sync = self.sync.sync_rh_repos(repos)
            # syn.sync_rh_repos returns boolean values and not objects
            self.assertTrue(sync)

    @stubbed()
    @tier4
    def test_positive_sync_disconnected_to_connected_rh_repos(self):
        """Migrating from disconnected to connected satellite.

        :id: 03b3d904-1697-441b-bb12-8b353a556218

        :Steps:
            1. Update the link to an internal http link where the content has
                been extracted from ISO's.
            2. Import a valid manifest.
            3. Enable few RedHat repos and Sync them.
            4. Now let's revert back the link to CDN's default link which is,
                'https://cdn.redhat.com'.
            5. Now Navigate to the 'Sync Page' and resync the repos synced
                earlier.

        :expectedresults: 1. Syncing should work fine without any issues. 2.
            Only the deltas are re-downloaded and not the entire repo.  [ Could
            be an exception when 7Server was earlier pointing to 7.1 and
            current 7Server points to latest 7.2] 3. After reverting the link
            the repos should not be seen in 'Others Tab' and should be seen
            only in 'RPM's Tab'.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    @upgrade
    def test_positive_sync_custom_ostree_repo(self):
        """Create custom ostree repository and sync it.

        :id: e4119b9b-0356-4661-a3ec-e5807224f7d2

        :expectedresults: ostree repo should be synced successfully

        :CaseLevel: Integration
        """
        prod = entities.Product(organization=self.organization).create()
        repo_name = gen_string('alpha')
        # Creates new ostree repository using api
        entities.Repository(
            name=repo_name,
            content_type='ostree',
            url=FEDORA23_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_sync_status()
            sync = self.sync.sync_custom_repos(prod.name, [repo_name])
            # sync.sync_custom_repos returns boolean value
            self.assertTrue(sync)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @skip_if_not_set('fake_manifest')
    @tier2
    @upgrade
    def test_positive_sync_rh_ostree_repo(self):
        """Sync CDN based ostree repository .

        :id: 4d28fff0-5fda-4eee-aa0c-c5af02c31de5

        :Steps:
            1. Import a valid manifest
            2. Enable the OStree repo and sync it

        :expectedresults: ostree repo should be synced successfully from CDN

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        with Session(self) as session:
            repos = self.sync.create_repos_tree(ATOMIC_HOST_TREE)
            session.nav.go_to_select_org(org.name)
            self.sync.enable_rh_repos(repos, repo_tab=REPO_TAB['ostree'])
            session.nav.go_to_sync_status()
            self.assertTrue(self.sync.sync_noversion_rh_repos(
                PRDS['rhah'], [REPOS['rhaht']['name']]
            ))
