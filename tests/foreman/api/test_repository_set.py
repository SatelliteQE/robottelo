"""Tests for ``repository_sets`` API endpoints.

A full API reference can be found here:
https://theforeman.org/plugins/katello/3.16/api/apidoc/v2/repository_sets.html

:Requirement: Repository Set

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""

import pytest

from robottelo.constants import PRDS, REPOSET

pytestmark = [pytest.mark.run_in_one_thread, pytest.mark.tier1]

PRODUCT_NAME = PRDS['rhel']
REPOSET_NAME = REPOSET['rhva6']
ARCH = 'x86_64'
RELEASE = '6Server'


@pytest.fixture
def product(function_sca_manifest_org, module_target_sat):
    """Find and return the product matching PRODUCT_NAME."""
    return module_target_sat.api.Product(
        name=PRODUCT_NAME, organization=function_sca_manifest_org
    ).search()[0]


@pytest.fixture
def reposet(product, module_target_sat):
    """Find and return the repository set matching REPOSET_NAME and product."""
    return module_target_sat.api.RepositorySet(name=REPOSET_NAME, product=product).search()[0]


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


@pytest.mark.upgrade
def test_positive_reposet_enable_and_disable(reposet, params):
    """Enable & disble repo from reposet

    :id: b77b7eb6-a9b0-4e89-bca9-b75c33ac49e2

    :expectedresults: Repository was enabled & disabled

    :CaseImportance: Critical
    """
    reposet.enable(data=params['enable'])

    repos = reposet.available_repositories(data=params['enable'])['results']
    matching_repos = match_repos(repos, params['match'])
    assert len(matching_repos) == 1

    reposet.disable(data=params['enable'])

    repos = reposet.available_repositories(data=params['enable'])['results']
    matching_repos = match_repos(repos, params['match'])
    assert len(matching_repos) == 0
