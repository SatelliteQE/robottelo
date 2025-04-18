"""Test class for Custom Sync UI

:Requirement: Sync

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    PRDS,
    REPO_TYPE,
    REPOS,
    REPOSET,
)
from robottelo.constants.repos import FEDORA_OSTREE_REPO


@pytest.fixture(scope='module')
def module_org(module_target_sat):
    return module_target_sat.api.Organization().create()


@pytest.fixture(scope='module')
def module_custom_product(module_org, module_target_sat):
    return module_target_sat.api.Product(organization=module_org).create()


@pytest.mark.run_in_one_thread
@pytest.mark.upgrade
def test_positive_sync_rh_repos(session, target_sat, module_sca_manifest_org):
    """Create Content RedHat Sync with two repos.

    :id: e30f6509-0b65-4bcc-a522-b4f3089d3911

    :expectedresults: Sync procedure for RedHat Repos is successful
    """
    repo_paths = []
    for key in ['rhsc8', 'rhsc9']:
        target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=module_sca_manifest_org.id,
            reposet=REPOS[key]['reposet'],
            product=REPOS[key]['product'],
            repo=REPOS[key]['name'],
            releasever=REPOS[key]['version'],
        )
        repo_paths.append((REPOS[key]['product'], REPOS[key]['name']))
    with session:
        session.organization.select(org_name=module_sca_manifest_org.name)
        results = session.sync_status.synchronize(repo_paths)
        assert len(results) == len(repo_paths)
        assert all([result == 'Syncing Complete.' for result in results])


@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.stubbed
def test_positive_sync_custom_ostree_repo(session, module_custom_product, module_target_sat):
    """Create custom ostree repository and sync it.

    :id: e4119b9b-0356-4661-a3ec-e5807224f7d2

    :expectedresults: ostree repo should be synced successfully

    :customerscenario: true

    :BZ: 1625783
    """
    repo = module_target_sat.api.Repository(
        content_type='ostree',
        url=FEDORA_OSTREE_REPO,
        product=module_custom_product,
        unprotected=False,
    ).create()
    with session:
        results = session.sync_status.synchronize([(module_custom_product.name, repo.name)])
        assert len(results) == 1
        assert results[0] == 'Syncing Complete.'


@pytest.mark.run_in_one_thread
@pytest.mark.upgrade
@pytest.mark.stubbed
def test_positive_sync_rh_ostree_repo(session, target_sat, module_sca_manifest_org):
    """Sync CDN based ostree repository.

    :id: 4d28fff0-5fda-4eee-aa0c-c5af02c31de5

    :steps:
        1. Import a valid manifest
        2. Enable the OStree repo and sync it

    :customerscenario: true

    :expectedresults: ostree repo should be synced successfully from CDN

    :BZ: 1625783
    """
    target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=None,
        org_id=module_sca_manifest_org.id,
        product=PRDS['rhah'],
        repo=REPOS['rhaht']['name'],
        reposet=REPOSET['rhaht'],
        releasever=None,
    )
    with session:
        session.organization.select(org_name=module_sca_manifest_org.name)
        results = session.sync_status.synchronize([(PRDS['rhah'], REPOS['rhaht']['name'])])
        assert len(results) == 1
        assert results[0] == 'Syncing Complete.'


@pytest.mark.upgrade
def test_positive_sync_docker_via_sync_status(session, module_org, module_target_sat):
    """Create custom docker repo and sync it via the sync status page.

    :id: 00b700f4-7e52-48ed-98b2-e49b3be102f2

    :expectedresults: Sync procedure for specific docker repository is
        successful
    """
    product = module_target_sat.api.Product(organization=module_org).create()
    repo_name = gen_string('alphanumeric')
    with session:
        session.repository.create(
            product.name,
            {
                'name': repo_name,
                'repo_type': REPO_TYPE['docker'],
                'repo_content.upstream_url': settings.container.rh.registry_hub,
                'repo_content.upstream_repo_name': settings.container.docker.repo_upstream_name,
                'repo_content.upstream_username': settings.subscription.rhn_username,
                'repo_content.upstream_password': settings.subscription.rhn_password,
            },
        )
        assert session.repository.search(product.name, repo_name)[0]['Name'] == repo_name
        result = session.sync_status.synchronize([(product.name, repo_name)])
        assert result[0] == 'Syncing Complete.'


def test_sync_active_only(target_sat, function_sca_manifest_org):
    """Ensure the Active Only check-box works as expected.

    :id: ebffc8d4-c3c3-40fe-a1f5-85148886cc35

    :steps:
        1. Create two repositories.
        2. Ensure none of them is displayed when Active Only is selected, both otherwise.
        3. Start syncing one of them asynchronously.
        4. Ensure only the syncing repository is displayed when Active Only is selected.
        5. Wait until the sync finish.
        6. Ensure none of the repos is displayed when Active Only is selected, both otherwise.

    :expectedresults: Only the repos under active sync are displayed when Active Only is selected.

    :Verifies: SAT-30291

    :customerscenario: true

    """
    # Create two repositories.
    for key in ['rhel9_aps', 'rhel9_bos']:
        prod, ver, arch, name = (
            REPOS['kickstart'][key]['product'],
            REPOS['kickstart'][key]['version'],
            'noarch',
            REPOS['kickstart'][key]['name'],
        )
        rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=function_sca_manifest_org.id,
            reposet=REPOS['kickstart'][key]['reposet'],
            product=prod,
            repo=name,
            releasever=ver,
        )
        repo = target_sat.api.Repository(id=rh_repo_id).read()

    with target_sat.ui_session() as session:
        session.organization.select(org_name=function_sca_manifest_org.name)

        # Ensure none of them is displayed when Active Only is selected, both otherwise.
        res = session.sync_status.read(active_only=True)
        assert len(res['table']) == 0
        res = session.sync_status.read(active_only=False)
        assert len(res['table'][prod][ver][arch]) == 2
        assert name in res['table'][prod][ver][arch]

        # Start syncing one of them asynchronously.
        res = session.sync_status.synchronize([(prod, ver, arch, name)], synchronous=False)

        # Ensure only the syncing repository is displayed when Active Only is selected.
        res = session.sync_status.read(active_only=True)
        assert len(res['table'][prod][ver][arch]) == 1
        assert name in res['table'][prod][ver][arch]

        # Wait until the sync finish.
        target_sat.wait_for_tasks(
            search_query='Actions::Katello::Repository::Sync'
            f' and organization_id = {function_sca_manifest_org.id}'
            f' and resource_id = {repo.id}'
            ' and resource_type = Katello::Repository',
            max_tries=12,
            search_rate=10,
        )
        session.browser.refresh()

        # Ensure none of the repos is displayed when Active Only is selected, both otherwise.
        res = session.sync_status.read(active_only=True)
        assert len(res['table']) == 0
        res = session.sync_status.read(active_only=False)
        assert len(res['table'][prod][ver][arch]) == 2
