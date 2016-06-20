# -*- encoding: utf-8 -*-
"""Unit tests for the ``repository_sets`` paths.

A full API reference for products can be found here:
http://www.katello.org/docs/api/apidoc/repository_sets.html


@Requirement: Repository set

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import PRDS, REPOSET
from robottelo.decorators import run_in_one_thread, run_only_on, tier1
from robottelo.test import APITestCase


@run_in_one_thread
class RepositorySetTestCase(APITestCase):
    """Tests for ``katello/api/v2/products/<product_id>/repository_sets``."""

    @tier1
    @run_only_on('sat')
    def test_positive_reposet_enable(self):
        """Enable repo from reposet

        @id: dedcecf7-613a-4e85-a3af-92fb57e2b0a1

        @Assert: Repository was enabled
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        product = entities.Product(
            name=PRDS['rhel'],
            organization=org,
        ).search()[0]
        reposet = entities.RepositorySet(
            name=REPOSET['rhva6'],
            product=product,
        ).search()[0]
        reposet.enable(data={'basearch': 'x86_64', 'releasever': '6Server'})
        repositories = reposet.available_repositories()['results']
        self.assertTrue([
            repo['enabled']
            for repo
            in repositories
            if (repo['substitutions']['basearch'] == 'x86_64' and
                repo['substitutions']['releasever'] == '6Server')
        ][0])

    @tier1
    @run_only_on('sat')
    def test_positive_reposet_disable(self):
        """Disable repo from reposet

        @id: 60a102df-099e-4325-8924-2a31e5f738ba

        @Assert: Repository was disabled
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        product = entities.Product(
            name=PRDS['rhel'],
            organization=org,
        ).search()[0]
        reposet = entities.RepositorySet(
            name=REPOSET['rhva6'],
            product=product,
        ).search()[0]
        reposet.enable(data={'basearch': 'x86_64', 'releasever': '6Server'})
        reposet.disable(data={'basearch': 'x86_64', 'releasever': '6Server'})
        repositories = reposet.available_repositories()['results']
        self.assertFalse([
            repo['enabled']
            for repo
            in repositories
            if (repo['substitutions']['basearch'] == 'x86_64' and
                repo['substitutions']['releasever'] == '6Server')
        ][0])
