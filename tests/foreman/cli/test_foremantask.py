"""Tests for the ``foreman_tasks/api/v2/tasks`` path.

:Requirement: Foremantask

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: TasksPlugin

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_tasks_backup():
    """Check no tasks are backup by default when cleaning up tasks from the database and
    no /var/lib/foreman/tasks-backup created for backup tasks.

    :id: 3575492c-7802-4b00-aefc-d53141ad7446

    :BZ: 1615015

    :customerscenario: true

    :steps:
        1. To run tasks cleanup every 5mins,
           `satellite-installer --foreman-plugin-tasks-cron-line '5 * * * *'`
        2. satellite-installer --foreman-plugin-tasks-backup true (which is default:false)
        3. Verify TASK_BACKUP=true in /etc/cron.d/foreman-tasks (which is default:false)
        4. Create any product or sync any repo to have a valid task.
        5. Include this line "TASK_SEARCH='label = Actions::Katello::Product::Create'"
           to /etc/cron.d/foreman-tasks
        6. Watch /var/log/foreman/cron.log for task cleanup of above labelled tasks.
        7. Verify /var/lib/foreman/tasks-backup created and has details of cleaned up tasks.

    :expectedresults: No tasks are backup by default when cleaning up tasks from the database,
                      and no /var/lib/foreman/tasks-backup created for backup tasks.

    :CaseImportance: High

    :CaseAutomation: NotAutomated

    """
