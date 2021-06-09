"""Tests for ``repository_sets`` API endpoints.

A full API reference can be found here:
https://theforeman.org/plugins/katello/3.16/api/apidoc/v2/repository_sets.html

:Requirement: Repository Set

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Repositories

:Assignee: chiggins

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

pytestmark = [pytest.mark.run_in_one_thread, pytest.mark.tier1]

PRODUCT_NAME = PRDS['rhel']
REPOSET_NAME = REPOSET['rhva6']
ARCH = 'x86_64'
RELEASE = '6Server'


@pytest.fixture
def org():
    """Create organization."""
    return entities.Organization().create()


@pytest.fixture
def manifest_org(org):
    """Upload manifest to organization."""
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    return org


@pytest.fixture
def product(manifest_org):
    """Find and return the product matching PRODUCT_NAME."""
    return entities.Product(name=PRODUCT_NAME, organization=manifest_org).search()[0]


@pytest.fixture
def reposet(product):
    """Find and return the repository set matching REPOSET_NAME and product."""
    return entities.RepositorySet(name=REPOSET_NAME, product=product).search()[0]


@pytest.fixture
def params(product):
    """Return dictionary of arch, release, and product id, for use in enabling and disabling
    repositories within a repository set.
    """
    enable = {'basearch': ARCH, 'releasever': RELEASE, 'product_id': product.id}
    match = {'substitutions': {'basearch': ARCH, 'releasever': RELEASE}, 'enabled': True}

    return {'enable': enable, 'match': match}


def match_repos(repos, match_params):
    """Return a list of all repos that match every key-value pair in match_params."""
    return [repo for repo in repos if match_params.items() <= repo.items()]


def test_positive_reposet_enable(reposet, params):
    """Enable repo from reposet

    :id: dedcecf7-613a-4e85-a3af-92fb57e2b0a1

    :expectedresults: Repository was enabled

    :CaseImportance: Critical
    """
    reposet.enable(data=params['enable'])

    repos = reposet.available_repositories(data=params['enable'])['results']
    matching_repos = match_repos(repos, params['match'])
    assert len(matching_repos) == 1


@pytest.mark.upgrade
def test_positive_reposet_disable(reposet, params):
    """Disable repo from reposet

    :id: 60a102df-099e-4325-8924-2a31e5f738ba

    :expectedresults: Repository was disabled

    :CaseImportance: Critical
    """
    reposet.enable(data=params['enable'])
    reposet.disable(data=params['enable'])

    repos = reposet.available_repositories(data=params['enable'])['results']
    matching_repos = match_repos(repos, params['match'])
    assert len(matching_repos) == 0
