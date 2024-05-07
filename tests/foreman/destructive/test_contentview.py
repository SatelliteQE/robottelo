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


@pytest.fixture(scope='module')
def module_big_repos(module_target_sat, module_sca_manifest_org):
    """Enables and syncs three bigger RH repos"""
    repos = []
    for tag in ['rhel7_optional', 'rhel7_extra', 'rhel7_sup']:
        id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=constants.DEFAULT_ARCHITECTURE,
            org_id=module_sca_manifest_org.id,
            product=constants.REPOS[tag]['product'],
            repo=constants.REPOS[tag]['name'],
            reposet=constants.REPOS[tag]['reposet'],
            releasever=constants.REPOS[tag]['releasever'],
        )
        repo = module_target_sat.api.Repository(id=id).read()
        repos.append(repo)
        repo.sync(synchronous=False)
    module_target_sat.wait_for_tasks(
        search_query=(
            f'label = Actions::Katello::Repository::Sync and organization_id = {module_sca_manifest_org.id}'
        ),
        poll_timeout=750,
        search_rate=10,
        max_tries=75,
    )
    return repos


@pytest.mark.tier4
@pytest.mark.run_in_one_thread
@pytest.mark.parametrize('reboot', [True, False], ids=['vm_reboot', 'fm_restart'])
def test_positive_reboot_recover_cv_publish(
    module_target_sat, module_sca_manifest_org, module_big_repos, reboot
):
    """Reboot the Satellite during publish and resume publishing

    :id: cceae727-81db-40a4-9c26-05ca6e93464e

    :parametrized: yes

    :setup:
        1. Enable and sync 3 bigger RH repos.

    :steps:
        1. Create and publish a Content View with the setup repos.
        2. Reboot or restart the Satellite while publish is running.
        3. Check Foreman Tasks.

    :expectedresults: Publish continues after reboot/restart and finishes successfully.
    """
    cv = module_target_sat.api.ContentView(
        organization=module_sca_manifest_org,
        solve_dependencies=True,
        repository=module_big_repos,
    ).create()
    try:
        publish_task = cv.publish(synchronous=False)
        sleep_time = random.randint(0, 60)  # publish takes ~70s in 6.15 and SatLab VM
        sleep(sleep_time)
        if reboot:
            module_target_sat.power_control(state='reboot', ensure=True)
        else:
            module_target_sat.cli.Service.restart()
        module_target_sat.wait_for_tasks(
            search_query=(f'id = {publish_task["id"]}'),
            search_rate=30,
            max_tries=60,
        )
    except TaskFailedError:
        module_target_sat.api.ForemanTask().bulk_resume(data={"task_ids": [publish_task['id']]})
        module_target_sat.wait_for_tasks(
            search_query=(f'id = {publish_task["id"]}'),
            search_rate=30,
            max_tries=60,
        )
    task_status = module_target_sat.api.ForemanTask(id=publish_task['id']).poll()
    assert (
        task_status['result'] == 'success'
    ), f'Publish after restart failed, sleep_time was {sleep_time}'
