from robottelo.common.decorators import skip_if_bug_open
from robottelo.test import CLITestCase
from robottelo.cli.factory import make_org
from robottelo.cli.subscription import Subscription
from robottelo.cli.repository_set import RepositorySet
from robottelo.common import manifests
from robottelo.common.ssh import upload_file


class TestRepositorySet(CLITestCase):
    """Repository Set CLI tests."""

    @skip_if_bug_open('bugzilla', 1172171)
    def test_available_repository_1(self):
        """@Test: Check if repositories are available

        @Feature: Repository-set

        @Assert: List of available repositories is displayed

        @BZ: 1172171

        """
        self.fail('This stubbed test should be fleshed out')

    def test_repositoryset_available_repositories(self):
        """@Test: List available repositories for repository-set

        @Feature: Repository-set

        @Assert: List of available repositories is displayed, with
        valid amount of enabled repositories

        """
        rhel_product_name = 'Red Hat Enterprise Linux Server'
        rhel_repo_set = (
            'Red Hat Enterprise Virtualization Agents '
            'for RHEL 6 Server (RPMs)'
        )

        # Clone manifest and upload it
        org = make_org()
        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        result = Subscription.upload({
            u'file': manifest,
            u'organization-id': org['id'],
        })
        self.assertEqual(result.return_code, 0)

        # No repos should be enabled by default
        result = RepositorySet.available_repositories({
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            sum(int(repo['enabled'] == u'true') for repo in result.stdout),
            0
        )

        # Enable repo from Repository Set
        result = RepositorySet.enable({
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)

        # Only 1 repo should be enabled
        result = RepositorySet.available_repositories({
            u'name': rhel_repo_set,
            u'organization': org['name'],
            u'product': rhel_product_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            sum(int(repo['enabled'] == u'true') for repo in result.stdout),
            1
        )

        # Enable one more repo
        result = RepositorySet.enable({
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
            u'releasever': '6Server',
            u'basearch': 'i386',
        })
        self.assertEqual(result.return_code, 0)

        # 2 repos should be enabled
        result = RepositorySet.available_repositories({
            u'name': rhel_repo_set,
            u'organization-label': org['label'],
            u'product': rhel_product_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            sum(int(repo['enabled'] == u'true') for repo in result.stdout),
            2
        )

        # Disable one repo
        result = RepositorySet.disable({
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
            u'releasever': '6Server',
            u'basearch': 'i386',
        })
        self.assertEqual(result.return_code, 0)

        # There should remain only 1 enabled repo
        result = RepositorySet.available_repositories({
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            sum(int(repo['enabled'] == u'true') for repo in result.stdout),
            1
        )

        # Disable the last enabled repo
        result = RepositorySet.disable({
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)

        # There should be no enabled repos
        result = RepositorySet.available_repositories({
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            sum(int(repo['enabled'] == u'true') for repo in result.stdout),
            0
        )
