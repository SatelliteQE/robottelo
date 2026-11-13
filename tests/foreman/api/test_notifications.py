"""Test class for Notifications API

:Requirement: Notifications

:CaseAutomation: Automated

:CaseComponent: Notifications

:Team: Dragonfly

:CaseImportance: High

"""

from email import message_from_string
import json
from re import findall
from shlex import quote
from urllib.parse import quote as urlquote, urlencode

from fauxfactory import gen_string
import pytest
from wait_for import TimedOutError, wait_for

from pytest_fixtures.component.notifications import _execute_checked, _mailpit_command
from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC, DEFAULT_ORG, repos as repo_constants

pytestmark = pytest.mark.foremanctl


@pytest.fixture
def admin_user_with_localhost_email(target_sat, notification_mail):
    """Create and clean up only the uniquely addressed admin owned by this test."""
    user = target_sat.api.User(
        admin=True,
        default_organization=DEFAULT_ORG,
        default_location=DEFAULT_LOC,
        description='created by nailgun',
        login=gen_string("alphanumeric"),
        password=gen_string("alphanumeric"),
        mail=notification_mail['address'],
    ).create()
    try:
        user.mail_enabled = True
        user.update()
        yield user
    finally:
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
def sysadmin_user_with_subscription_reposync_fail(target_sat, notification_mail):
    """System admin user with a unique localhost e-mail
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
        mail=notification_mail['address'],
        role=[sysadmin_role.id],
    ).create()
    try:
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
    finally:
        user.delete()


def mailpit_messages(target_sat, config):
    query = urlencode({'query': f'to:{config["address"]}', 'limit': 1000})
    response = _execute_checked(
        target_sat, _mailpit_command(config['mailpit'], f'/api/v1/search?{query}')
    )
    return [
        message_from_string(
            _execute_checked(
                target_sat,
                _mailpit_command(
                    config['mailpit'], f'/api/v1/message/{urlquote(message["ID"], safe="")}/raw'
                ),
            ).stdout
        )
        for message in json.loads(response.stdout)['messages']
    ]


def _check_long_running_tasks(target_sat):
    code = (
        'Rake::Task.define_task(check_long_running_tasks: "dynflow:client") { '
        'User.as_anonymous_admin { ForemanTasks.sync_task(Actions::CheckLongRunningTasks) } }'
    )
    _execute_checked(
        target_sat,
        f'ALLOW_UNSUPPORTED=true foreman-rake -E {quote(code)} check_long_running_tasks',
    )


def wait_for_mail(target_sat, notification_mail, contains_string, timeout=30):
    wait_for(
        lambda: any(
            contains_string in message.as_string()
            for message in mailpit_messages(target_sat, notification_mail)
        ),
        timeout=timeout,
        delay=5,
    )


@pytest.fixture
def long_running_task(target_sat, notification_mail):
    """Create an async task forced into a two-days-old ``running`` state.

    The task is launched via the API so a real, cancellable dynflow plan
    exists, then its state and timestamps are set directly in the DB so the
    long-running-tasks checker reports on it.
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

    def _task_exists():
        rows = target_sat.query_db(
            f"SELECT id FROM foreman_tasks_tasks WHERE id='{job['task']['id']}'"
        )
        return bool(rows)

    wait_for(
        func=_task_exists,
        fail_condition=lambda exists: not exists,
        timeout=60,
        delay=1,
    )

    sql_date_2_days_ago = "now() - INTERVAL '2 days'"
    query = (
        "UPDATE foreman_tasks_tasks "
        "SET state = 'running', result = 'pending', "
        f"start_at = {sql_date_2_days_ago}, "
        f"started_at = {sql_date_2_days_ago}, "
        f"state_updated_at = {sql_date_2_days_ago} "
        f"WHERE id='{job['task']['id']}'"
    )
    result = target_sat.query_db(query, output_format='raw')
    assert 'UPDATE 1' in result, f'Failed to age task {job["task"]["id"]}'

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
def failed_repo_sync_task(target_sat, fake_yum_repo, sysadmin_user_with_subscription_reposync_fail):
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


@pytest.mark.usefixtures('admin_user_with_localhost_email')
def test_positive_notification_for_long_running_tasks(
    target_sat, notification_mail, long_running_task
):
    """Check that a long-running task (i.e., running or paused for more than two days)
     is detected and an e-mail notification is sent to admin users.

    :id: effc1ff2-263b-11ee-b623-000c2989e153

    :setup:
        1. Create an admin user with a unique localhost e-mail address.
        2. Start Mailpit and configure Foreman SMTP delivery to it.

    :steps:
        1. Create a long-running task:
            1a. Schedule a sample task to run on the Satellite host.
            2b. In DB, update the task start time and status report time to two days back,
            so it is considered by Satellite as a long-running task.
        2. Execute the long-running task checker synchronously.
        3. Wait for the notification e-mail to be sent to the admin user address.
        4. Check the e-mail if it contains all the important information, like,
            the task ID, link to the task, link to all long-running tasks.

    :BZ: 1950836, 2223996

    :customerscenario: true
    """
    _check_long_running_tasks(target_sat)
    task_id = long_running_task['task']['id']
    assert task_id
    wait_for_mail(target_sat, notification_mail, task_id)

    for email in mailpit_messages(target_sat, notification_mail):
        if task_id in email.as_string():
            assert 'Tasks pending since' in email.get('Subject'), (
                f'Notification e-mail has wrong subject: {email.get("Subject")}'
            )
            for mime_body in email.get_payload():
                body_text = mime_body.as_string()
                assert 'Tasks lingering in states running, paused since' in body_text
                assert f'/foreman_tasks/tasks/{task_id}' in body_text
                assert (
                    '/foreman_tasks/tasks?search=state+%5E+%28running%2C+paused'
                    '%29+AND+state_updated_at' in body_text
                ), 'Link for long-running tasks is missing in the e-mail body.'
                assert not findall(r'_\("[\w\s]*"\)', body_text), 'Untranslated strings found.'


def test_positive_notification_failed_repo_sync(
    target_sat, notification_mail, failed_repo_sync_task
):
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
    wait_for_mail(target_sat, notification_mail, task_id)
    for email in mailpit_messages(target_sat, notification_mail):
        if task_id in email.as_string():
            assert f'Repository {repo_name} failed to synchronize' in email.get('Subject'), (
                f'Notification e-mail has wrong subject: {email.get("Subject")}'
            )
            for mime_body in email.get_payload():
                body_text = mime_body.as_string()
                assert product_name in body_text
                assert f'/foreman_tasks/tasks/{task_id}' in body_text


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


@pytest.mark.parametrize(
    'admin_user_with_custom_settings',
    [
        pytest.param({'disabled': True, 'mail_enabled': True}, id='account_disabled'),
        pytest.param({'disabled': False, 'mail_enabled': False}, id='mail_disabled'),
    ],
    indirect=True,
)
def test_negative_no_notification_for_long_running_tasks(
    target_sat, notification_mail, admin_user_with_custom_settings, long_running_task
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
        2. Execute the checker synchronously after applying the user's settings.
        3. Verify no matching notification arrives within 30 seconds.

    :BZ: 2245056

    :customerscenario: true
    """
    _check_long_running_tasks(target_sat)
    with pytest.raises(TimedOutError):
        wait_for_mail(target_sat, notification_mail, long_running_task['task']['id'])
