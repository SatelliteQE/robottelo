"""Unit tests for the ``repositories`` paths.

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Repositories

:Assignee: chiggins

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun.entity_mixins import TaskFailedError

from robottelo import constants
from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import upload_manifest
from robottelo.api.utils import wait_for_tasks

pytestmark = pytest.mark.destructive


@pytest.mark.run_in_one_thread
def test_positive_reboot_recover_sync(target_sat):
    """Reboot during repo sync and resume the sync when the Satellite is online

    :id: 4f746e28-444c-4688-b92b-778a6e58d614

    :steps:
        1. Add a repo and start sync
        2. Reboot the Satellite while sync is running
        3. Check Foreman Tasks

    :expectedresults: Repo sync resumes / can resume and finishes successfully

    :CaseImportance: High

    :CaseAutomation: Automated
    """
    org = target_sat.api.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    rhel7_extra = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=constants.PRDS['rhel'],
        repo=constants.REPOS['rhel7_extra']['name'],
        reposet=constants.REPOSET['rhel7_extra'],
        releasever=None,
    )
    rhel7_extra = target_sat.api.Repository(id=rhel7_extra).read()
    sync_task = rhel7_extra.sync(synchronous=False)
    target_sat.power_control(state='reboot', ensure=True)
    try:
        wait_for_tasks(
            search_query=(f'id = {sync_task["id"]}'),
            search_rate=15,
            max_tries=10,
        )
    except TaskFailedError:
        sync_task = rhel7_extra.sync(synchronous=False)
        wait_for_tasks(
            search_query=(f'id = {sync_task["id"]}'),
            search_rate=15,
            max_tries=10,
        )
    task_status = target_sat.api.ForemanTask(id=sync_task['id']).poll()
    assert task_status['result'] == 'success'
