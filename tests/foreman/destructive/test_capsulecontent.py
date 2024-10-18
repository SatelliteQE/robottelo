"""Capsule-Content related tests, which require destructive Satellite

:Requirement: Capsule-Content

:CaseAutomation: Automated

:CaseComponent: Capsule-Content

:team: Phoenix-content

:CaseImportance: High

"""

from datetime import datetime, timedelta

from box import Box
from fauxfactory import gen_alpha
import pytest

from robottelo import constants

pytestmark = [pytest.mark.destructive]


@pytest.mark.tier4
@pytest.mark.skip_if_not_set('capsule')
def test_positive_sync_without_deadlock(
    target_sat,
    large_capsule_configured,
    function_sca_manifest_org,
    function_published_cv,
):
    """Synchronize one bigger repo, published in multiple CVs, to a blank Capsule.
    Assert that the sync task(s) succeed and no deadlock happens.

    :id: 91c6eec9-a582-46ea-9898-bdcaebcea2f0

    :setup:
        1. A blank external capsule that has not been synced yet (!) with immediate download
           policy and running multiple (4 and more) pulpcore workers.

    :steps:
        1. Add one bigger repository to the Satellite.
        2. Create a Content View, add the repository and publish it.
        3. Create several copies of the CV and publish them.
        4. Add the Library environment to the Capsule.
        5. Synchronize the bigger repository.
        6. Capsule sync is triggered once repo sync is finished.

    :expectedresults:
        1. Sync passes without deadlock.
        2. Capsule Content counts match expected, added content from repository.

    :customerscenario: true

    :BZ: 2062526
    """
    rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=constants.DEFAULT_ARCHITECTURE,
        org_id=function_sca_manifest_org.id,
        product=constants.REPOS['rhel9_aps']['product'],
        repo=constants.REPOS['rhel9_aps']['name'],
        reposet=constants.REPOSET['rhel9_aps'],
        releasever=constants.REPOS['rhel9_aps']['releasever'],
    )
    repo = target_sat.api.Repository(id=rh_repo_id).read()
    # add large repo to cv and publish
    function_published_cv.repository = [repo]
    function_published_cv.update(['repository'])
    task_query = (
        f'Metadata generate repository "{repo.name}";'
        f' product "{constants.REPOS["rhel9_aps"]["product"]}";'
        f' organization "{function_sca_manifest_org.name}"'
    )
    # wait_for repo metadata task, prior to publish
    target_sat.wait_for_tasks(
        search_query=task_query,
        search_rate=2,
        max_tries=10,
    )
    function_published_cv = function_published_cv.read()
    function_published_cv.publish()
    # copies of content view with added repo
    for _ in range(4):
        copy_id = target_sat.api.ContentView(id=function_published_cv.id).copy(
            data={'name': gen_alpha()}
        )['id']
        copy_cv = target_sat.api.ContentView(id=copy_id).read()
        copy_cv.publish()

    proxy = large_capsule_configured.nailgun_smart_proxy.read()
    proxy.download_policy = 'immediate'
    proxy.update(['download_policy'])
    nailgun_capsule = large_capsule_configured.nailgun_capsule
    # Capsule set to use Library environment
    lce = target_sat.api.LifecycleEnvironment(organization=function_sca_manifest_org).search(
        query={'search': f'name={constants.ENVIRONMENT}'}
    )[0]
    nailgun_capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
    result = nailgun_capsule.content_lifecycle_environments()
    assert len(result['results']) == 1
    assert result['results'][0]['id'] == lce.id

    # Synchronize repository, Capsule Sync tasks triggered
    repo_sync = repo.sync(timeout='60m')
    assert (
        'Associating Content' in repo_sync['humanized']['output']
    ), f'Failed to add new content with repository sync:\n{repo_sync.read()}'
    # timestamp: to check capsule task(s) began, exclude priors
    # within 120 seconds of end of repo_sync
    timestamp = datetime.utcnow().replace(microsecond=0) - timedelta(seconds=120)
    repo_to_capsule_task = target_sat.wait_for_tasks(
        search_query=(
            'label=Actions::Katello::Repository::CapsuleSync' f' and started_at >= {timestamp}'
        ),
        search_rate=2,
        max_tries=60,  # in-progress within 120s
        poll_timeout=5400,  # 90m, total duration
    )
    assert len(repo_to_capsule_task) == 1
    repo_to_capsule_task = repo_to_capsule_task[0].read()
    capsule_sync_task = target_sat.wait_for_tasks(
        search_query=(
            f'"{nailgun_capsule.name}"'
            ' and label=Actions::Katello::CapsuleContent::Sync'
            f' and started_at >= {timestamp}'
        ),
        search_rate=2,
        max_tries=60,
        poll_timeout=5400,
    )
    assert len(capsule_sync_task) == 1
    capsule_sync_task = capsule_sync_task[0].read()
    nailgun_capsule = nailgun_capsule.read()
    # capsule content reflects expected counts, from synced rh repo in CVV
    repo = repo.read()
    updated_content = str(nailgun_capsule.content_counts()['content_view_versions'])
    assert f"'rpm': {repo.content_counts['rpm']}" in updated_content
    assert f"'erratum': {repo.content_counts['erratum']}" in updated_content
    assert f"'package_group': {repo.content_counts['package_group']}" in updated_content


@pytest.mark.tier4
@pytest.mark.skip_if_not_set('capsule')
def test_positive_sync_without_deadlock_after_rpm_trim_changelog(
    target_sat,
    capsule_configured,
    function_sca_manifest_org,
):
    """Promote a CV published with larger repos into multiple LCEs, assign LCEs to blank Capsule.
    Assert that the sync task succeeds and no deadlock happens.

    :id: 91c6eec9-a582-46ea-9898-bdcaebcea2f1

    :setup:
        1. Blank external capsule which is not synced yet, running with 4 & more pulpcore-workers

    :steps:
        1. Sync a few large repositories to the Satellite.
        2. Create a Content View, add the repository and publish it.
        3. Promote it to 10+ LCEs and assign them to Capsule.
        4. Sync the Capsule
        5. pulpcore-manager rpm-trim-changelogs --changelog-limit x
        6. Sync Capsule again and verify no deadlocks occurs.
        7. Repeat step 5 with a lesser changelog limit and step 6 again.

    :expectedresults:
        1. Sync passes without deadlock.

    :customerscenario: true

    :BZ: 2170535, 2218661
    """
    org = function_sca_manifest_org
    rh_repos = []
    tasks = []
    LCE_COUNT = 10
    for name in [
        'rhel9_bos',
        'rhsclient9',
        'rhel9_aps',
    ]:
        rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=org.id,
            product=constants.REPOS[name]['product'],
            repo=constants.REPOS[name]['name'],
            reposet=constants.REPOS[name]['reposet'],
            releasever=constants.REPOS[name]['releasever'],
        )
        rh_repo = target_sat.api.Repository(id=rh_repo_id).read()
        task = rh_repo.sync(synchronous=False)
        tasks.append(task)
        rh_repos.append(rh_repo)
    for task in tasks:
        target_sat.wait_for_tasks(
            search_query=(f'id = {task["id"]}'),
            poll_timeout=3600,
        )
        task_status = target_sat.api.ForemanTask(id=task['id']).poll()
        assert task_status['result'] == 'success'

    cv = target_sat.publish_content_view(org, rh_repos)
    cvv = cv.version[0]
    nailgun_capsule = capsule_configured.nailgun_capsule

    for i in range(LCE_COUNT):
        lce = target_sat.api.LifecycleEnvironment(name=f'lce{i}', organization=org).create()
        cvv.read().promote(data={'environment_ids': lce.read().id, 'force': False})
        nailgun_capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})

    result = Box(nailgun_capsule.content_lifecycle_environments())
    assert len(result.results) == LCE_COUNT
    # Verify all LCE have a CV promoted
    assert [env.content_views[0].name for env in result.results].count(cv.name) == LCE_COUNT

    sync_status = nailgun_capsule.content_sync(timeout='90m')
    assert sync_status['result'] == 'success', 'Capsule sync task failed'

    # Run rpm-trim-changelogs with changelog-limit below 10 then again sync capsule
    # and repeat again with changelog-limit below it to make sure deadlock
    pulp_cmd = (
        'sudo -u pulp PULP_SETTINGS="/etc/pulp/settings.py" '
        '/usr/bin/pulpcore-manager rpm-trim-changelogs --changelog-limit '
    )
    for limit in range(9, 0, -1):
        result = target_sat.execute(f'{pulp_cmd}{limit}')
        cvv = cvv.read()
        assert f'Trimmed changelogs for {cvv.package_count} packages' in result.stdout
        target_sat.cli.ContentView.version_republish_repositories({'id': cvv.id, 'force': 'true'})

        sync_status = nailgun_capsule.content_sync(timeout='90m')
        assert sync_status['result'] == 'success', 'Capsule sync task failed'

        # Verify no deadlock detected in the postgres logs and pulp/syslogs
        day = target_sat.execute('date').stdout[:3]
        check_log_files = [f'/var/lib/pgsql/data/log/postgresql-{day}.log', '/var/log/messages']
        for file in check_log_files:
            assert capsule_configured.execute(f'grep -i "deadlock detected" {file}').status
