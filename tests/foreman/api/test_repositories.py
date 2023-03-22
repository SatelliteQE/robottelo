"""Unit tests for the new ``repositories`` paths.

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Repositories

:team: Phoenix-content

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
from nailgun import entities
from nailgun.entity_mixins import call_entity_method_with_timeout
from requests.exceptions import HTTPError

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import MIRRORING_POLICIES
from robottelo.utils.datafactory import parametrized


@pytest.mark.skip_if_open('BZ:2137950')
@pytest.mark.tier1
def test_negative_disable_repository_with_cv(module_entitlement_manifest_org, target_sat):
    """Attempt to disable a Repository that is published in a Content View

    :id: e521a7a4-2502-4fe2-b297-a13fc99e679b

    :Steps:
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

    :Steps:
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

    :Steps:
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
def test_positive_sync_kickstart_repo(self, module_entitlement_manifest_org, target_sat):
    """No encoding gzip errors on kickstart repositories
    sync.

    :id: dbdabc0e-583c-4186-981a-a02844f90412

    :expectedresults: No encoding gzip errors present in /var/log/messages.

    :CaseLevel: Integration

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
        org_id=module_entitlement_manifest_org.id,
        product=constants.REPOS['kickstart'][distro]['product'],
        reposet=constants.REPOSET['kickstart'][distro],
        repo=constants.REPOS['kickstart'][distro]['name'],
        releasever=constants.REPOS['kickstart'][distro]['version'],
    )
    rh_repo = entities.Repository(id=rh_repo_id).read()
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
