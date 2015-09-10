from robottelo.cli.factory import make_org
from robottelo.cli.product import Product
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo import manifests
from robottelo.constants import PRDS, REPOSET
from robottelo.decorators import skip_if_bug_open
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase


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

    def test_repositoryset_enable_by_name(self):
        """@Test: Enable repo from reposet by names of reposet, org and product

        @Feature: Repository-set

        @Assert: Repository was enabled

        """
        org = make_org()
        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        result = Subscription.upload({
            u'file': manifest,
            u'organization-id': org['id'],
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.enable({
            u'name': REPOSET['rhva6'],
            u'organization': org['name'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.available_repositories({
            u'name': REPOSET['rhva6'],
            u'organization': org['name'],
            u'product': PRDS['rhel'],
        })
        self.assertEqual(result.return_code, 0)
        enabled = [
            repo['enabled']
            for repo
            in result.stdout
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'true')

    def test_repositoryset_enable_by_label(self):
        """@Test: Enable repo from reposet by org label, reposet and product
        names

        @Feature: Repository-set

        @Assert: Repository was enabled

        """
        org = make_org()
        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        result = Subscription.upload({
            u'file': manifest,
            u'organization-id': org['id'],
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.enable({
            u'name': REPOSET['rhva6'],
            u'organization-label': org['label'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.available_repositories({
            u'name': REPOSET['rhva6'],
            u'organization-label': org['label'],
            u'product': PRDS['rhel'],
        })
        self.assertEqual(result.return_code, 0)
        enabled = [
            repo['enabled']
            for repo
            in result.stdout
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'true')

    def test_repositoryset_enable_by_id(self):
        """@Test: Enable repo from reposet by IDs of reposet, org and product

        @Feature: Repository-set

        @Assert: Repository was enabled

        """
        org = make_org()
        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        result = Subscription.upload({
            u'file': manifest,
            u'organization-id': org['id'],
        })
        self.assertEqual(result.return_code, 0)
        product_id = Product.info({
            u'name': PRDS['rhel'],
            u'organization-id': org['id'],
        }).stdout['id']
        reposet_id = RepositorySet.info({
            u'name': REPOSET['rhva6'],
            u'organization-id': org['id'],
            u'product-id': product_id,
        }).stdout['id']
        result = RepositorySet.enable({
            u'id': reposet_id,
            u'organization-id': org['id'],
            u'product-id': product_id,
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.available_repositories({
            u'id': reposet_id,
            u'organization-id': org['id'],
            u'product-id': product_id,
        })
        self.assertEqual(result.return_code, 0)
        enabled = [
            repo['enabled']
            for repo
            in result.stdout
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'true')

    def test_repositoryset_disable_by_name(self):
        """@Test: Disable repo from reposet by names of reposet, org and product

        @Feature: Repository-set

        @Assert: Repository was disabled

        """
        org = make_org()
        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        result = Subscription.upload({
            u'file': manifest,
            u'organization-id': org['id'],
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.enable({
            u'name': REPOSET['rhva6'],
            u'organization': org['name'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.disable({
            u'name': REPOSET['rhva6'],
            u'organization': org['name'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.available_repositories({
            u'name': REPOSET['rhva6'],
            u'organization': org['name'],
            u'product': PRDS['rhel'],
        })
        self.assertEqual(result.return_code, 0)
        enabled = [
            repo['enabled']
            for repo
            in result.stdout
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'false')

    def test_repositoryset_disable_by_label(self):
        """@Test: Disable repo from reposet by org label, reposet and product
        names

        @Feature: Repository-set

        @Assert: Repository was disabled

        """
        org = make_org()
        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        result = Subscription.upload({
            u'file': manifest,
            u'organization-id': org['id'],
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.enable({
            u'name': REPOSET['rhva6'],
            u'organization-label': org['label'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.disable({
            u'name': REPOSET['rhva6'],
            u'organization-label': org['label'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.available_repositories({
            u'name': REPOSET['rhva6'],
            u'organization-label': org['label'],
            u'product': PRDS['rhel'],
        })
        self.assertEqual(result.return_code, 0)
        enabled = [
            repo['enabled']
            for repo
            in result.stdout
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'false')

    def test_repositoryset_disable_by_id(self):
        """@Test: Disable repo from reposet by IDs of reposet, org and product

        @Feature: Repository-set

        @Assert: Repository was disabled

        """
        org = make_org()
        manifest = manifests.clone()
        upload_file(manifest, remote_file=manifest)
        result = Subscription.upload({
            u'file': manifest,
            u'organization-id': org['id'],
        })
        self.assertEqual(result.return_code, 0)
        product_id = Product.info({
            u'name': PRDS['rhel'],
            u'organization-id': org['id'],
        }).stdout['id']
        reposet_id = RepositorySet.info({
            u'name': REPOSET['rhva6'],
            u'organization-id': org['id'],
            u'product-id': product_id,
        }).stdout['id']
        result = RepositorySet.enable({
            u'id': reposet_id,
            u'organization-id': org['id'],
            u'product-id': product_id,
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.disable({
            u'id': reposet_id,
            u'organization-id': org['id'],
            u'product-id': product_id,
            u'releasever': '6Server',
            u'basearch': 'x86_64',
        })
        self.assertEqual(result.return_code, 0)
        result = RepositorySet.available_repositories({
            u'id': reposet_id,
            u'organization-id': org['id'],
            u'product-id': product_id,
        })
        self.assertEqual(result.return_code, 0)
        enabled = [
            repo['enabled']
            for repo
            in result.stdout
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'false')
