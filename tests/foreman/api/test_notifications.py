"""Notification API tests for Foreman 5.0 and later on foremanctl hosts.

:Requirement: Notifications

:CaseAutomation: Automated

:CaseComponent: Notifications

:Team: Dragonfly

:CaseImportance: High

"""

from contextlib import ExitStack
from email import message_from_string
from email.utils import getaddresses
from mailbox import mbox
from pathlib import PurePosixPath
from re import findall
from shlex import quote
from tempfile import mkstemp

from fauxfactory import gen_string
import pytest
from wait_for import TimedOutError, wait_for

from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC, DEFAULT_ORG, DataFile, repos as repo_constants

pytestmark = pytest.mark.foremanctl

MAIL_CATCHER_SCRIPT = DataFile.DATA_DIR.joinpath('mail_catcher.py')


@pytest.fixture
def admin_user_with_localhost_email(target_sat, use_smtp_mail_delivery):
    """Create and clean up only the uniquely addressed admin owned by this test."""
    user = target_sat.api.User(
        admin=True,
        default_organization=DEFAULT_ORG,
        default_location=DEFAULT_LOC,
        description='created by nailgun',
        login=gen_string("alphanumeric"),
        password=gen_string("alphanumeric"),
        mail=use_smtp_mail_delivery['address'],
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
def sysadmin_user_with_subscription_reposync_fail(target_sat, use_smtp_mail_delivery):
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
        mail=use_smtp_mail_delivery['address'],
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


@pytest.fixture
def reschedule_long_running_tasks_notification(target_sat, use_smtp_mail_delivery):
    """Reschedule long-running tasks checker from midnight (default) to every minute.
    Reset it back after the test.
    """
    default_cron_schedule = '0 0 * * *'
    every_minute_cron_schedule = '* * * * *'

    def reschedule(schedule):
        _execute_checked(
            target_sat,
            'podman exec foreman foreman-rake '
            'foreman_tasks:reschedule_long_running_tasks_checker '
            f'FOREMAN_TASKS_CHECK_LONG_RUNNING_TASKS_CRONLINE={quote(schedule)}',
        )

    try:
        reschedule(every_minute_cron_schedule)
        yield
    finally:
        reschedule(default_cron_schedule)


def _mailpit_command(mailpit, path):
    return (
        'podman exec foreman curl --noproxy "*" --fail --silent --show-error --max-time 10 '
        f'{quote(f"http://{mailpit}:8025{path}")}'
    )



def _execute_checked(target_sat, command):
    result = target_sat.execute(command)
    assert result.status == 0, f'Command failed: {command}: {result.stderr}'
    return result


def _restore_setting(setting, value):
    setting.value = value
    setting.update(['value'])


def _change_setting(target_sat, cleanup, name, value):
    setting = target_sat.api.Setting().search(query={'search': f'name={name}'})[0]
    cleanup.callback(_restore_setting, setting, setting.value)
    setting.value = value
    setting.update(['value'])


def _stop_mail_catcher(target_sat, pid_file):
    # The PID file lives in a private directory; never match the cleanup shell's command line.
    _execute_checked(
        target_sat,
        f'if test -f {quote(pid_file)}; then '
        f'pid=$(cat {quote(pid_file)}) && '
        'if kill -0 "$pid" 2>/dev/null; then kill "$pid"; fi; fi',
    )


def _mail_catcher_address(target_sat, port):
    """Select a host address that completes SMTP from the Foreman container."""
    import json

    network_info = _execute_checked(
        target_sat,
        "podman inspect foreman --format '{{.HostConfig.NetworkMode}} "
        "{{json .NetworkSettings.Networks}}'",
    ).stdout.strip()
    network_mode, networks_json = network_info.split(' ', 1)
    networks = json.loads(networks_json) or {}
    candidates = ['host.containers.internal']
    if network_mode == 'host':
        candidates.append('127.0.0.1')
    candidates.extend(network['Gateway'] for network in networks.values() if network.get('Gateway'))
    candidates.append(target_sat.hostname)

    # Ruby is available in the application container; bound DNS, connect and read time together.
    probe = r'''
Timeout.timeout(5) do
  Socket.tcp(ARGV[0], Integer(ARGV[1]), connect_timeout: 3, resolv_timeout: 3) do |socket|
    raise 'Unexpected SMTP greeting' unless socket.gets == "220 mail-catcher\r\n"
    socket.write("EHLO robottelo\r\n")
    raise 'SMTP EHLO failed' unless socket.gets == "250 mail-catcher\r\n"
    socket.write("QUIT\r\n")
    raise 'SMTP QUIT failed' unless socket.gets == "221 Bye\r\n"
  end
end
'''
    failures = []
    for address in dict.fromkeys(candidates):
        result = target_sat.execute(
            f'podman exec foreman ruby -rsocket -rtimeout -e {quote(probe)} '
            f'{quote(address)} {int(port)}'
        )
        if result.status == 0:
            return address
        failures.append(f'{address}: {result.stderr.strip() or result.stdout.strip()}')
    raise AssertionError(
        'No reachable SMTP catcher from the Foreman container: ' + '; '.join(failures)
    )


def _setup_mail_catcher(target_sat, mails_dir, cleanup):
    """Start an isolated catcher and register each resource before changing settings."""
    script_path = f'{mails_dir}/mail_catcher.py'
    pid_file = f'{mails_dir}/catcher.pid'
    ready_file = f'{mails_dir}/catcher.ready'
    target_sat.put(MAIL_CATCHER_SCRIPT, remote_path=script_path)
    cleanup.callback(_stop_mail_catcher, target_sat, pid_file)
    _execute_checked(
        target_sat,
        f'nohup python3 {quote(script_path)} 0 {quote(mails_dir)} {quote(ready_file)} '
        f'> {quote(mails_dir)}/catcher.log 2>&1 < /dev/null & '
        f'echo $! > {quote(pid_file)}',
    )
    wait_for(
        func=target_sat.execute,
        func_args=[f'test -s {quote(ready_file)}'],
        fail_condition=lambda res: res.status != 0,
        timeout=30,
        delay=1,
    )
    pid, port = _execute_checked(target_sat, f'cat {quote(ready_file)}').stdout.split()
    started_pid = _execute_checked(target_sat, f'cat {quote(pid_file)}').stdout.strip()
    assert pid == started_pid, 'Readiness was published by a different process'
    _execute_checked(target_sat, f'kill -0 {int(pid)}')
    smtp_address = _mail_catcher_address(target_sat, int(port))

    for name, value in (
        ('smtp_authentication', ''),
        ('smtp_user_name', ''),
        ('smtp_enable_starttls_auto', False),
        ('smtp_address', smtp_address),
        ('smtp_port', int(port)),
    ):
        _change_setting(target_sat, cleanup, name, value)


def _setup_file_delivery_method(target_sat, mails_dir, cleanup):
    """Allow file delivery without relaxing permissions on existing mailboxes."""
    result = target_sat.execute(f'test -d {quote(mails_dir)}')
    if result.status == 0:
        owner, mode = _execute_checked(
            target_sat, f"stat -c '%u:%g %a' {quote(mails_dir)}"
        ).stdout.split()
        cleanup.callback(_execute_checked, target_sat, f'chmod {mode} {quote(mails_dir)}')
        cleanup.callback(_execute_checked, target_sat, f'chown {owner} {quote(mails_dir)}')
    else:
        _execute_checked(target_sat, f'mkdir -m 0700 {quote(mails_dir)}')
        cleanup.callback(_execute_checked, target_sat, f'rmdir {quote(mails_dir)}')
    _execute_checked(target_sat, f'chown foreman:foreman {quote(mails_dir)}')
    _execute_checked(target_sat, f'chmod 0700 {quote(mails_dir)}')
    _change_setting(target_sat, cleanup, 'delivery_method', 'file')


@pytest.fixture(autouse=True)
def use_smtp_mail_delivery(target_sat):
    """Capture mail in a private Mailpit container and restore shared SMTP settings."""
    lock_dir = '/run/robottelo-notifications.lock'
    wait_for(
        func=target_sat.execute,
        func_args=[f'mkdir -m 0700 {lock_dir}'],
        fail_condition=lambda res: res.status != 0,
        timeout=1800,
        delay=5,
    )
    with ExitStack() as cleanup:
        cleanup.callback(_execute_checked, target_sat, f'rmdir {lock_dir}')
        networks = _execute_checked(
            target_sat,
            "podman inspect foreman --format "
            "'{{range $name, $network := .NetworkSettings.Networks}}{{$name}} {{end}}'",
        ).stdout.split()
        assert networks, 'Foreman must be attached to a Podman network'
        mailpit = f'robottelo-mailpit-{gen_string("alpha").lower()}'
        cleanup.callback(_execute_checked, target_sat, f'podman rm -f --ignore {quote(mailpit)}')
        network_args = ' '.join(f'--network {quote(network)}' for network in networks)
        image = settings.get('notifications.mailpit_image', 'docker.io/axllent/mailpit:v1.27.4')
        _execute_checked(
            target_sat,
            f'podman run -d --name {quote(mailpit)} {network_args} '
            f'{quote(image)} '
            '--smtp :1025 --listen :8025 --smtp-disable-rdns --disable-version-check --max 0',
        )
        wait_for(
            func=target_sat.execute,
            func_args=[_mailpit_command(mailpit, '/readyz')],
            fail_condition=lambda res: res.status != 0,
            timeout=60,
            delay=1,
        )
        workers = _execute_checked(
            target_sat, "podman ps --filter name=^dynflow-sidekiq- --format '{{.Names}}'"
        ).stdout.split()
        probe = 'Timeout.timeout(5) { Net::SMTP.start(ARGV[0], 1025) {} }'
        for container in ['foreman', *workers]:
            _execute_checked(
                target_sat,
                f'podman exec {quote(container)} ruby -rnet/smtp -rtimeout '
                f'-e {quote(probe)} {quote(mailpit)}',
            )
        for name, value in (
            ('smtp_authentication', ''),
            ('smtp_user_name', ''),
            ('smtp_enable_starttls_auto', False),
            ('smtp_address', mailpit),
            ('smtp_port', 1025),
        ):
            _change_setting(target_sat, cleanup, name, value)
        yield {'mailpit': mailpit, 'address': f'root+{gen_string("alphanumeric")}@localhost'}


@pytest.fixture
def clean_root_mailbox(use_smtp_mail_delivery):
    """Return the freshly created mailbox owned by this test."""
    return use_smtp_mail_delivery['mailbox']


def _read_mailbox(target_sat, path):
    mailbox = quote(path)
    parent = quote(str(PurePosixPath(path).parent))
    result = target_sat.execute(
        f'if test -e {mailbox} || test -L {mailbox}; then cat -- {mailbox}; '
        f'elif test -d {parent} && test -r {parent} && test -x {parent}; then exit 44; '
        'else exit 1; fi'
    )
    assert result.status in (0, 44), f'Could not read mailbox {path}: {result.stderr}'
    return result.stdout if result.status == 0 else ''


def _recipient_messages(content, recipient):
    # Installer delivery puts all root+ addresses in root's system mailbox.
    messages = content.split('\nFrom ')
    for index, raw in enumerate(messages):
        if index or raw.startswith('From '):
            raw = raw.split('\n', 1)[-1]
        message = message_from_string(raw)
        addresses = getaddresses(message.get_all('To', []) + message.get_all('Cc', []))
        if recipient in [address for _, address in addresses]:
            yield message


def wait_for_mail(sat_obj, mailbox_file, contains_string, recipient, timeout=300, delay=5):
    """Wait for the expected text in mail addressed to this test's user."""

    def received():
        return any(
            contains_string in message.as_string()
            for message in _recipient_messages(_read_mailbox(sat_obj, mailbox_file), recipient)
        )

    try:
        wait_for(func=received, fail_condition=False, timeout=timeout, delay=delay)
    except TimedOutError as err:
        raise AssertionError(
            f'No e-mail with text "{contains_string}" has arrived to mailbox {mailbox_file} '
            f'after {timeout} seconds.'
        ) from err
    return True


@pytest.fixture
def wait_for_long_running_task_mail(
    target_sat, clean_root_mailbox, long_running_task, use_smtp_mail_delivery
):
    """Wait until the long-running task ID is found in the Satellite's mbox file."""
    return wait_for_mail(
        sat_obj=target_sat,
        mailbox_file=clean_root_mailbox,
        contains_string=long_running_task["task"]["id"],
        recipient=use_smtp_mail_delivery["address"],
    )


@pytest.fixture
def wait_for_failed_repo_sync_mail(
    target_sat, clean_root_mailbox, fake_yum_repo, failed_repo_sync_task, use_smtp_mail_delivery
):
    """Wait until the repo name that didn't sync is found in the Satellite's mbox file."""
    return wait_for_mail(
        sat_obj=target_sat,
        mailbox_file=clean_root_mailbox,
        contains_string=fake_yum_repo.name,
        recipient=use_smtp_mail_delivery["address"],
    )


@pytest.fixture
def wait_for_no_long_running_task_mail(
    target_sat, clean_root_mailbox, long_running_task, use_smtp_mail_delivery
):
    """Wait and check that no long-running task ID is found in the Satellite's mbox file."""
    timeout = 120
    try:
        wait_for_mail(
            sat_obj=target_sat,
            mailbox_file=clean_root_mailbox,
            contains_string=long_running_task["task"]["id"],
            recipient=use_smtp_mail_delivery["address"],
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

    :return: :class:`mailbox.mbox` instance
    """
    result = target_sat.execute(f'cat {clean_root_mailbox}')
    assert result.status == 0, f'Could not read mailbox {clean_root_mailbox} on Satellite host.'
    mbox_content = result.stdout
    _, local_mbox_file = mkstemp()
    with open(local_mbox_file, 'w') as fh:
        fh.writelines(mbox_content)
    return mbox(path=local_mbox_file)


@pytest.fixture
def long_running_task(target_sat, use_smtp_mail_delivery):
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
        1. Create an admin user with a unique localhost e-mail address.
        2. Change the long-running tasks checker cron schedule from '0 0 * * * ' (midnight)
            to '* * * * * ' (every minute).
        3. Start the SMTP catcher and configure Foreman to deliver to it.

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
            assert f'Repository {repo_name} failed to synchronize' in email.get('Subject'), (
                f'Notification e-mail has wrong subject: {email.get("Subject")}'
            )
            for mime_body in email.get_payload():
                body_text = mime_body.as_string()
                assert product_name in body_text
                assert f'/foreman_tasks/tasks/{task_id}' in body_text


def _check_long_running_tasks(target_sat):
    marker = 'ROBOTTELO_NOTIFICATION_CHECK_COMPLETE'
    code = (
        'User.as_anonymous_admin { ForemanTasks.sync_task(Actions::CheckLongRunningTasks) }; '
        f'puts "{marker}"; exit'
    )
    result = _execute_checked(
        target_sat, f'printf \'%s\\n\' {quote(code)} | podman exec -i foreman foreman-rake console'
    )
    assert marker in result.stdout.splitlines(), (
        f'Notification checker did not complete: {result.stdout}'
    )



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
        assert task_id not in email.as_string(), (
            f'Unexpected notification e-mail with long-running task ID {task_id} found in user mailbox!'
        )
