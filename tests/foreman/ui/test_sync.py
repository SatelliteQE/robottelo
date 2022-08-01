"""Test class for Custom Sync UI

:Requirement: Sync

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Repositories

:Assignee: chiggins

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import CONTAINER_UPSTREAM_NAME
from robottelo.constants import DISTRO_RHEL6
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import PRDS
from robottelo.constants import REPO_TYPE
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants.repos import FEDORA_OSTREE_REPO


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_custom_product(module_org):
    return entities.Product(organization=module_org).create()


@pytest.fixture(scope='module')
def module_org_with_manifest():
    org = entities.Organization().create()
    manifests.upload_manifest_locked(org.id)
    return org


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_sync_custom_repo(session, module_custom_product):
    """Create Content Custom Sync with minimal input parameters

    :id: 00fb0b04-0293-42c2-92fa-930c75acee89

    :expectedresults: Sync procedure is successful

    :CaseImportance: Critical
    """
    repo = entities.Repository(url=settings.repos.yum_1.url, product=module_custom_product).create()
    with session:
        results = session.sync_status.synchronize([(module_custom_product.name, repo.name)])
        assert len(results) == 1
        assert results[0] == 'Syncing Complete.'


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_sync_rh_repos(session, target_sat, module_org_with_manifest):
    """Create Content RedHat Sync with two repos.

    :id: e30f6509-0b65-4bcc-a522-b4f3089d3911

    :expectedresults: Sync procedure for RedHat Repos is successful

    :CaseLevel: Integration
    """
    repos = (
        target_sat.cli_factory.SatelliteCapsuleRepository(cdn=True),
        target_sat.cli_factory.RHELCloudFormsTools(cdn=True),
    )
    distros = [DISTRO_RHEL7, DISTRO_RHEL6]
    repo_collections = [
        target_sat.cli_factory.RepositoryCollection(distro=distro, repositories=[repo])
        for distro, repo in zip(distros, repos)
    ]
    for repo_collection in repo_collections:
        repo_collection.setup(module_org_with_manifest.id, synchronize=False)
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
        session.organization.select(org_name=module_org_with_manifest.name)
        results = session.sync_status.synchronize(repo_paths)
        assert len(results) == len(repo_paths)
        assert all([result == 'Syncing Complete.' for result in results])


@pytest.mark.skip_if_open("BZ:1625783")
@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_sync_custom_ostree_repo(session, module_custom_product):
    """Create custom ostree repository and sync it.

    :id: e4119b9b-0356-4661-a3ec-e5807224f7d2

    :expectedresults: ostree repo should be synced successfully

    :customerscenario: true

    :CaseLevel: Integration

    :BZ: 1625783
    """
    repo = entities.Repository(
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
def test_positive_sync_rh_ostree_repo(session, module_org_with_manifest):
    """Sync CDN based ostree repository.

    :id: 4d28fff0-5fda-4eee-aa0c-c5af02c31de5

    :Steps:
        1. Import a valid manifest
        2. Enable the OStree repo and sync it

    :customerscenario: true

    :expectedresults: ostree repo should be synced successfully from CDN

    :CaseLevel: Integration

    :BZ: 1625783
    """
    enable_rhrepo_and_fetchid(
        basearch=None,
        org_id=module_org_with_manifest.id,
        product=PRDS['rhah'],
        repo=REPOS['rhaht']['name'],
        reposet=REPOSET['rhaht'],
        releasever=None,
    )
    with session:
        session.organization.select(org_name=module_org_with_manifest.name)
        results = session.sync_status.synchronize([(PRDS['rhah'], REPOS['rhaht']['name'])])
        assert len(results) == 1
        assert results[0] == 'Syncing Complete.'


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_sync_docker_via_sync_status(session, module_org):
    """Create custom docker repo and sync it via the sync status page.

    :id: 00b700f4-7e52-48ed-98b2-e49b3be102f2

    :expectedresults: Sync procedure for specific docker repository is
        successful

    :CaseLevel: Integration
    """
    product = entities.Product(organization=module_org).create()
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
