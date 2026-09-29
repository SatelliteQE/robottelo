"""Local regression tests for notification mail setup and recipient isolation."""

from contextlib import ExitStack
from email.message import EmailMessage
from mailbox import mbox
import socket
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tests.foreman.api import test_notifications as notifications
from tests.foreman.data import mail_catcher


@pytest.mark.parametrize(
    'recipient',
    [
        '',
        '/tmp/escaped',
        '../escaped',
        '../../root@localhost',
        'a/b@localhost',
        r'a\b@localhost',
        'a\x00@localhost',
        '.',
        '..',
    ],
)
def test_recipient_paths_are_rejected(tmp_path, monkeypatch, recipient):
    """Reject recipient paths before any mailbox is opened.

    :id: 3325741c-72da-465c-b0cd-ef015dcb0ffe
    :steps: Validate absolute paths, traversal paths and invalid filenames.
    :expectedresults: Every unsafe recipient is rejected.
    """
    monkeypatch.setattr(mail_catcher, 'MAILS_DIR', str(tmp_path))
    with pytest.raises(ValueError, match='Invalid recipient'):
        mail_catcher.mailbox_path(recipient)


def test_symlink_mailbox_is_rejected(tmp_path, monkeypatch):
    """Preserve files outside the catcher when a recipient names a symlink.

    :id: 55ba8eae-c7d0-45f8-af17-71f061b54cc0
    :steps: Validate a mailbox symlink pointing outside the mail directory.
    :expectedresults: The recipient is rejected and its target remains intact.
    """
    directory = tmp_path / 'mail'
    directory.mkdir()
    outside = tmp_path / 'outside'
    outside.write_text('keep')
    (directory / 'root@localhost').symlink_to(outside)
    monkeypatch.setattr(mail_catcher, 'MAILS_DIR', str(directory))
    with pytest.raises(ValueError, match='escapes mailbox directory'):
        mail_catcher.mailbox_path('root@localhost')
    assert outside.read_text() == 'keep'


def test_smtp_rejects_traversal_and_delivers_safe_recipient(tmp_path, monkeypatch):
    """Exercise recipient validation through the SMTP protocol.

    :id: daea5e05-8cde-43e5-ab9c-f1a9373adf96
    :steps: Submit an invalid recipient, then deliver mail to a unique valid recipient.
    :expectedresults: Invalid RCPT/DATA commands fail; valid mail stays inside the directory.
    """
    monkeypatch.setattr(mail_catcher, 'MAILS_DIR', str(tmp_path))
    client, server = socket.socketpair()
    client.settimeout(5)
    worker = threading.Thread(target=mail_catcher.handle, args=(server,), daemon=True)
    worker.start()
    stream = client.makefile('rb')

    def command(line):
        client.sendall(line.encode() + b'\r\n')
        return stream.readline()[:3]

    try:
        assert stream.readline().startswith(b'220')
        assert command('EHLO localhost') == b'250'
        assert command('MAIL FROM:<sender@localhost>') == b'250'
        assert command('RCPT TO:<../outside>') == b'550'
        assert command('DATA') == b'503'
        assert command('RCPT TO:<root+test@localhost>') == b'250'
        assert command('DATA') == b'354'
        assert command('To: root+test@localhost\r\nSubject: regression\r\n\r\nbody\r\n.') == b'250'
        assert command('QUIT') == b'221'
    finally:
        stream.close()
        client.close()
        worker.join(timeout=5)
    box = mbox(tmp_path / 'root+test@localhost')
    try:
        assert len(box) == 1
        assert box[0]['Subject'] == 'regression'
    finally:
        box.close()
    assert set(p.name for p in tmp_path.iterdir()) == {'root+test@localhost'}


def test_setting_update_failure_restores_completed_changes():
    """Restore values even when an update fails during setup.

    :id: bfa4b053-e71e-47ca-9563-e1b1e5b068b9
    :steps: Change one SMTP setting, then raise during the next setting update.
    :expectedresults: Both original setting values are restored.
    """
    address = SimpleNamespace(value='original-host', update=Mock())
    port = SimpleNamespace(value=25, update=Mock(side_effect=[RuntimeError('setup'), None]))
    target = Mock()
    target.api.Setting.return_value.search.side_effect = [[address], [port]]

    def setup():
        with ExitStack() as cleanup:
            notifications._change_setting(target, cleanup, 'smtp_address', 'catcher')
            notifications._change_setting(target, cleanup, 'smtp_port', 12345)

    with pytest.raises(RuntimeError, match='setup'):
        setup()
    assert (address.value, port.value) == ('original-host', 25)
    assert address.update.call_count == port.update.call_count == 2


def test_file_delivery_restores_setting_owner_and_permissions():
    """Restore delivery settings and directory permissions after file delivery.

    :id: 3d4abb90-2cad-498a-9c52-feec3c37a17f
    :steps: Set up file delivery for an existing directory and then unwind setup.
    :expectedresults: The original method, owner and mode are restored.
    """
    setting = SimpleNamespace(value='smtp', update=Mock())
    target = Mock()
    target.api.Setting.return_value.search.return_value = [setting]
    target.execute.side_effect = lambda command: SimpleNamespace(
        status=0, stdout='123:456 750' if command.startswith('stat ') else '', stderr=''
    )
    with ExitStack() as cleanup:
        notifications._setup_file_delivery_method(target, '/mails', cleanup)
        assert setting.value == 'file'
    assert setting.value == 'smtp'
    commands = [call.args[0] for call in target.execute.call_args_list]
    assert commands[-2:] == ['chown 123:456 /mails', 'chmod 750 /mails']
    assert not any('0777' in command or '0666' in command for command in commands)


@pytest.mark.parametrize('envelope', [True, False])
def test_mail_is_filtered_by_unique_recipient(tmp_path, envelope):
    """Exclude mail addressed to existing admins sharing the root system mailbox.

    :id: 1d7b2f49-0260-466f-9a6d-1f57d0b09b8c
    :steps: Parse a mailbox containing legitimate admin mail and this test's mail.
    :expectedresults: Only mail to the unique test address is returned.
    """
    box = mbox(tmp_path / 'mail')
    try:
        for recipient in ('root@localhost', 'root+test@localhost'):
            message = EmailMessage()
            message['To'] = recipient
            message['Subject'] = 'task-id'
            message.set_content('body')
            box.add(message)
        box.flush()
    finally:
        box.close()
    content = (tmp_path / 'mail').read_text()
    if not envelope:
        content = message.as_string()
    messages = list(notifications._recipient_messages(content, 'root+test@localhost'))
    assert len(messages) == 1
    assert messages[0]['To'] == 'root+test@localhost'


@pytest.mark.parametrize('bind_failure', [True, False])
def test_readiness_identifies_only_successfully_bound_catcher(tmp_path, monkeypatch, bind_failure):
    """Never publish readiness when the catcher fails to acquire its port.

    :id: 255de1f1-234c-4b0c-a0f9-1a5b551df890
    :steps: Start the server with a successful or failing socket bind.
    :expectedresults: Readiness is published only after listen, with the server PID and port.
    """
    server = Mock()
    if bind_failure:
        server.bind.side_effect = OSError('port in use')
    server.getsockname.return_value = ('0.0.0.0', 34567)
    server.accept.side_effect = RuntimeError('stop test server')
    monkeypatch.setattr(mail_catcher.socket, 'socket', Mock(return_value=server))
    monkeypatch.setattr(mail_catcher.os, 'umask', Mock())
    monkeypatch.setattr(mail_catcher.os, 'getpid', Mock(return_value=1234))
    ready = tmp_path / 'ready'
    published_while_writing = []
    write_text = mail_catcher.Path.write_text

    def write_readiness(path, content):
        result = write_text(path, content)
        published_while_writing.append(ready.exists())
        return result

    monkeypatch.setattr(mail_catcher.Path, 'write_text', write_readiness)
    monkeypatch.setattr(mail_catcher.sys, 'argv', ['catcher', '0', str(tmp_path), str(ready)])
    with pytest.raises((OSError, RuntimeError)):
        mail_catcher.main()
    if bind_failure:
        assert not ready.exists()
        server.listen.assert_not_called()
    else:
        assert ready.read_text() == '1234 34567'
        server.listen.assert_called_once()
    assert not ready.with_name('ready.tmp').exists()
    assert published_while_writing == ([] if bind_failure else [False])


def test_admin_fixture_cleans_up_only_its_own_user():
    """Keep legitimate admins intact even if fixture setup fails.

    :id: 4e246a4f-0360-4184-be57-ed8b67a1bee4
    :steps: Raise while enabling mail for a newly created, uniquely addressed admin.
    :expectedresults: The fixture deletes only its own user and never searches for stale admins.
    """
    target = Mock()
    user = target.api.User.return_value.create.return_value
    user.update.side_effect = RuntimeError('setup')
    fixture = notifications.admin_user_with_localhost_email.__wrapped__(
        target, {'address': 'root+test@localhost'}
    )
    with pytest.raises(RuntimeError, match='setup'):
        next(fixture)
    target.api.User.return_value.search.assert_not_called()
    user.delete.assert_called_once()
    assert target.api.User.call_args.kwargs['mail'] == 'root+test@localhost'


@pytest.mark.parametrize('failure', ['readiness', 'pid', 'setting', None])
def test_catcher_setup_always_cleans_completed_steps(tmp_path, monkeypatch, failure):
    """Clean up the catcher and SMTP settings after partial setup failures.

    :id: 64c90538-2dce-4b43-8dd5-6f204b779360
    :steps: Fail readiness, PID verification, SMTP connectivity or a setting update during setup.
    :expectedresults: The started PID is stopped and all attempted settings are restored.
    """
    target = Mock()
    originals = {
        'smtp_authentication': 'login',
        'smtp_user_name': 'existing-user',
        'smtp_enable_starttls_auto': True,
        'smtp_address': 'existing-host',
        'smtp_port': 25,
    }
    settings = {
        name: SimpleNamespace(value=value, update=Mock()) for name, value in originals.items()
    }
    if failure == 'setting':
        settings['smtp_port'].update.side_effect = [RuntimeError('setting failure'), None]
    target.api.Setting.return_value.search.side_effect = lambda query: [
        settings[query['search'].removeprefix('name=')]
    ]

    def execute(command):
        stdout = ''
        if command.startswith('cat ') and command.endswith('catcher.ready'):
            stdout = '123 4567'
        elif command.startswith('cat ') and command.endswith('catcher.pid'):
            stdout = '999' if failure == 'pid' else '123'
        return SimpleNamespace(status=0, stdout=stdout, stderr='')

    target.execute.side_effect = execute
    readiness = Mock(
        side_effect=RuntimeError('readiness failure') if failure == 'readiness' else None
    )
    monkeypatch.setattr(notifications, 'wait_for', readiness)
    monkeypatch.setattr(
        notifications,
        '_mail_catcher_address',
        Mock(
            return_value='10.130.0.1',
            side_effect=AssertionError('SMTP connectivity failure')
            if failure == 'connectivity'
            else None,
        ),
    )

    def setup():
        with ExitStack() as cleanup:
            notifications._setup_mail_catcher(target, str(tmp_path), cleanup)
            assert settings['smtp_authentication'].value == ''
            assert settings['smtp_user_name'].value == ''
            assert settings['smtp_enable_starttls_auto'].value is False
            assert settings['smtp_address'].value == '10.130.0.1'
            assert settings['smtp_port'].value == 4567

    if failure:
        with pytest.raises((RuntimeError, AssertionError), match='failure|different process'):
            setup()
    else:
        setup()
    assert {name: setting.value for name, setting in settings.items()} == originals
    if failure == 'connectivity':
        target.api.Setting.return_value.search.assert_not_called()
    cleanup_command = target.execute.call_args.args[0]
    assert 'kill "$pid"' in cleanup_command
    assert 'pkill' not in cleanup_command


def test_notification_lock_covers_setup_and_cleanup(monkeypatch):
    """Hold the Satellite lock until partial setup cleanup finishes.

    :id: 4e0e7035-d4a7-4d0b-8f82-c75b15083a4b
    :steps: Acquire the remote lock, then fail after creating a catcher resource.
    :expectedresults: Catcher cleanup precedes removal of the lock directory.
    """
    target = Mock(spec=['execute', 'api', 'put'])
    target.execute.return_value = SimpleNamespace(status=0, stdout='/private/mail', stderr='')

    def wait_for(func, func_args, **kwargs):
        return func(*func_args)

    def setup(target, mails_dir, cleanup):
        cleanup.callback(target.execute, 'stop owned catcher')
        raise RuntimeError('setup failure')

    monkeypatch.setattr(notifications, 'wait_for', wait_for)
    monkeypatch.setattr(notifications, '_setup_mail_catcher', setup)
    fixture = notifications.use_smtp_mail_delivery.__wrapped__(target)
    with pytest.raises(RuntimeError, match='setup failure'):
        next(fixture)
    commands = [call.args[0] for call in target.execute.call_args_list]
    assert commands[0] == 'mkdir -m 0700 /run/robottelo-notifications.lock'
    assert commands[-3:] == [
        'stop owned catcher',
        'rm -rf -- /private/mail',
        'rmdir /run/robottelo-notifications.lock',
    ]


@pytest.mark.parametrize('setup_failure', [True, False])
def test_positive_reschedule_uses_application_rake(setup_failure):
    """Run scheduling and restoration inside the Foreman container.

    :id: 45013410-a1d2-48e6-add5-3352b6939cba
    :steps: Reschedule notifications on foremanctl, including a setup failure.
    :expectedresults: Both scheduling and restoration execute rake in the application container.
    """
    target = Mock(spec=['execute'])
    target.execute.side_effect = [
        SimpleNamespace(status=1 if setup_failure else 0, stderr='setup failure'),
        SimpleNamespace(status=0, stderr=''),
    ]
    fixture = notifications.reschedule_long_running_tasks_notification.__wrapped__(target, {})
    if setup_failure:
        with pytest.raises(AssertionError, match='setup failure'):
            next(fixture)
    else:
        next(fixture)
        with pytest.raises(StopIteration):
            next(fixture)
    rake = 'podman exec foreman foreman-rake'
    assert [call.args[0] for call in target.execute.call_args_list] == [
        f'{rake} foreman_tasks:reschedule_long_running_tasks_checker '
        "FOREMAN_TASKS_CHECK_LONG_RUNNING_TASKS_CRONLINE='* * * * *'",
        f'{rake} foreman_tasks:reschedule_long_running_tasks_checker '
        "FOREMAN_TASKS_CHECK_LONG_RUNNING_TASKS_CRONLINE='0 0 * * *'",
    ]


@pytest.mark.parametrize('cleanup_failure', [True, False])
def test_positive_notification_lock_spans_fixture_lifetime(monkeypatch, cleanup_failure):
    """Keep shared mail configuration locked throughout the test and cleanup.

    :id: 2314dcec-404a-413c-b154-e621605fd37d
    :steps: Set up mail delivery, use the yielded fixture and tear down with or without an error.
    :expectedresults: The lock is released after all cleanup, including when cleanup fails.
    """
    target = Mock(spec=['execute', 'api', 'put'])
    target.execute.return_value = SimpleNamespace(status=0, stdout='/private/mail', stderr='')
    stop = Mock(side_effect=RuntimeError('cleanup failure') if cleanup_failure else None)

    def setup(target, mails_dir, cleanup):
        cleanup.callback(stop)

    monkeypatch.setattr(
        notifications, 'wait_for', lambda func, func_args, **kwargs: func(*func_args)
    )
    monkeypatch.setattr(notifications, '_setup_mail_catcher', setup)
    fixture = notifications.use_smtp_mail_delivery.__wrapped__(target)
    config = next(fixture)
    assert config['mailbox'] == f'/private/mail/{config["address"]}'
    assert target.execute.call_args.args[0] == 'mktemp -d /var/tmp/robottelo-mail.XXXXXXXXXX'
    stop.assert_not_called()
    expected_error = RuntimeError if cleanup_failure else StopIteration
    with pytest.raises(expected_error):
        next(fixture)
    stop.assert_called_once()
    assert [call.args[0] for call in target.execute.call_args_list][-2:] == [
        'rm -rf -- /private/mail',
        'rmdir /run/robottelo-notifications.lock',
    ]


@pytest.mark.parametrize(
    ('network_mode', 'reachable'),
    [
        ('bridge', 'host.containers.internal'),
        ('bridge', '10.130.0.1'),
        ('bridge', 'satellite.example.test'),
        ('host', '127.0.0.1'),
        ('bridge', None),
    ],
)
def test_positive_catcher_address_requires_container_smtp(network_mode, reachable):
    """Use only an address verified by SMTP from the application container.

    :id: 6521a02f-a5fe-44d1-993e-477fd25a150c
    :steps: Probe aliases, duplicate network gateways, the host name and host networking.
    :expectedresults: The first reachable address is selected; total failure reports diagnostics.
    """
    import json
    from shlex import split

    networks = {
        'core': {'Gateway': '10.130.0.1'},
        'other': {'Gateway': '10.130.0.1'},
        'ipv6': {'IPv6Gateway': 'fd00:10:130::1'},
    }
    network_info = f'{network_mode} {json.dumps(None if network_mode == "host" else networks)}'
    target = Mock(hostname='satellite.example.test', spec=['hostname', 'execute'])

    def execute(command):
        if command.startswith('podman inspect'):
            return SimpleNamespace(status=0, stdout=network_info, stderr='')
        address = split(command)[-2]
        return SimpleNamespace(
            status=0 if address == reachable else 1, stdout='', stderr='Connection refused'
        )

    target.execute.side_effect = execute
    if reachable:
        assert notifications._mail_catcher_address(target, 4567) == reachable
    else:
        with pytest.raises(AssertionError, match='No reachable SMTP catcher') as exc:
            notifications._mail_catcher_address(target, 4567)
        assert 'satellite.example.test: Connection refused' in str(exc.value)
    probes = [
        split(call.args[0])
        for call in target.execute.call_args_list
        if call.args[0].startswith('podman exec')
    ]
    candidates = ['host.containers.internal', '10.130.0.1', 'satellite.example.test']
    if network_mode == 'host':
        candidates = ['host.containers.internal', '127.0.0.1', 'satellite.example.test']
    expected = candidates if reachable is None else candidates[: candidates.index(reachable) + 1]
    assert [probe[-2] for probe in probes] == expected
    assert {tuple(probe[:7]) for probe in probes} == {
        ('podman', 'exec', 'foreman', 'ruby', '-rsocket', '-rtimeout', '-e')
    }
    assert {probe[-1] for probe in probes} == {'4567'}


@pytest.mark.parametrize('valid_greeting', [True, False])
def test_positive_catcher_probe_checks_smtp_protocol(valid_greeting):
    """Execute the Ruby probe against a real catcher or an unrelated TCP service.

    :id: aacbea64-76c4-4f57-847a-173576642d89
    :steps: Run the container's probe code locally against a server with valid or invalid SMTP.
    :expectedresults: A working SMTP dialogue succeeds; an unrelated listener is rejected.
    """
    from shlex import split
    from shutil import which
    import subprocess

    ruby = which('ruby')
    if ruby is None:
        pytest.skip('Ruby is required to execute the container SMTP probe locally')
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(('127.0.0.1', 0))
    listener.listen(1)
    listener.settimeout(5)
    port = listener.getsockname()[1]

    def serve():
        connection, _ = listener.accept()
        if valid_greeting:
            mail_catcher.handle(connection)
        else:
            with connection:
                connection.sendall(b'220 unrelated service\r\n')

    worker = threading.Thread(target=serve, daemon=True)
    worker.start()
    target = Mock(hostname='satellite.example.test', spec=['hostname', 'execute'])

    def execute(command):
        if command.startswith('podman inspect'):
            return SimpleNamespace(status=0, stdout='host null', stderr='')
        args = split(command)
        if args[-2] != '127.0.0.1':
            return SimpleNamespace(status=1, stdout='', stderr='Name resolution failed')
        result = subprocess.run(
            [ruby, *args[4:]], capture_output=True, text=True, check=False, timeout=10
        )
        return SimpleNamespace(status=result.returncode, stdout=result.stdout, stderr=result.stderr)

    target.execute.side_effect = execute
    try:
        if valid_greeting:
            assert notifications._mail_catcher_address(target, port) == '127.0.0.1'
        else:
            with pytest.raises(AssertionError, match='Unexpected SMTP greeting'):
                notifications._mail_catcher_address(target, port)
    finally:
        listener.close()
        worker.join(timeout=5)
    assert not worker.is_alive()
