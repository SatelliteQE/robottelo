"""Test class for PuppetModule CLI

:Requirement: Puppetmodule

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.config import settings
from robottelo.constants.repos import FAKE_0_PUPPET_REPO
from robottelo.constants.repos import FAKE_1_PUPPET_REPO


pytestmark = [
    pytest.mark.skipif(
        not settings.robottelo.REPOS_HOSTING_URL,
        reason="repos_hosting_url is not defined in robottelo.properties",
    )
]


@pytest.fixture(scope='module')
def module_setup(module_org):
    product = make_product({'organization-id': module_org.id})
    repo = make_repository(
        {
            'organization-id': module_org.id,
            'product-id': product['id'],
            'content-type': 'puppet',
            'url': FAKE_0_PUPPET_REPO,
        }
    )
    Repository.synchronize({'id': repo['id']})
    return {'org': module_org, 'product': product, 'repo': repo}


@pytest.mark.tier1
def test_positive_list(module_setup):
    """Check if puppet-module list retrieves puppet-modules of
    the given org

    :id: 77635e70-19e7-424d-9c89-ec5dbe91de75

    :expectedresults: Puppet-modules are retrieved for the given org

    :BZ: 1283173

    :CaseImportance: Critical
    """
    result = PuppetModule.list({'organization-id': module_setup['org'].id})
    # There are 4 puppet modules in the test puppet-module url
    assert len(result) == 4


@pytest.mark.tier1
def test_positive_info(module_setup):
    """Check if puppet-module info retrieves info for the given
    puppet-module id

    :id: 8aaa9243-5e20-49d6-95ce-620cc1ba18dc

    :expectedresults: The puppet-module info is retrieved

    :CaseImportance: Critical
    """
    return_value = PuppetModule.list({'organization-id': module_setup['org'].id})
    for i in range(len(return_value)):
        result = PuppetModule.info({'id': return_value[i]['id']}, output_format='json')
        assert result['id'] == return_value[i]['id']


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_list_multiple_repos(module_setup):
    """Verify that puppet-modules list for specific repo is correct
    and does not affected by other repositories.

    :id: f36d25b3-2495-4e89-a1cf-e39d52762d95

    :expectedresults: Number of modules has not changed after a second repo
        was synced.

    :CaseImportance: Critical
    """
    # Verify that number of synced modules is correct
    repo1 = Repository.info({'id': module_setup['repo']['id']})
    repo_content_count = repo1['content-counts']['puppet-modules']
    modules_num = len(PuppetModule.list({'repository-id': repo1['id']}))
    assert repo_content_count == str(modules_num)
    # Create and sync second repo
    repo2 = make_repository(
        {
            'organization-id': module_setup['org'].id,
            'product-id': module_setup['product']['id'],
            'content-type': 'puppet',
            'url': FAKE_1_PUPPET_REPO,
        }
    )
    Repository.synchronize({'id': repo2['id']})
    # Verify that number of modules from the first repo has not changed
    assert modules_num == len(PuppetModule.list({'repository-id': repo1['id']}))
