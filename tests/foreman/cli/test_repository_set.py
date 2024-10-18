"""Repository Set CLI tests.

:Requirement: Repository Set

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""

import pytest

from robottelo.constants import PRDS, REPOSET

pytestmark = [pytest.mark.run_in_one_thread, pytest.mark.tier1]


@pytest.fixture
def params(function_sca_manifest_org, target_sat):
    PRODUCT_NAME = PRDS['rhel']
    REPOSET_NAME = REPOSET['rhva6']
    ARCH = 'x86_64'
    ARCH_2 = 'i386'
    RELEASE = '6Server'
    manifest_org = function_sca_manifest_org

    product_id = target_sat.cli.Product.info(
        {'name': PRODUCT_NAME, 'organization-id': manifest_org.id}
    )['id']
    reposet_id = target_sat.cli.RepositorySet.info(
        {'name': REPOSET_NAME, 'organization-id': manifest_org.id, 'product-id': product_id}
    )['id']

    avail = {
        'id': {
            'name': REPOSET_NAME,
            'organization-id': manifest_org.id,
            'product': PRODUCT_NAME,
        },
        'ids': {
            'id': reposet_id,
            'organization-id': manifest_org.id,
            'product-id': product_id,
        },
        'label': {
            'name': REPOSET_NAME,
            'organization-label': manifest_org.label,
            'product': PRODUCT_NAME,
        },
        'name': {
            'name': REPOSET_NAME,
            'organization': manifest_org.name,
            'product': PRODUCT_NAME,
        },
    }

    enable = {
        'arch_2': {
            'basearch': ARCH_2,
            'name': REPOSET_NAME,
            'organization-id': manifest_org.id,
            'product': PRODUCT_NAME,
            'releasever': RELEASE,
        },
        'id': {
            'basearch': ARCH,
            'name': REPOSET_NAME,
            'organization-id': manifest_org.id,
            'product': PRODUCT_NAME,
            'releasever': RELEASE,
        },
        'ids': {
            'basearch': ARCH,
            'id': reposet_id,
            'organization-id': manifest_org.id,
            'product-id': product_id,
            'releasever': RELEASE,
        },
        'label': {
            'basearch': ARCH,
            'name': REPOSET_NAME,
            'organization-label': manifest_org.label,
            'product': PRODUCT_NAME,
            'releasever': RELEASE,
        },
        'name': {
            'basearch': ARCH,
            'name': REPOSET_NAME,
            'organization': manifest_org.name,
            'product': PRODUCT_NAME,
            'releasever': RELEASE,
        },
    }

    match = {
        'enabled': {'enabled': 'true'},
        'enabled_arch_rel': {'enabled': 'true', 'arch': ARCH, 'release': RELEASE},
    }

    return {'enable': enable, 'avail': avail, 'match': match}


def match_repos(repos, match_params):
    """Return a list of all repos that match every key-value pair in match_params."""
    return [repo for repo in repos if match_params.items() <= repo.items()]


@pytest.mark.upgrade
def test_positive_list_available_repositories(params, target_sat):
    """List available repositories for repository-set

    :id: 987d6b08-acb0-4264-a459-9cef0d2c6f3f

    :expectedresults: List of available repositories is displayed, with
        valid amount of enabled repositories

    :CaseImportance: Critical
    """
    # No repos should be enabled by default
    result = target_sat.cli.RepositorySet.available_repositories(params['avail']['id'])
    assert len(match_repos(result, params['match']['enabled'])) == 0

    # Enable repo from Repository Set
    target_sat.cli.RepositorySet.enable(params['enable']['id'])

    # Only 1 repo should be enabled, and it should match the arch and releasever
    result = target_sat.cli.RepositorySet.available_repositories(params['avail']['name'])
    assert len(match_repos(result, params['match']['enabled'])) == 1

    # Enable one more repo
    target_sat.cli.RepositorySet.enable(params['enable']['arch_2'])

    # 2 repos should be enabled
    result = target_sat.cli.RepositorySet.available_repositories(params['avail']['label'])
    assert len(match_repos(result, params['match']['enabled'])) == 2

    # Disable one repo
    target_sat.cli.RepositorySet.disable(params['enable']['id'])

    # There should remain only 1 enabled repo
    result = target_sat.cli.RepositorySet.available_repositories(params['avail']['id'])
    assert len(match_repos(result, params['match']['enabled'])) == 1

    # Disable the last enabled repo
    target_sat.cli.RepositorySet.disable(params['enable']['arch_2'])

    # There should be no enabled repos
    result = target_sat.cli.RepositorySet.available_repositories(params['avail']['id'])
    assert len(match_repos(result, params['match']['enabled'])) == 0


@pytest.mark.parametrize('act_by', ['name', 'label', 'ids'])
def test_positive_enable_disable_by_param(act_by, params, target_sat):
    """Enable and disable repo from reposet by name, label and id (parametrized).

    :id: 6e4817dc-8d05-4296-b47b-78cbb8c68c6b

    :expectedresults: Repository was enabled and disabled.

    :CaseImportance: Critical
    """
    target_sat.cli.RepositorySet.enable(params['enable'][act_by])
    result = target_sat.cli.RepositorySet.available_repositories(params['avail'][act_by])
    assert len(match_repos(result, params['match']['enabled_arch_rel'])) == 1

    target_sat.cli.RepositorySet.disable(params['enable'][act_by])
    result = target_sat.cli.RepositorySet.available_repositories(params['avail'][act_by])
    assert len(match_repos(result, params['match']['enabled'])) == 0
