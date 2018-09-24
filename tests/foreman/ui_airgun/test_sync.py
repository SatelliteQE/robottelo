"""Test class for Custom Sync UI

:Requirement: Sync

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DISTRO_RHEL6, DISTRO_RHEL7,
    FAKE_1_YUM_REPO,
    FEDORA23_OSTREE_REPO,
    REPOS,
    REPOSET,
    PRDS,
)
from robottelo.decorators import (
    fixture,
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    tier2,
    upgrade,
)
from robottelo.decorators.host import skip_if_os
from robottelo.products import (
    RepositoryCollection,
    RHELCloudFormsTools,
    SatelliteCapsuleRepository,
)


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_custom_product(module_org):
    return entities.Product(organization=module_org).create()


@fixture(scope='module')
def org_manifest(module_org):
    manifests.upload_manifest_locked(module_org.id)


@tier2
def test_positive_sync_custom_repo(session, module_org, module_custom_product):
    """Create Content Custom Sync with minimal input parameters

    :id: 00fb0b04-0293-42c2-92fa-930c75acee89

    :expectedresults: Sync procedure is successful

    :CaseImportance: Critical
    """
    repo = entities.Repository(
        url=FAKE_1_YUM_REPO, product=module_custom_product).create()
    with session:
        session.organization.select(org_name=module_org.name)
        results = session.sync_status.synchronize([
            (module_custom_product.name, repo.name)])
        assert len(results) == 1
        assert results[0] == 'Syncing Complete.'


@run_in_one_thread
@run_only_on('sat')
@skip_if_not_set('fake_manifest')
@tier2
@upgrade
def test_positive_sync_rh_repos(session, module_org, org_manifest):
    """Create Content RedHat Sync with two repos.

    :id: e30f6509-0b65-4bcc-a522-b4f3089d3911

    :expectedresults: Sync procedure for RedHat Repos is successful

    :CaseLevel: Integration
    """
    repos = (
        SatelliteCapsuleRepository(cdn=True),
        RHELCloudFormsTools(cdn=True)
    )
    distros = [DISTRO_RHEL7, DISTRO_RHEL6]
    repo_collections = [
        RepositoryCollection(distro=distro, repositories=[repo])
        for distro, repo in zip(distros, repos)
    ]
    for repo_collection in repo_collections:
        repo_collection.setup(module_org.id, synchronize=False)
    repo_paths = []
    for repo in repos:
        if repo.repo_data.get('releasever'):
            repo_paths.append((
                repo.repo_data['product'],
                repo.repo_data['releasever'],
                repo.repo_data.get('arch', DEFAULT_ARCHITECTURE),
                repo.repo_data['name'],
             ))
        else:
            repo_paths.append(
                (repo.repo_data['product'], repo.repo_data['name']))
    with session:
        session.organization.select(org_name=module_org.name)
        results = session.sync_status.synchronize(repo_paths)
        assert len(results) == len(repo_paths)
        assert all([result == 'Syncing Complete.' for result in results])


@run_only_on('sat')
@skip_if_os('RHEL6')
@tier2
@upgrade
def test_positive_sync_custom_ostree_repo(
        session, module_org, module_custom_product):
    """Create custom ostree repository and sync it.

    :id: e4119b9b-0356-4661-a3ec-e5807224f7d2

    :expectedresults: ostree repo should be synced successfully

    :CaseLevel: Integration
    """
    repo = entities.Repository(
        content_type='ostree',
        url=FEDORA23_OSTREE_REPO,
        product=module_custom_product,
        unprotected=False,
    ).create()
    with session:
        session.organization.select(org_name=module_org.name)
        results = session.sync_status.synchronize([
            (module_custom_product.name, repo.name)])
        assert len(results) == 1
        assert results[0] == 'Syncing Complete.'


@run_only_on('sat')
@skip_if_os('RHEL6')
@skip_if_not_set('fake_manifest')
@tier2
@upgrade
def test_positive_sync_rh_ostree_repo(session, module_org, org_manifest):
    """Sync CDN based ostree repository.

    :id: 4d28fff0-5fda-4eee-aa0c-c5af02c31de5

    :Steps:
        1. Import a valid manifest
        2. Enable the OStree repo and sync it

    :expectedresults: ostree repo should be synced successfully from CDN

    :CaseLevel: Integration
    """
    enable_rhrepo_and_fetchid(
        basearch=None,
        org_id=module_org.id,
        product=PRDS['rhah'],
        repo=REPOS['rhaht']['name'],
        reposet=REPOSET['rhaht'],
        releasever=None,
    )
    with session:
        session.organization.select(org_name=module_org.name)
        results = session.sync_status.synchronize([
            (PRDS['rhah'], REPOS['rhaht']['name'])])
        assert len(results) == 1
        assert results[0] == 'Syncing Complete.'
