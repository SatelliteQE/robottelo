"""Unit tests for the ``content_views`` paths.

:Requirement: Contentview

:CaseAutomation: Automated

:CaseComponent: ContentViews

:team: Phoenix-content

:CaseImportance: High

"""
import random
from time import sleep

from nailgun.entity_mixins import TaskFailedError
import pytest

from robottelo import constants

pytestmark = pytest.mark.destructive


@pytest.mark.tier4
@pytest.mark.run_in_one_thread
def test_positive_reboot_recover_cv_publish(target_sat, function_sca_manifest_org):
    """Reboot the Satellite during publish and resume publishing

    :id: cceae727-81db-40a4-9c26-05ca6e93464e

    :setup:
        1. Enable and sync 3 bigger RH repos.

    :steps:
        1. Create and publish a Content View with the setup repos.
        2. Reboot the Satellite while publish is running.
        3. Check Foreman Tasks.

    :expectedresults: Publish continues after reboot and finishes successfully

    :CaseImportance: High

    :CaseAutomation: Automated
    """
    org = function_sca_manifest_org
    repos = []
    for tag in ['rhel7_optional', 'rhel7_extra', 'rhel7_sup']:
        id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=org.id,
            product=constants.REPOS[tag]['product'],
            repo=constants.REPOS[tag]['name'],
            reposet=constants.REPOS[tag]['reposet'],
            releasever=constants.REPOS[tag]['releasever'],
        )
        repo = target_sat.api.Repository(id=id).read()
        repos.append(repo)
        repo.sync(synchronous=False)
    target_sat.wait_for_tasks(
        search_query=(f'label = Actions::Katello::Repository::Sync and organization_id = {org.id}'),
        poll_timeout=750,
        search_rate=10,
        max_tries=75,
    )

    cv = target_sat.api.ContentView(
        organization=org,
        solve_dependencies=True,
        repository=repos,
    ).create()
    try:
        publish_task = cv.publish(synchronous=False)
        sleep_time = random.randint(0, 60)  # publish takes ~70s in 6.15 and SatLab VM
        sleep(sleep_time)
        target_sat.power_control(state='reboot', ensure=True)
        target_sat.wait_for_tasks(
            search_query=(f'id = {publish_task["id"]}'),
            search_rate=30,
            max_tries=60,
        )
    except TaskFailedError:
        target_sat.api.ForemanTask().bulk_resume(data={"task_ids": [publish_task['id']]})
        target_sat.wait_for_tasks(
            search_query=(f'id = {publish_task["id"]}'),
            search_rate=30,
            max_tries=60,
        )
    task_status = target_sat.api.ForemanTask(id=publish_task['id']).poll()
    assert (
        task_status['result'] == 'success'
    ), f'Publish after restart failed, sleep_time was {sleep_time}'
