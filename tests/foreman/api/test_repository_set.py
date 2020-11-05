"""Unit tests for the ``repository_sets`` paths.

A full API reference for products can be found here:
http://www.katello.org/docs/api/apidoc/repository_sets.html


:Requirement: Repository Set

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Repositories

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import PRDS
from robottelo.constants import REPOSET
from robottelo.test import APITestCase


@pytest.mark.run_in_one_thread
class RepositorySetTestCase(APITestCase):
    """Tests for ``katello/api/v2/products/<product_id>/repository_sets``."""

    @pytest.mark.tier1
    def test_positive_reposet_enable(self):
        """Enable repo from reposet

        :id: dedcecf7-613a-4e85-a3af-92fb57e2b0a1

        :expectedresults: Repository was enabled

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        product = entities.Product(name=PRDS['rhel'], organization=org).search()[0]
        reposet = entities.RepositorySet(name=REPOSET['rhva6'], product=product).search()[0]
        data = {'basearch': 'x86_64', 'releasever': '6Server', 'product_id': product.id}
        reposet.enable(data=data)
        repositories = reposet.available_repositories(data=data)['results']
        self.assertTrue(
            [
                repo['enabled']
                for repo in repositories
                if (
                    repo['substitutions']['basearch'] == 'x86_64'
                    and repo['substitutions']['releasever'] == '6Server'
                )
            ][0]
        )

    @pytest.mark.tier1
    @pytest.mark.upgrade
    def test_positive_reposet_disable(self):
        """Disable repo from reposet

        :id: 60a102df-099e-4325-8924-2a31e5f738ba

        :expectedresults: Repository was disabled

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        product = entities.Product(name=PRDS['rhel'], organization=org).search()[0]
        reposet = entities.RepositorySet(name=REPOSET['rhva6'], product=product).search()[0]
        data = {'basearch': 'x86_64', 'releasever': '6Server', 'product_id': product.id}
        reposet.enable(data=data)
        reposet.disable(data=data)
        repositories = reposet.available_repositories(data=data)['results']
        self.assertFalse(
            [
                repo['enabled']
                for repo in repositories
                if (
                    repo['substitutions']['basearch'] == 'x86_64'
                    and repo['substitutions']['releasever'] == '6Server'
                )
            ][0]
        )
