"""Test class for Notifications API

:Requirement: Notifications

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Notifications

:Team: Endeavour

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from mailbox import mbox
from re import findall
from tempfile import mkstemp

from fauxfactory import gen_string
import pytest
from wait_for import TimedOutError, wait_for

from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC, DEFAULT_ORG
from robottelo.utils.issue_handlers import is_open


@pytest.fixture
def admin_user_with_localhost_email(target_sat):
    """Admin user with e-mail set to `root@localhost`."""
    user = target_sat.api.User(
        admin=True,
        default_organization=DEFAULT_ORG,
        default_location=DEFAULT_LOC,
        description='created by nailgun',
        login=gen_string("alphanumeric"),
        password=gen_string("alphanumeric"),
        mail='root@localhost',
    ).create()
    user.mail_enabled = True
    user.update()

    yield user

    user.delete()


@pytest.fixture
def reschedule_long_running_tasks_notification(target_sat):
    """Reschedule long-running tasks checker from midnight (default) to every minute.
    Reset it back after the test.
    """
    default_cron_schedule = '0 0 * * *'
    every_minute_cron_schedule = '* * * * *'

    assert (
        target_sat.execute(
            f"FOREMAN_TASKS_CHECK_LONG_RUNNING_TASKS_CRONLINE='{every_minute_cron_schedule}' "
            "foreman-rake foreman_tasks:reschedule_long_running_tasks_checker"
        ).status
        == 0
    )

    yield

    assert (
        target_sat.execute(
            f"FOREMAN_TASKS_CHECK_LONG_RUNNING_TASKS_CRONLINE='{default_cron_schedule}' "
            "foreman-rake foreman_tasks:reschedule_long_running_tasks_checker"
        ).status
        == 0
    )


@pytest.fixture
def start_postfix_service(target_sat):
    """Start postfix service (disabled by default)."""
    assert target_sat.execute('systemctl start postfix').status == 0


@pytest.fixture
def clean_root_mailbox(target_sat):
    """Backup & purge local mailbox of the Satellite's root@localhost user.
    Restore it afterwards.
    """
    root_mailbox = '/var/spool/mail/root'
    root_mailbox_backup = f'{root_mailbox}-{gen_string("alphanumeric")}.bak'
    target_sat.execute(f'cp -f {root_mailbox} {root_mailbox_backup}')
    target_sat.execute(f'truncate -s 0 {root_mailbox}')

    yield root_mailbox

    target_sat.execute(f'mv -f {root_mailbox_backup} {root_mailbox}')


@pytest.fixture
def wait_for_long_running_task_mail(target_sat, clean_root_mailbox, long_running_task):
    """Wait until the long-running task ID is found in the Satellite's mbox file."""
    timeout = 300
    try:
        wait_for(
            func=target_sat.execute,
            func_args=[f'grep --quiet {long_running_task["task"]["id"]} {clean_root_mailbox}'],
            fail_condition=lambda res: res.status == 0,
            timeout=timeout,
            delay=5,
        )
    except TimedOutError:
        raise AssertionError(
            f'No notification e-mail with long-running task ID {long_running_task["task"]["id"]} '
            f'has arrived to {clean_root_mailbox} after {timeout} seconds.'
        )
    return True


@pytest.fixture
def root_mailbox_copy(target_sat, clean_root_mailbox, wait_for_long_running_task_mail):
    """Parsed local system copy of the Satellite's root user mailbox.

    :returns: :class:`mailbox.mbox` instance
    """
    assert wait_for_long_running_task_mail
    result = target_sat.execute(f'cat {clean_root_mailbox}')
    assert result.status == 0, f'Could not read mailbox {clean_root_mailbox} on Satellite host.'
    mbox_content = result.stdout
    _, local_mbox_file = mkstemp()
    with open(local_mbox_file, 'w') as fh:
        fh.writelines(mbox_content)
    return mbox(path=local_mbox_file)


@pytest.fixture
def long_running_task(target_sat):
    """Create an async task and set its start time and last report time to two days ago.
    After the test finishes, the task is cancelled.
    """
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Run Command - Script Default"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'organization': DEFAULT_ORG,
            'location': DEFAULT_LOC,
            'inputs': {
                'command': 'sleep 300',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {target_sat.hostname}',
            'password': settings.server.ssh_password,
        },
    )
    sql_date_2_days_ago = "now() - INTERVAL \'2 days\'"
    result = target_sat.execute(
        "su - postgres -c \"psql foreman postgres <<EOF\n"
        "UPDATE foreman_tasks_tasks "
        f"SET start_at = {sql_date_2_days_ago}, "
        f" started_at = {sql_date_2_days_ago}, "
        f" state_updated_at = {sql_date_2_days_ago} "
        f"WHERE id=\'{job['task']['id']}\';\nEOF\n\" "
    )
    assert 'UPDATE 1' in result.stdout, f'Failed to age task {job["task"]["id"]}: {result.stderr}'

    yield job

    result = target_sat.api.ForemanTask().bulk_cancel(data={"task_ids": [job['task']['id']]})
    assert 'cancelled' in result


@pytest.mark.tier3
@pytest.mark.usefixtures(
    'admin_user_with_localhost_email',
    'reschedule_long_running_tasks_notification',
    'start_postfix_service',
)
def test_positive_notification_for_long_running_tasks(long_running_task, root_mailbox_copy):
    """Check that a long-running task (i.e., running or paused for more than two days)
     is detected and an e-mail notification is sent to admin users.

    :id: effc1ff2-263b-11ee-b623-000c2989e153

    :setup:
        1. Create an admin user with e-mail 'root@localhost'.
        2. Change the long-running tasks checker cron schedule from '0 0 * * * ' (midnight)
            to '* * * * * ' (every minute).
        3. Start the `sendmail` service (disabled by default).

    :steps:
        1. Create a long-running task:
            1a. Schedule a sample task to run on the Satellite host.
            2b. In DB, update the task start time and status report time to two days back,
            so it is considered by Satellite as a long-running task.
        2. Update the long-running task checker schedule to run every minute
            (it runs at midnight by default).
        3. Wait for the notification e-mail to be sent to the admin user address.
        4. Check the e-mail if it contains all the important information, like,
            the task ID, link to the task, link to all long-running tasks.

    :BZ: 1950836, 2223996

    :customerscenario: true
    """
    task_id = long_running_task['task']['id']
    assert task_id

    for email in root_mailbox_copy:
        if task_id in email.as_string():
            assert 'Tasks pending since' in email.get(
                'Subject'
            ), f'Notification e-mail has wrong subject: {email.get("Subject")}'
            for mime_body in email.get_payload():
                body_text = mime_body.as_string()
                assert 'Tasks lingering in states running, paused since' in body_text
                assert f'/foreman_tasks/tasks/{task_id}' in body_text
                assert (
                    '/foreman_tasks/tasks?search=state+%5E+%28running%2C+paused'
                    '%29+AND+state_updated_at' in body_text
                ), 'Link for long-running tasks is missing in the e-mail body.'
                if not is_open('BZ:2223996'):
                    assert findall(r'_\("[\w\s]*"\)', body_text), 'Untranslated strings found.'
