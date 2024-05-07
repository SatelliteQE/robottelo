"""Test class for Notifications API

:Requirement: Notifications

:CaseAutomation: Automated

:CaseComponent: Notifications

:Team: Endeavour

:CaseImportance: High

"""

from mailbox import mbox
from re import findall
from tempfile import mkstemp

from fauxfactory import gen_string
import pytest
from wait_for import TimedOutError, wait_for

from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC, DEFAULT_ORG, repos as repo_constants


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
def admin_user_with_custom_settings(request, admin_user_with_localhost_email):
    """Admin user with custom properties set via parametrization.
    `request.param` should be a dict-like value.
    """
    for key, value in request.param.items():
        setattr(admin_user_with_localhost_email, key, value)
    admin_user_with_localhost_email.update(list(request.param.keys()))
    return admin_user_with_localhost_email


@pytest.fixture
def sysadmin_user_with_subscription_reposync_fail(target_sat):
    """System admin user with `root@localhost` e-mail
    and subscription to `Repository sync failure` notification.
    """
    sysadmin_role = target_sat.api.Role().search(query={'search': 'name="System admin"'})[0]
    user = target_sat.api.User(
        admin=False,
        default_organization=DEFAULT_ORG,
        default_location=DEFAULT_LOC,
        description='created by nailgun',
        login=gen_string("alphanumeric"),
        password=gen_string("alphanumeric"),
        mail='root@localhost',
        role=[sysadmin_role.id],
    ).create()
    user.mail_enabled = True
    user.update()
    target_sat.cli.User.mail_notification_add(
        {
            'user-id': user.id,
            'mail-notification': 'repository_sync_failure',
            'subscription': 'Subscribe',
        }
    )

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
            "foreman-rake foreman_tasks:reschedule_long_running_tasks_checker "
            f"FOREMAN_TASKS_CHECK_LONG_RUNNING_TASKS_CRONLINE='{every_minute_cron_schedule}'"
        ).status
        == 0
    )

    yield

    assert (
        target_sat.execute(
            "foreman-rake foreman_tasks:reschedule_long_running_tasks_checker "
            f"FOREMAN_TASKS_CHECK_LONG_RUNNING_TASKS_CRONLINE='{default_cron_schedule}'"
        ).status
        == 0
    )


@pytest.fixture(autouse=True)
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


def wait_for_mail(sat_obj, mailbox_file, contains_string, timeout=300, delay=5):
    """
    Wait until the desired string is found in the Satellite's mbox file.
    """
    try:
        wait_for(
            func=sat_obj.execute,
            func_args=[f"grep --quiet '{contains_string}' {mailbox_file}"],
            fail_condition=lambda res: res.status != 0,
            timeout=timeout,
            delay=delay,
        )
    except TimedOutError as err:
        raise AssertionError(
            f'No e-mail with text "{contains_string}" has arrived to mailbox {mailbox_file} '
            f'after {timeout} seconds.'
        ) from err
    return True


@pytest.fixture
def wait_for_long_running_task_mail(target_sat, clean_root_mailbox, long_running_task):
    """Wait until the long-running task ID is found in the Satellite's mbox file."""
    return wait_for_mail(
        sat_obj=target_sat,
        mailbox_file=clean_root_mailbox,
        contains_string=long_running_task["task"]["id"],
    )


@pytest.fixture
def wait_for_failed_repo_sync_mail(
    target_sat, clean_root_mailbox, fake_yum_repo, failed_repo_sync_task
):
    """Wait until the repo name that didn't sync is found in the Satellite's mbox file."""
    return wait_for_mail(
        sat_obj=target_sat, mailbox_file=clean_root_mailbox, contains_string=fake_yum_repo.name
    )


@pytest.fixture
def wait_for_no_long_running_task_mail(target_sat, clean_root_mailbox, long_running_task):
    """Wait and check that no long-running task ID is found in the Satellite's mbox file."""
    timeout = 120
    try:
        wait_for_mail(
            sat_obj=target_sat,
            mailbox_file=clean_root_mailbox,
            contains_string=long_running_task["task"]["id"],
            timeout=timeout,
        )
    except AssertionError:
        return True
    raise AssertionError(
        f'E-mail with long running task ID "{long_running_task["task"]["id"]}" '
        f'should not have arrived to mailbox {clean_root_mailbox}!'
    )


@pytest.fixture
def root_mailbox_copy(target_sat, clean_root_mailbox):
    """Parsed local system copy of the Satellite's root user mailbox.

    :returns: :class:`mailbox.mbox` instance
    """
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
    sql_date_2_days_ago = "now() - INTERVAL \'2 days\'"  # fmt: skip
    result = target_sat.execute(
        "su - postgres -c \"psql foreman postgres <<EOF\n"
        "UPDATE foreman_tasks_tasks "
        f"SET start_at = {sql_date_2_days_ago}, "
        f" started_at = {sql_date_2_days_ago}, "
        f" state_updated_at = {sql_date_2_days_ago} "
        f"WHERE id=\'{job['task']['id']}\';\nEOF\n\" "
    )  # fmt: skip  # skip formatting to avoid breaking the SQL query
    assert 'UPDATE 1' in result.stdout, f'Failed to age task {job["task"]["id"]}: {result.stderr}'

    yield job

    result = target_sat.api.ForemanTask().bulk_cancel(data={"task_ids": [job['task']['id']]})
    assert 'cancelled' in result


@pytest.fixture
def fake_yum_repo(target_sat):
    """Create a fake YUM repo. Delete it afterwards."""
    repo = target_sat.api.Repository(
        content_type='yum', url=repo_constants.FAKE_YUM_MISSING_REPO
    ).create()

    yield repo

    repo.delete()


@pytest.fixture
def failed_repo_sync_task(target_sat, fake_yum_repo):
    """
    Do a repo sync that should fail. Return the result.
    """
    fake_yum_repo.sync(synchronous=False)
    task_result = target_sat.wait_for_tasks(
        search_query=f"Synchronize repository '{fake_yum_repo.name}'", must_succeed=False
    )[0]
    task_status = target_sat.api.ForemanTask(id=task_result.id).poll(must_succeed=False)
    assert task_status['result'] != 'success'
    return task_status


@pytest.mark.tier3
@pytest.mark.usefixtures(
    'admin_user_with_localhost_email',
    'reschedule_long_running_tasks_notification',
    'wait_for_long_running_task_mail',
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
                assert not findall(r'_\("[\w\s]*"\)', body_text), 'Untranslated strings found.'


@pytest.mark.tier3
@pytest.mark.usefixtures(
    'sysadmin_user_with_subscription_reposync_fail',
    'wait_for_failed_repo_sync_mail',
)
def test_positive_notification_failed_repo_sync(failed_repo_sync_task, root_mailbox_copy):
    """Check that a failed repository sync emits an email notification to the subscribed user.

    :id: 19c477a2-8e39-11ee-9e3c-000c2989e153

    :setup:
        1. Create a user with 'System admin' role.
        2. Subscribe the user to the 'Repository sync failure' email notification.
        3. Create a non-existent YUM repository.
        4. Run repository sync, it should fail.

    :steps:
        1. Check that email notification has been sent.
        2. Check the e-mail if it contains all the important information, like,
            repository name, failed task ID and link to the task.

    :BZ: 1393613

    :customerscenario: true
    """
    task_id = failed_repo_sync_task['id']
    repo_name = failed_repo_sync_task['input']['repository']['name']
    product_name = failed_repo_sync_task['input']['product']['name']
    for email in root_mailbox_copy:
        if task_id in email.as_string():
            assert f'Repository {repo_name} failed to synchronize' in email.get(
                'Subject'
            ), f'Notification e-mail has wrong subject: {email.get("Subject")}'
            for mime_body in email.get_payload():
                body_text = mime_body.as_string()
                assert product_name in body_text
                assert f'/foreman_tasks/tasks/{task_id}' in body_text


@pytest.mark.tier1
def test_positive_notification_recipients(target_sat):
    """Check that endpoint `/notification_recipients` works and returns correct data structure.

    :id: 10e0fac2-f11f-11ee-ba60-000c2989e153

    :steps:
        1. Do a GET request to /notification_recipients endpoint.
        2. Check the returned data structure for expected keys.

    :BZ: 2249970

    :customerscenario: true
    """
    notification_keys = [
        'id',
        'seen',
        'level',
        'text',
        'created_at',
        'group',
        'actions',
    ]

    recipients = target_sat.api.NotificationRecipients().read()
    for notification in recipients.notifications:
        assert set(notification_keys) == set(notification.keys())


@pytest.mark.tier3
@pytest.mark.parametrize(
    'admin_user_with_custom_settings',
    [
        pytest.param({'disabled': True, 'mail_enabled': True}, id='account_disabled'),
        pytest.param({'disabled': False, 'mail_enabled': False}, id='mail_disabled'),
    ],
    indirect=True,
)
@pytest.mark.usefixtures(
    'reschedule_long_running_tasks_notification',
    'wait_for_no_long_running_task_mail',
)
def test_negative_no_notification_for_long_running_tasks(
    admin_user_with_custom_settings, long_running_task, root_mailbox_copy
):
    """Check that an e-mail notification for a long-running task
    (i.e., running or paused for more than two days)
    is NOT sent to users with disabled account or disabled e-mail.

    :id: 03b41216-f39b-11ee-b9ea-000c2989e153

    :setup:
        1. Create an admin user with e-mail address set and:
           a. account disabled & mail enabled
           b. account enabled & mail disabled

    :steps:
        1. Create a long-running task.
        3. For each user, wait and check that the notification e-mail has NOT been sent.

    :BZ: 2245056

    :customerscenario: true
    """
    assert admin_user_with_custom_settings
    task_id = long_running_task['task']['id']
    assert task_id

    for email in root_mailbox_copy:
        assert (
            task_id not in email.as_string()
        ), f'Unexpected notification e-mail with long-running task ID {task_id} found in user mailbox!'
