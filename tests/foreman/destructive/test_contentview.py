"""Unit tests for the ``content_views`` paths.

:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun.entity_mixins import TaskFailedError

from robottelo import constants
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import wait_for_tasks

pytestmark = pytest.mark.destructive


@pytest.mark.tier4
@pytest.mark.run_in_one_thread
def test_positive_reboot_recover_cv_publish(target_sat, function_entitlement_manifest_org):
    """Reboot the Satellite during publish and resume publishing

    :id: cceae727-81db-40a4-9c26-05ca6e93464e

    :steps:
        1. Create and publish a Content View
        2. Reboot the Satellite while publish is running
        3. Check Foreman Tasks

    :expectedresults: Publish continues after reboot and finishes successfully

    :CaseImportance: High

    :CaseAutomation: Automated
    """
    org = function_entitlement_manifest_org
    rhel7_extra = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=constants.PRDS['rhel'],
        repo=constants.REPOS['rhel7_extra']['name'],
        reposet=constants.REPOSET['rhel7_extra'],
        releasever=None,
    )
    rhel7_optional = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=constants.PRDS['rhel'],
        repo=constants.REPOS['rhel7_optional']['name'],
        reposet=constants.REPOSET['rhel7_optional'],
        releasever=constants.REPOS['rhel7_optional']['releasever'],
    )
    rhel7_sup = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=constants.PRDS['rhel'],
        repo=constants.REPOS['rhel7_sup']['name'],
        reposet=constants.REPOSET['rhel7_sup'],
        releasever=constants.REPOS['rhel7_sup']['releasever'],
    )
    rhel7_extra = target_sat.api.Repository(id=rhel7_extra).read()
    rhel7_optional = target_sat.api.Repository(id=rhel7_optional).read()
    rhel7_sup = target_sat.api.Repository(id=rhel7_sup).read()
    for repo in [rhel7_extra, rhel7_optional, rhel7_sup]:
        repo.sync(timeout=1200)
    cv = target_sat.api.ContentView(
        organization=org,
        solve_dependencies=True,
        repository=[rhel7_extra, rhel7_sup, rhel7_optional],
    ).create()
    try:
        publish_task = cv.publish(synchronous=False)
        target_sat.power_control(state='reboot', ensure=True)
        wait_for_tasks(
            search_query=(f'id = {publish_task["id"]}'),
            search_rate=30,
            max_tries=60,
        )
    except TaskFailedError:
        target_sat.api.ForemanTask().bulk_resume(data={"task_ids": [publish_task['id']]})
        wait_for_tasks(
            search_query=(f'id = {publish_task["id"]}'),
            search_rate=30,
            max_tries=60,
        )
    task_status = target_sat.api.ForemanTask(id=publish_task['id']).poll()
    assert task_status['result'] == 'success'
