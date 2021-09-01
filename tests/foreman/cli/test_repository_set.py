"""Repository Set CLI tests.

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

from robottelo import manifests
from robottelo.cli.factory import make_org
from robottelo.cli.product import Product
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.constants import PRDS
from robottelo.constants import REPOSET

pytestmark = [pytest.mark.run_in_one_thread, pytest.mark.tier1]


@pytest.fixture
def params(manifest_org):
    PRODUCT_NAME = PRDS['rhel']
    REPOSET_NAME = REPOSET['rhva6']
    ARCH = 'x86_64'
    ARCH_2 = 'i386'
    RELEASE = '6Server'

    product_id = Product.info({'name': PRODUCT_NAME, 'organization-id': manifest_org['id']})['id']
    reposet_id = RepositorySet.info(
        {'name': REPOSET_NAME, 'organization-id': manifest_org['id'], 'product-id': product_id}
    )['id']

    avail = {
        'id': {
            'name': REPOSET_NAME,
            'organization-id': manifest_org['id'],
            'product': PRODUCT_NAME,
        },
        'ids': {
            'id': reposet_id,
            'organization-id': manifest_org['id'],
            'product-id': product_id,
        },
        'label': {
            'name': REPOSET_NAME,
            'organization-label': manifest_org['label'],
            'product': PRODUCT_NAME,
        },
        'name': {
            'name': REPOSET_NAME,
            'organization': manifest_org['name'],
            'product': PRODUCT_NAME,
        },
    }

    enable = {
        'arch_2': {
            'basearch': ARCH_2,
            'name': REPOSET_NAME,
            'organization-id': manifest_org['id'],
            'product': PRODUCT_NAME,
            'releasever': RELEASE,
        },
        'id': {
            'basearch': ARCH,
            'name': REPOSET_NAME,
            'organization-id': manifest_org['id'],
            'product': PRODUCT_NAME,
            'releasever': RELEASE,
        },
        'ids': {
            'basearch': ARCH,
            'id': reposet_id,
            'organization-id': manifest_org['id'],
            'product-id': product_id,
            'releasever': RELEASE,
        },
        'label': {
            'basearch': ARCH,
            'name': REPOSET_NAME,
            'organization-label': manifest_org['label'],
            'product': PRODUCT_NAME,
            'releasever': RELEASE,
        },
        'name': {
            'basearch': ARCH,
            'name': REPOSET_NAME,
            'organization': manifest_org['name'],
            'product': PRODUCT_NAME,
            'releasever': RELEASE,
        },
    }

    match = {
        'enabled': {'enabled': 'true'},
        'enabled_arch_rel': {'enabled': 'true', 'arch': ARCH, 'release': RELEASE},
    }

    return {'enable': enable, 'avail': avail, 'match': match}


@pytest.fixture
def org():
    """Create and return an organization."""
    return make_org()


@pytest.fixture
def manifest_org(org, default_sat):
    """Upload a manifest to the organization."""
    with manifests.clone() as manifest:
        default_sat.put(manifest.content, manifest.filename)
    Subscription.upload({'file': manifest.filename, 'organization-id': org['id']})
    return org


def match_repos(repos, match_params):
    """Return a list of all repos that match every key-value pair in match_params."""
    return [repo for repo in repos if match_params.items() <= repo.items()]


@pytest.mark.upgrade
def test_positive_list_available_repositories(params):
    """List available repositories for repository-set

    :id: 987d6b08-acb0-4264-a459-9cef0d2c6f3f

    :expectedresults: List of available repositories is displayed, with
        valid amount of enabled repositories

    :CaseImportance: Critical
    """
    # No repos should be enabled by default
    result = RepositorySet.available_repositories(params['avail']['id'])
    assert len(match_repos(result, params['match']['enabled'])) == 0

    # Enable repo from Repository Set
    RepositorySet.enable(params['enable']['id'])

    # Only 1 repo should be enabled, and it should match the arch and releasever
    result = RepositorySet.available_repositories(params['avail']['name'])
    assert len(match_repos(result, params['match']['enabled'])) == 1

    # Enable one more repo
    RepositorySet.enable(params['enable']['arch_2'])

    # 2 repos should be enabled
    result = RepositorySet.available_repositories(params['avail']['label'])
    assert len(match_repos(result, params['match']['enabled'])) == 2

    # Disable one repo
    RepositorySet.disable(params['enable']['id'])

    # There should remain only 1 enabled repo
    result = RepositorySet.available_repositories(params['avail']['id'])
    assert len(match_repos(result, params['match']['enabled'])) == 1

    # Disable the last enabled repo
    RepositorySet.disable(params['enable']['arch_2'])

    # There should be no enabled repos
    result = RepositorySet.available_repositories(params['avail']['id'])
    assert len(match_repos(result, params['match']['enabled'])) == 0


def test_positive_enable_by_name(params):
    """Enable repo from reposet by names of reposet, org and product

    :id: a78537bd-b88d-4f00-8901-e7944e5de729

    :expectedresults: Repository was enabled

    :CaseImportance: Critical
    """
    RepositorySet.enable(params['enable']['name'])
    result = RepositorySet.available_repositories(params['avail']['name'])
    assert len(match_repos(result, params['match']['enabled_arch_rel'])) == 1


def test_positive_enable_by_label(params):
    """Enable repo from reposet by org label, reposet and product
    names

    :id: 5230c1cd-fed7-40ac-8445-bac4f9c5ee68

    :expectedresults: Repository was enabled

    :CaseImportance: Critical
    """
    RepositorySet.enable(params['enable']['label'])
    result = RepositorySet.available_repositories(params['avail']['label'])
    assert len(match_repos(result, params['match']['enabled_arch_rel'])) == 1


def test_positive_enable_by_id(params):
    """Enable repo from reposet by IDs of reposet, org and product

    :id: f7c88534-1d45-45d9-9b87-c50c4e268e8d

    :expectedresults: Repository was enabled

    :CaseImportance: Critical
    """
    RepositorySet.enable(params['enable']['ids'])
    result = RepositorySet.available_repositories(params['avail']['ids'])
    assert len(match_repos(result, params['match']['enabled_arch_rel'])) == 1


def test_positive_disable_by_name(params):
    """Disable repo from reposet by names of reposet, org and
    product

    :id: 1690a701-ae41-4724-bbc6-b0adba5a5319

    :expectedresults: Repository was disabled

    :CaseImportance: Critical
    """
    RepositorySet.enable(params['enable']['name'])
    RepositorySet.disable(params['enable']['name'])
    result = RepositorySet.available_repositories(params['avail']['name'])
    assert len(match_repos(result, params['match']['enabled'])) == 0


def test_positive_disable_by_label(params):
    """Disable repo from reposet by org label, reposet and product
    names

    :id: a87a5df6-f8ab-469e-94e5-ca79378f8dbe

    :expectedresults: Repository was disabled

    :CaseImportance: Critical
    """
    RepositorySet.enable(params['enable']['label'])
    RepositorySet.disable(params['enable']['label'])
    result = RepositorySet.available_repositories(params['avail']['label'])
    assert len(match_repos(result, params['match']['enabled'])) == 0


def test_positive_disable_by_id(params):
    """Disable repo from reposet by IDs of reposet, org and product

    :id: 0d6102ba-3fb9-4eb8-972e-d537e252a8e6

    :expectedresults: Repository was disabled

    :CaseImportance: Critical
    """
    RepositorySet.enable(params['enable']['ids'])
    RepositorySet.disable(params['enable']['ids'])
    result = RepositorySet.available_repositories(params['avail']['ids'])
    assert len(match_repos(result, params['match']['enabled'])) == 0
