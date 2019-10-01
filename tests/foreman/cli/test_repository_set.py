"""Tests for cli repository set

:Requirement: Repository Set

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Repositories

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.cli.factory import make_org
from robottelo.cli.product import Product
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo import manifests
from robottelo.constants import PRDS, REPOSET
from robottelo.decorators import (
    run_in_one_thread,
    tier1,
    upgrade,
)
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase


@run_in_one_thread
class RepositorySetTestCase(CLITestCase):
    """Repository Set CLI tests."""

    @tier1
    @upgrade
    def test_positive_list_available_repositories(self):
        """List available repositories for repository-set

        :id: 987d6b08-acb0-4264-a459-9cef0d2c6f3f

        :expectedresults: List of available repositories is displayed, with
            valid amount of enabled repositories

        :CaseImportance: Critical
        """
        rhel_product_name = PRDS['rhel']
        rhel_repo_set = REPOSET['rhva6']

        # Clone manifest and upload it
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            u'file': manifest.filename,
            u'organization-id': org['id'],
        })

        # No repos should be enabled by default
        result = RepositorySet.available_repositories({
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
        })
        self.assertEqual(
            sum(int(repo['enabled'] == u'true') for repo in result),
            0
        )

        # Enable repo from Repository Set
        RepositorySet.enable({
            u'basearch': 'x86_64',
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
            u'releasever': '6Server',
        })

        # Only 1 repo should be enabled
        result = RepositorySet.available_repositories({
            u'name': rhel_repo_set,
            u'organization': org['name'],
            u'product': rhel_product_name,
        })
        self.assertEqual(
            sum(int(repo['enabled'] == u'true') for repo in result),
            1
        )

        # Enable one more repo
        RepositorySet.enable({
            u'basearch': 'i386',
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
            u'releasever': '6Server',
        })

        # 2 repos should be enabled
        result = RepositorySet.available_repositories({
            u'name': rhel_repo_set,
            u'organization-label': org['label'],
            u'product': rhel_product_name,
        })
        self.assertEqual(
            sum(int(repo['enabled'] == u'true') for repo in result),
            2
        )

        # Disable one repo
        RepositorySet.disable({
            u'basearch': 'i386',
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
            u'releasever': '6Server',
        })

        # There should remain only 1 enabled repo
        result = RepositorySet.available_repositories({
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
        })
        self.assertEqual(
            sum(int(repo['enabled'] == u'true') for repo in result),
            1
        )

        # Disable the last enabled repo
        RepositorySet.disable({
            u'basearch': 'x86_64',
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
            u'releasever': '6Server',
        })

        # There should be no enabled repos
        result = RepositorySet.available_repositories({
            u'name': rhel_repo_set,
            u'organization-id': org['id'],
            u'product': rhel_product_name,
        })
        self.assertEqual(
            sum(int(repo['enabled'] == u'true') for repo in result),
            0
        )

    @tier1
    def test_positive_enable_by_name(self):
        """Enable repo from reposet by names of reposet, org and product

        :id: a78537bd-b88d-4f00-8901-e7944e5de729

        :expectedresults: Repository was enabled

        :CaseImportance: Critical
        """
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            u'file': manifest.filename,
            u'organization-id': org['id'],
        })
        RepositorySet.enable({
            u'basearch': 'x86_64',
            u'name': REPOSET['rhva6'],
            u'organization': org['name'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
        })
        result = RepositorySet.available_repositories({
            u'name': REPOSET['rhva6'],
            u'organization': org['name'],
            u'product': PRDS['rhel'],
        })
        enabled = [
            repo['enabled']
            for repo
            in result
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'true')

    @tier1
    def test_positive_enable_by_label(self):
        """Enable repo from reposet by org label, reposet and product
        names

        :id: 5230c1cd-fed7-40ac-8445-bac4f9c5ee68

        :expectedresults: Repository was enabled

        :CaseImportance: Critical
        """
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            u'file': manifest.filename,
            u'organization-id': org['id'],
        })
        RepositorySet.enable({
            u'basearch': 'x86_64',
            u'name': REPOSET['rhva6'],
            u'organization-label': org['label'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
        })
        result = RepositorySet.available_repositories({
            u'name': REPOSET['rhva6'],
            u'organization-label': org['label'],
            u'product': PRDS['rhel'],
        })
        enabled = [
            repo['enabled']
            for repo
            in result
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'true')

    @tier1
    def test_positive_enable_by_id(self):
        """Enable repo from reposet by IDs of reposet, org and product

        :id: f7c88534-1d45-45d9-9b87-c50c4e268e8d

        :expectedresults: Repository was enabled

        :CaseImportance: Critical
        """
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            u'file': manifest.filename,
            u'organization-id': org['id'],
        })
        product_id = Product.info({
            u'name': PRDS['rhel'],
            u'organization-id': org['id'],
        })['id']
        reposet_id = RepositorySet.info({
            u'name': REPOSET['rhva6'],
            u'organization-id': org['id'],
            u'product-id': product_id,
        })['id']
        RepositorySet.enable({
            u'basearch': 'x86_64',
            u'id': reposet_id,
            u'organization-id': org['id'],
            u'product-id': product_id,
            u'releasever': '6Server',
        })
        result = RepositorySet.available_repositories({
            u'id': reposet_id,
            u'organization-id': org['id'],
            u'product-id': product_id,
        })
        enabled = [
            repo['enabled']
            for repo
            in result
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'true')

    @tier1
    def test_positive_disable_by_name(self):
        """Disable repo from reposet by names of reposet, org and
        product

        :id: 1690a701-ae41-4724-bbc6-b0adba5a5319

        :expectedresults: Repository was disabled

        :CaseImportance: Critical
        """
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            u'file': manifest.filename,
            u'organization-id': org['id'],
        })
        RepositorySet.enable({
            u'basearch': 'x86_64',
            u'name': REPOSET['rhva6'],
            u'organization': org['name'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
        })
        RepositorySet.disable({
            u'basearch': 'x86_64',
            u'name': REPOSET['rhva6'],
            u'organization': org['name'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
        })
        result = RepositorySet.available_repositories({
            u'name': REPOSET['rhva6'],
            u'organization': org['name'],
            u'product': PRDS['rhel'],
        })
        enabled = [
            repo['enabled']
            for repo
            in result
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'false')

    @tier1
    def test_positive_disable_by_label(self):
        """Disable repo from reposet by org label, reposet and product
        names

        :id: a87a5df6-f8ab-469e-94e5-ca79378f8dbe

        :expectedresults: Repository was disabled

        :CaseImportance: Critical
        """
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            u'file': manifest.filename,
            u'organization-id': org['id'],
        })
        RepositorySet.enable({
            u'basearch': 'x86_64',
            u'name': REPOSET['rhva6'],
            u'organization-label': org['label'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
        })
        RepositorySet.disable({
            u'basearch': 'x86_64',
            u'name': REPOSET['rhva6'],
            u'organization-label': org['label'],
            u'product': PRDS['rhel'],
            u'releasever': '6Server',
        })
        result = RepositorySet.available_repositories({
            u'name': REPOSET['rhva6'],
            u'organization-label': org['label'],
            u'product': PRDS['rhel'],
        })
        enabled = [
            repo['enabled']
            for repo
            in result
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'false')

    @tier1
    def test_positive_disable_by_id(self):
        """Disable repo from reposet by IDs of reposet, org and product

        :id: 0d6102ba-3fb9-4eb8-972e-d537e252a8e6

        :expectedresults: Repository was disabled

        :CaseImportance: Critical
        """
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            u'file': manifest.filename,
            u'organization-id': org['id'],
        })
        product_id = Product.info({
            u'name': PRDS['rhel'],
            u'organization-id': org['id'],
        })['id']
        reposet_id = RepositorySet.info({
            u'name': REPOSET['rhva6'],
            u'organization-id': org['id'],
            u'product-id': product_id,
        })['id']
        RepositorySet.enable({
            u'basearch': 'x86_64',
            u'id': reposet_id,
            u'organization-id': org['id'],
            u'product-id': product_id,
            u'releasever': '6Server',
        })
        RepositorySet.disable({
            u'basearch': 'x86_64',
            u'id': reposet_id,
            u'organization-id': org['id'],
            u'product-id': product_id,
            u'releasever': '6Server',
        })
        result = RepositorySet.available_repositories({
            u'id': reposet_id,
            u'organization-id': org['id'],
            u'product-id': product_id,
        })
        enabled = [
            repo['enabled']
            for repo
            in result
            if repo['arch'] == 'x86_64' and repo['release'] == '6Server'
        ][0]
        self.assertEqual(enabled, 'false')
