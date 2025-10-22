"""Capsule-Content related tests, which require destructive Satellite

:Requirement: Capsule-Content

:CaseAutomation: Automated

:CaseComponent: Capsule-Content

:team: Artemis

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
import pytest

from robottelo import constants
from robottelo.config import settings

pytestmark = [pytest.mark.destructive]


@pytest.mark.skip_if_not_set('capsule')
def test_positive_sync_rpm_without_deadlock(
    target_sat,
    large_capsule_configured,
    function_sca_manifest_org,
):
    """Synchronize one bigger repo, published in multiple CVs, to a blank Capsule.
    Assert that the sync task(s) succeed and no deadlock happens.

    :id: 91c6eec9-a582-46ea-9898-bdcaebcea2f0

    :setup:
        1. A blank external capsule that has not been synced yet (!) with immediate download
           policy and running multiple (4 and more) pulpcore workers.

    :steps:
        1. Set immediate download policy for RH repos to avoid OOM on Capsule sync.
        2. Sync one bigger repository to the Satellite.
        3. Create a Content View, add the repository and publish it.
        4. Create several copies of the CV and publish them.
        5. Set immediate download policy to the Capsule.
        6. Add the Library environment to the Capsule.
        7. Synchronize the Capsule, ensure the sync task succeeded.
        8. Ensure no 'ShareLock' or 'deadlock' found in /var/log/messages.

    :expectedresults:
        1. Capsule sync succeeds.
        2. No deadlock nor sharelock found in logs.

    :customerscenario: true

    :BZ: 2062526
    """
    # Set immediate download policy for RH repos to avoid OOM on Capsule sync.
    target_sat.update_setting('default_redhat_download_policy', 'immediate')

    # Sync one bigger repository to the Satellite.
    rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=constants.DEFAULT_ARCHITECTURE,
        org_id=function_sca_manifest_org.id,
        product=constants.REPOS['rhel9_bos']['product'],
        repo=constants.REPOS['rhel9_bos']['name'],
        reposet=constants.REPOSET['rhel9_bos'],
        releasever=constants.REPOS['rhel9_bos']['releasever'],
    )
    repo = target_sat.api.Repository(id=rh_repo_id).read()
    repo.sync(timeout='60m')

    # Create a Content View, add the repository and publish it.
    cv = target_sat.publish_content_view(function_sca_manifest_org, repo)

    # Create several copies of the CV and publish them.
    for _ in range(7):
        copy_id = target_sat.api.ContentView(id=cv.id).copy(data={'name': gen_alpha()})['id']
        copy_cv = target_sat.api.ContentView(id=copy_id).read()
        copy_cv.publish()

    # Set immediate download policy to the Capsule.
    proxy = large_capsule_configured.nailgun_smart_proxy.read()
    proxy.download_policy = 'immediate'
    proxy.update(['download_policy'])

    # Add the Library environment to the Capsule.
    nailgun_capsule = large_capsule_configured.nailgun_capsule
    lce = target_sat.api.LifecycleEnvironment(organization=function_sca_manifest_org).search(
        query={'search': f'name={constants.ENVIRONMENT}'}
    )[0]
    nailgun_capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
    result = nailgun_capsule.content_lifecycle_environments()
    assert len(result['results']) == 1
    assert result['results'][0]['id'] == lce.id

    # Synchronize the Capsule, ensure the sync task succeeded.
    sync_status = nailgun_capsule.content_sync(timeout='90m')
    assert sync_status['result'] == 'success', f'Capsule sync task failed: {sync_status}'

    # Ensure no 'ShareLock' or 'deadlock' found in /var/log/messages.
    sharelock_check = large_capsule_configured.execute('grep -i "ShareLock" /var/log/messages')
    assert sharelock_check.status != 0, 'ShareLock detected in /var/log/messages'
    deadlock_check = large_capsule_configured.execute('grep -i "deadlock" /var/log/messages')
    assert deadlock_check.status != 0, 'Deadlock detected in /var/log/messages'


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


@pytest.mark.skip_if_not_set('capsule')
def test_sync_AC_without_deadlock(
    target_sat,
    capsule_configured,
    function_org,
    function_product,
):
    """Synchronize Ansible-Collection repository with multiple content views to capsule.
    Assert that the sync task succeeds and no deadlock happens.

    :id: ac38c045-7b4b-400c-8f23-f4ffc4a38f77

    :setup:
        1. A blank external capsule with immediate download policy.

    :steps:
        1. Create an Ansible-Collection repository and sync it.
        2. Create 5 lifecycle environments.
        3. Create 8 content views, add the repository and publish/promote to all LCEs.
        4. Assign all lifecycle environments to the capsule and trigger optimized sync.
        5. Ensure sync task succeeded and no 'ShareLock' or 'deadlock' found in /var/log/messages.

    :expectedresults:
        1. Sync passes without deadlock.

    :customerscenario: true

    :Verifies: SAT-34271

    """
    # Set capsule to immediate download policy
    proxy = capsule_configured.nailgun_smart_proxy.read()
    proxy.download_policy = 'immediate'
    proxy.update(['download_policy'])

    # 1. Create Ansible-Collection repository and sync it
    requirements = '''
    ---
    collections:
    - name: ansible.eda
    - name: check_point.mgmt
    - name: ansible.platform
    - name: redhat.satellite
    '''
    repo = target_sat.api.Repository(
        content_type='ansible_collection',
        ansible_collection_requirements=requirements,
        product=function_product,
        url=settings.ansible_hub.url,
        ansible_collection_auth_token=settings.ansible_hub.token,
        ansible_collection_auth_url=settings.ansible_hub.sso_url,
    ).create()
    repo_sync = repo.sync()
    assert repo_sync['result'] == 'success', f'Repository sync failed: {repo_sync}'
    repo = repo.read()
    assert repo.content_counts['ansible_collection'] > 75, (
        'Insufficient collections count in testing repo'
    )

    # 2. Create 5 lifecycle environments
    lces = [target_sat.api.LifecycleEnvironment(name='LCE-0', organization=function_org).create()]
    for i in range(1, 5):
        lce = target_sat.api.LifecycleEnvironment(
            name=f'LCE-{i}', organization=function_org, prior=lces[-1].id
        ).create()
        lces.append(lce)

    # 3. Create 8 content views, add repository and publish/promote to all LCEs
    content_views = []
    for i in range(8):
        cv = target_sat.api.ContentView(
            name=f'CV-{i}', organization=function_org, repository=[repo]
        ).create()

        cv.publish()
        cv = cv.read()
        cvv = cv.version[0]
        cvv.promote(data={'environment_ids': [lce.id for lce in lces]})

        content_views.append(cv)

    # 4. Assign all lifecycle environments to capsule and trigger optimized sync
    nailgun_capsule = capsule_configured.nailgun_capsule

    nailgun_capsule.content_add_lifecycle_environment(
        data={'environment_id': [lce.id for lce in lces]}
    )
    result = nailgun_capsule.content_lifecycle_environments()
    assert len(result['results']) == len(lces)

    sync_status = nailgun_capsule.content_sync(timeout='10m')

    # 5. Ensure sync task succeeded and no 'ShareLock' or 'deadlock' found in /var/log/messages.
    assert sync_status['result'] == 'success', f'Capsule sync task failed: {sync_status}'
    sharelock_check = capsule_configured.execute('grep -i "ShareLock" /var/log/messages')
    assert sharelock_check.status != 0, 'ShareLock detected in /var/log/messages'
    deadlock_check = capsule_configured.execute('grep -i "deadlock" /var/log/messages')
    assert deadlock_check.status != 0, 'Deadlock detected in /var/log/messages'
