"""Unit tests for the new ``repositories`` paths.

:Requirement: Repository

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: Critical

"""

from manifester import Manifester
from nailgun.entity_mixins import call_entity_method_with_timeout
import pytest
from requests.exceptions import HTTPError

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    MIRRORING_POLICIES,
    REPOS,
)
from robottelo.constants.repos import FAKE_ZST_REPO
from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.datafactory import parametrized


@pytest.mark.skip_if_open('BZ:2137950')
@pytest.mark.tier1
def test_negative_disable_repository_with_cv(module_entitlement_manifest_org, target_sat):
    """Attempt to disable a Repository that is published in a Content View

    :id: e521a7a4-2502-4fe2-b297-a13fc99e679b

    :steps:
        1. Enable and sync a RH Repo
        2. Create a Content View with Repository attached
        3. Publish Content View
        4. Attempt to disable the Repository

    :expectedresults: A message should be thrown saying you cannot disable the Repo
    """
    rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=constants.DEFAULT_ARCHITECTURE,
        org_id=module_entitlement_manifest_org.id,
        product=constants.PRDS['rhel8'],
        repo=constants.REPOS['rhst8']['name'],
        reposet=constants.REPOSET['rhst8'],
        releasever=None,
    )
    rh_repo = target_sat.api.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    cv = target_sat.api.ContentView(
        organization=module_entitlement_manifest_org, repository=[rh_repo_id]
    ).create()
    cv.publish()
    reposet = target_sat.api.RepositorySet(
        name=constants.REPOSET['rhst8'], product=rh_repo.product
    ).search()[0]
    data = {'basearch': 'x86_64', 'releasever': '7Server', 'product_id': rh_repo.product.id}
    with pytest.raises(HTTPError) as error:
        reposet.disable(data=data)
        # assert error.value.response.status_code == 500
    assert (
        'Repository cannot be deleted since it has already been '
        'included in a published Content View' in error.value.response.text
    )


@pytest.mark.tier1
def test_positive_update_repository_metadata(module_org, target_sat):
    """Update a Repositories url and check that the rpm content counts are different.
        This process will modify the publication of a repo(metadata).

    :id: 6fe7bb3f-1640-4904-a223-b4764534afe8

    :steps:
        1. Create a Product and Yum Repository
        2. Sync the Repository and returns its content_counts for rpm
        3. Update the url to a different Repo and re-sync the Repository
        4. assert that the rpm counts have changed

    :expectedresults: Repository rpm counts are different, confirming metadata was updated
    """
    product = target_sat.api.Product(organization=module_org).create()
    repo = target_sat.api.Repository(
        content_type='yum', product=product, url=settings.repos.module_stream_1.url
    ).create()
    repo.sync()
    content_counts_before_update = (
        target_sat.api.Repository(name=repo.name)
        .search(query={'organization_id': module_org.id})[0]
        .content_counts['rpm']
    )
    repo.url = settings.repos.module_stream_0.url
    repo.update(['url'])
    repo.sync()
    content_counts_after_update = (
        target_sat.api.Repository(name=repo.name)
        .search(query={'organization_id': module_org.id})[0]
        .content_counts['rpm']
    )
    assert content_counts_before_update != content_counts_after_update


@pytest.mark.parametrize(
    'module_repo_options',
    **parametrized(
        [
            {
                'content_type': 'yum',
                'mirroring_policy': policy,
                'url': settings.repos.mock_service_repo.rhel7,
            }
            for policy in MIRRORING_POLICIES
        ]
    ),
    indirect=True,
)
def test_positive_epel_repositories_with_mirroring_policy(
    module_org, module_repo_options, module_repo, target_sat
):
    """Create an Epel Repository with different mirroring policies set and confirm content exist

    :id: 5c4e0ba4-4486-4eaf-b6ad-62831b7353a4

    :steps:
        1. Create a Epel repository with mirroring_policy set
        2. Sync the Repository and return its content_counts for rpm
        3. Assert content was synced and mirroring policy type is correct

    :expectedresults: All Epel repositories with mirroring policy options set should have content
    """
    module_repo.sync()
    repodata = target_sat.api.Repository(name=module_repo.name).search(
        query={'organization_id': module_org.id}
    )[0]
    assert repodata.content_counts['rpm'] != 0
    assert module_repo_options['mirroring_policy'] == repodata.mirroring_policy


@pytest.mark.tier4
def test_positive_sync_kickstart_repo(module_sca_manifest_org, target_sat):
    """No encoding gzip errors on kickstart repositories
    sync.

    :id: dbdabc0e-583c-4186-981a-a02844f90412

    :expectedresults: No encoding gzip errors present in /var/log/messages.

    :customerscenario: true

    :steps:

        1. Sync a kickstart repository.
        2. After the repo is synced, change the download policy to
            immediate.
        3. Sync the repository again.
        4. Assert that no errors related to encoding gzip are present in
            /var/log/messages.
        5. Assert that sync was executed properly.

    :CaseComponent: Pulp

    :BZ: 1687801
    """
    distro = 'rhel8_bos'
    rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=module_sca_manifest_org.id,
        product=constants.REPOS['kickstart'][distro]['product'],
        reposet=constants.REPOS['kickstart'][distro]['reposet'],
        repo=constants.REPOS['kickstart'][distro]['name'],
        releasever=constants.REPOS['kickstart'][distro]['version'],
    )
    rh_repo = target_sat.api.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    rh_repo.download_policy = 'immediate'
    rh_repo = rh_repo.update(['download_policy'])
    call_entity_method_with_timeout(rh_repo.sync, timeout=600)
    result = target_sat.execute(
        'grep pulp /var/log/messages | grep failed | grep encoding | grep gzip'
    )
    assert result.status == 1
    assert not result.stdout
    rh_repo = rh_repo.read()
    assert rh_repo.content_counts['package_group'] > 0
    assert rh_repo.content_counts['rpm'] > 0


def test_positive_sync_upstream_repo_with_zst_compression(
    module_org, module_product, module_target_sat
):
    """Sync upstream repo having zst compression and verify it succeeds.

    :id: 1eddff2a-b6b5-420b-a0e8-ba6a05c11ca4

    :expectedresults: Repo sync is successful and no zst type compression errors are present in /var/log/messages.

    :steps:

        1. Sync upstream repository having zst type compression.
        2. Assert that no errors related to compression type  are present in
            /var/log/messages.
        3. Assert that sync was executed properly.

    :BZ: 2241934

    :customerscenario: true
    """
    repo = module_target_sat.api.Repository(
        product=module_product, content_type='yum', url=FAKE_ZST_REPO
    ).create()
    assert repo.read().content_counts['rpm'] == 0
    sync = module_product.sync()
    assert sync['result'] == 'success'
    assert repo.read().content_counts['rpm'] > 0
    result = module_target_sat.execute(
        'grep pulp /var/log/messages | grep "Cannot detect compression type"'
    )
    assert result.status == 1


@pytest.mark.tier1
def test_negative_upload_expired_manifest(module_org, target_sat):
    """Upload an expired manifest and attempt to refresh it

    :id: d6e652d8-5f46-4d15-9191-d842466d45d0

    :steps:
        1. Upload a manifest
        2. Delete the Subscription Allocation on RHSM
        3. Attempt to refresh the manifest

    :expectedresults: Manifest refresh should fail and return error message
    """
    manifester = Manifester(manifest_category=settings.manifest.entitlement)
    manifest = manifester.get_manifest()
    target_sat.upload_manifest(module_org.id, manifest.content)
    manifester.delete_subscription_allocation()
    with pytest.raises(CLIReturnCodeError) as error:
        target_sat.cli.Subscription.refresh_manifest({'organization-id': module_org.id})
    assert (
        "The manifest doesn't exist on console.redhat.com. "
        "Please create and import a new manifest." in error.value.stderr
    )


@pytest.mark.tier1
def test_positive_multiple_orgs_with_same_repo(target_sat):
    """Test that multiple organizations with the same repository synced have matching metadata

    :id: 39cff8ea-969d-4b8f-9fb4-33b1ba768ff2

    :steps:
        1. Create multiple organizations
        2. Sync the same repository to each organization
        3. Assert that each repository from each organization contain the same content counts

    :expectedresults: Each repository in each organziation should have the same content counts
    """
    repos = []
    orgs = [target_sat.api.Organization().create() for _ in range(3)]
    for org in orgs:
        product = target_sat.api.Product(organization=org).create()
        repo = target_sat.api.Repository(
            content_type='yum', product=product, url=settings.repos.module_stream_1.url
        ).create()
        repo.sync()
        repo_counts = target_sat.api.Repository(id=repo.id).read().content_counts
        repos.append(repo_counts)
    assert repos[0] == repos[1] == repos[2]


def test_positive_sync_mulitple_large_repos(module_target_sat, module_entitlement_manifest_org):
    """Enable and bulk sync multiple large repositories

    :id: b51c4a3d-d532-4342-be61-e868f7c3a723

    :steps:
        1. Enabled multiple large Repositories
                Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs 8
                Red Hat Enterprise Linux 8 for x86_64 - BaseOS RPMs 8
                Red Hat Enterprise Linux 8 for x86_64 - AppStream Kickstart 8
                Red Hat Enterprise Linux 8 for x86_64 - BaseOS Kickstart 8
        2. Sync all four repositories at the same time
        3. Assert that the bulk sync succeeds

    :expectedresults: All repositories should sync with no errors

    :BZ: 2224031
    """
    repo_names = ['rhel8_bos', 'rhel8_aps']
    kickstart_names = ['rhel8_bos', 'rhel8_aps']
    for name in repo_names:
        rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=DEFAULT_ARCHITECTURE,
            org_id=module_entitlement_manifest_org.id,
            product=REPOS[name]['product'],
            repo=REPOS[name]['name'],
            reposet=REPOS[name]['reposet'],
            releasever=REPOS[name]['releasever'],
        )

    for name in kickstart_names:
        rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=module_entitlement_manifest_org.id,
            product=constants.REPOS['kickstart'][name]['product'],
            repo=constants.REPOS['kickstart'][name]['name'],
            reposet=constants.REPOS['kickstart'][name]['reposet'],
            releasever=constants.REPOS['kickstart'][name]['version'],
        )
    rh_repos = module_target_sat.api.Repository(id=rh_repo_id).read()
    rh_products = module_target_sat.api.Product(id=rh_repos.product.id).read()
    assert len(rh_products.repository) == 4
    res = module_target_sat.api.ProductBulkAction().sync(
        data={'ids': [rh_products.id]}, timeout=2000
    )
    assert res['result'] == 'success'


def test_positive_available_repositories_endpoint(module_sca_manifest_org, target_sat):
    """Attempt to hit the /available_repositories endpoint with no failures

    :id: f4c9d4a0-9a82-4f06-b772-b1f7e3f45e7d

    :steps:
        1. Enable a Red Hat Repository
        2. Attempt to hit the enpoint:
           GET /katello/api/repository_sets/:id/available_repositories
        3. Verify Actions::Katello::RepositorySet::ScanCdn task is run
        4. Verify there are no failures when scanning for repository


    :expectedresults: Actions::Katello::RepositorySet::ScanCdn task should succeed and
        not fail when scanning for repositories

    :customerscenario: true

    :BZ: 2030445
    """
    rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=constants.DEFAULT_ARCHITECTURE,
        org_id=module_sca_manifest_org.id,
        product=constants.REPOS['rhel7_extra']['product'],
        repo=constants.REPOS['rhel7_extra']['name'],
        reposet=constants.REPOS['rhel7_extra']['reposet'],
        releasever=None,
    )
    rh_repo = target_sat.api.Repository(id=rh_repo_id).read()
    product = target_sat.api.Product(id=rh_repo.product.id).read()
    reposet = target_sat.api.RepositorySet(
        name=constants.REPOSET['rhel7_extra'], product=product
    ).search()[0]
    touch_endpoint = target_sat.api.RepositorySet.available_repositories(reposet)
    assert touch_endpoint['total'] != 0
    results = target_sat.execute('tail -15 /var/log/foreman/production.log').stdout
    assert 'Actions::Katello::RepositorySet::ScanCdn' in results
    assert 'result: success' in results
    assert 'Failed at scanning for repository' not in results
