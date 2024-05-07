"""Capsule-Content related tests, which require destructive Satellite

:Requirement: Capsule-Content

:CaseAutomation: Automated

:CaseComponent: Capsule-Content

:team: Phoenix-content

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
import pytest

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
        basearch=constants.DEFAULT_ARCHITECTURE,
        org_id=function_entitlement_manifest_org.id,
        product=constants.REPOS['rhscl7']['product'],
        repo=constants.REPOS['rhscl7']['name'],
        reposet=constants.REPOSET['rhscl7'],
        releasever=constants.REPOS['rhscl7']['releasever'],
    )
    repo = target_sat.api.Repository(id=repo_id).read()
    repo.sync(timeout='60m')

    cv = target_sat.publish_content_view(function_entitlement_manifest_org, repo)

    for _ in range(4):
        copy_id = target_sat.api.ContentView(id=cv.id).copy(data={'name': gen_alpha()})['id']
        copy_cv = target_sat.api.ContentView(id=copy_id).read()
        copy_cv.publish()

    proxy = large_capsule_configured.nailgun_smart_proxy.read()
    proxy.download_policy = 'immediate'
    proxy.update(['download_policy'])

    nailgun_capsule = large_capsule_configured.nailgun_capsule
    lce = target_sat.api.LifecycleEnvironment(
        organization=function_entitlement_manifest_org
    ).search(query={'search': f'name={constants.ENVIRONMENT}'})[0]
    nailgun_capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
    result = nailgun_capsule.content_lifecycle_environments()
    assert len(result['results']) == 1
    assert result['results'][0]['id'] == lce.id
    sync_status = nailgun_capsule.content_sync(timeout='90m')
    assert sync_status['result'] == 'success', 'Capsule sync task failed.'


@pytest.mark.tier4
@pytest.mark.skip_if_not_set('capsule')
def test_positive_sync_without_deadlock_after_rpm_trim_changelog(
    target_sat, capsule_configured, function_entitlement_manifest_org
):
    """Promote a CV published with larger repos into multiple LCEs, assign LCEs to blank Capsule.
    Assert that the sync task succeeds and no deadlock happens.

    :id: 91c6eec9-a582-46ea-9898-bdcaebcea2f1

    :setup:
        1. Blank external capsule which is not synced yet, running with 4 & more pulpcore-workers

    :steps:
        1. Sync a few large repositories to the Satellite.
        2. Create a Content View, add the repository and publish it.
        3. Promote it to 10+ LCEs and assign them to Capsule
        4. Sync the Capsule
        5. pulpcore-manager rpm-trim-changelogs --changelog-limit x
        6. Sync Capsule again and verify no deadlocks occurs.
        7. Repeat step 5 with a lesser changelog limit and step 6 again

    :expectedresults:
        1. Sync passes without deadlock.

    :customerscenario: true

    :BZ: 2170535, 2218661
    """
    org = function_entitlement_manifest_org
    rh_repos = []
    tasks = []
    LCE_COUNT = 10
    for name in ['rhel8_bos', 'rhel8_aps']:
        rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=org.id,
            product=constants.REPOS[name]['product'],
            repo=constants.REPOS[name]['name'],
            reposet=constants.REPOS[name]['reposet'],
            releasever=constants.REPOS[name]['releasever'],
        )
        # Sync step because repo is not synced by default
        rh_repo = target_sat.api.Repository(id=rh_repo_id).read()
        task = rh_repo.sync(synchronous=False)
        tasks.append(task)
        rh_repos.append(rh_repo)
    for task in tasks:
        target_sat.wait_for_tasks(
            search_query=(f'id = {task["id"]}'),
            poll_timeout=2500,
        )
        task_status = target_sat.api.ForemanTask(id=task['id']).poll()
        assert task_status['result'] == 'success'

    cv = target_sat.publish_content_view(org, rh_repos)
    cvv = cv.version[0].read()
    nailgun_capsule = capsule_configured.nailgun_capsule

    for i in range(LCE_COUNT):
        lce = target_sat.api.LifecycleEnvironment(name=f'lce{i}', organization=org).create()
        cvv.promote(data={'environment_ids': lce.id, 'force': False})
        nailgun_capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})

    result = Box(nailgun_capsule.content_lifecycle_environments())
    assert len(result.results) == LCE_COUNT
    # Verify all LCE have a CV promoted
    assert [env.content_views[0].name for env in result.results].count(cv.name) == LCE_COUNT

    sync_status = nailgun_capsule.content_sync(timeout='60m')
    assert sync_status['result'] == 'success', 'Capsule sync task failed'

    # Run rpm-trim-changelogs with changelog-limit below 10 then again sync capsule
    # and repeat again with changelog-limit below it to make sure deadlock
    pulp_cmd = (
        'sudo -u pulp PULP_SETTINGS="/etc/pulp/settings.py" '
        '/usr/bin/pulpcore-manager rpm-trim-changelogs --changelog-limit '
    )
    for limit in range(9, 0, -1):
        result = target_sat.execute(f'{pulp_cmd}{limit}')
        assert f'Trimmed changelogs for {cvv.package_count} packages' in result.stdout
        target_sat.cli.ContentView.version_republish_repositories({'id': cvv.id, 'force': 'true'})

        sync_status = nailgun_capsule.content_sync(timeout='60m')
        assert sync_status['result'] == 'success', 'Capsule sync task failed'

        # Verify no deadlock detected in the postgres logs and pulp/syslogs
        day = target_sat.execute('date').stdout[:3]
        check_log_files = [f'/var/lib/pgsql/data/log/postgresql-{day}.log', '/var/log/messages']
        for file in check_log_files:
            assert capsule_configured.execute(f'grep -i "deadlock detected" {file}').status
