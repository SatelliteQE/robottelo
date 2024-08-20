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
    CONTAINER_REGISTRY_HUB,
    CONTAINER_UPSTREAM_NAME,
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
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_sync_rh_repos(session, target_sat, module_entitlement_manifest_org):
    """Create Content RedHat Sync with two repos.

    :id: e30f6509-0b65-4bcc-a522-b4f3089d3911

    :expectedresults: Sync procedure for RedHat Repos is successful
    """
    repos = (
        target_sat.cli_factory.SatelliteCapsuleRepository(cdn=True),
        target_sat.cli_factory.RHELCloudFormsTools(cdn=True),
    )
    distros = ['rhel6', 'rhel7']
    repo_collections = [
        target_sat.cli_factory.RepositoryCollection(distro=distro, repositories=[repo])
        for distro, repo in zip(distros, repos, strict=True)
    ]
    for repo_collection in repo_collections:
        repo_collection.setup(module_entitlement_manifest_org.id, synchronize=False)
    repo_paths = [
        (
            repo.repo_data['product'],
            repo.repo_data.get('releasever'),
            repo.repo_data.get('arch'),
            repo.repo_data['name'],
        )
        for repo in repos
    ]
    with session:
        session.organization.select(org_name=module_entitlement_manifest_org.name)
        results = session.sync_status.synchronize(repo_paths)
        assert len(results) == len(repo_paths)
        assert all([result == 'Syncing Complete.' for result in results])


@pytest.mark.skip_if_open("BZ:1625783")
@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
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
@pytest.mark.skip_if_open("BZ:1625783")
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_sync_rh_ostree_repo(session, target_sat, module_entitlement_manifest_org):
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
        org_id=module_entitlement_manifest_org.id,
        product=PRDS['rhah'],
        repo=REPOS['rhaht']['name'],
        reposet=REPOSET['rhaht'],
        releasever=None,
    )
    with session:
        session.organization.select(org_name=module_entitlement_manifest_org.name)
        results = session.sync_status.synchronize([(PRDS['rhah'], REPOS['rhaht']['name'])])
        assert len(results) == 1
        assert results[0] == 'Syncing Complete.'


@pytest.mark.tier2
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
                'repo_content.upstream_url': CONTAINER_REGISTRY_HUB,
                'repo_content.upstream_repo_name': CONTAINER_UPSTREAM_NAME,
            },
        )
        assert session.repository.search(product.name, repo_name)[0]['Name'] == repo_name
        result = session.sync_status.synchronize([(product.name, repo_name)])
        assert result[0] == 'Syncing Complete.'
