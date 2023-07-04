"""Capsule-Content related tests, which require destructive Satellite

:Requirement: Capsule-Content

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: Capsule-Content

:team: Phoenix-content

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_alpha

from robottelo import constants

pytestmark = [pytest.mark.destructive]


@pytest.mark.tier4
@pytest.mark.skip_if_not_set('capsule')
def test_positive_sync_without_deadlock(
    target_sat, large_capsule_configured, function_entitlement_manifest_org
):
    """Synchronize one bigger repo published in multiple CVs to a blank Capsule.
    Assert that the sync task succeeds and no deadlock happens.

    :id: 91c6eec9-a582-46ea-9898-bdcaebcea2f0

    :setup:
        1. A blank external capsule that has not been synced yet (!) with immediate download
           policy and running multiple (4 and more) pulpcore workers.

    :steps:
        1. Sync one bigger repository to the Satellite.
        2. Create a Content View, add the repository and publish it.
        3. Create several copies of the CV and publish them.
        4. Add the Library LCE to the Capsule.
        5. Sync the Capsule.

    :expectedresults:
        1. Sync passes without deadlock.

    :customerscenario: true

    :BZ: 2062526

    """
    # Note: As of now BZ#2122872 prevents us to use the originally intended RHEL7 repo because
    # of a memory leak causing Satellite OOM crash in this scenario. Therefore, for now we use
    # smaller RHSCL repo instead, which was also capable to hit the deadlock issue, regardless
    # the lower rpms count. When the BZ is fixed, reconsider upscale to RHEL7 repo or similar.
    repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=function_entitlement_manifest_org.id,
        product=constants.REPOS['rhscl7']['product'],
        repo=constants.REPOS['rhscl7']['name'],
        reposet=constants.REPOSET['rhscl7'],
        releasever=constants.REPOS['rhscl7']['releasever'],
    )
    repo = target_sat.api.Repository(id=repo_id).read()
    repo.sync(timeout='60m')

    cv = target_sat.publish_content_view(function_entitlement_manifest_org, repo)

    for i in range(4):
        copy_id = target_sat.api.ContentView(id=cv.id).copy(data={'name': gen_alpha()})['id']
        copy_cv = target_sat.api.ContentView(id=copy_id).read()
        copy_cv.publish()

    proxy = large_capsule_configured.nailgun_smart_proxy.read()
    proxy.download_policy = 'immediate'
    proxy.update(['download_policy'])

    lce = target_sat.api.LifecycleEnvironment(
        organization=function_entitlement_manifest_org
    ).search(query={'search': f'name={constants.ENVIRONMENT}'})[0]
    large_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
        data={'environment_id': lce.id}
    )
    result = large_capsule_configured.nailgun_capsule.content_lifecycle_environments()
    assert len(result['results']) == 1
    assert result['results'][0]['id'] == lce.id

    sync_status = large_capsule_configured.nailgun_capsule.content_sync(timeout='90m')
    assert sync_status['result'] == 'success', 'Capsule sync task failed.'
