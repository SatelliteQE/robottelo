"""Tests for the non-mutating Insights registration readiness check."""

from contextlib import nullcontext
from io import BytesIO
from pathlib import Path
import shlex
import sys
import tarfile
from types import SimpleNamespace
from unittest.mock import Mock, call

from broker.binds.hussh import Session as HusshSession
from broker.binds.paramiko import Session as ParamikoSession
from broker.binds.ssh2 import Session as SSH2Session
import pytest
from requests.exceptions import ReadTimeout, SSLError

from pytest_fixtures.component.rh_cloud import enable_insights
from robottelo.exceptions import ContentHostError
from robottelo.hosts import ContentHost
from robottelo.utils import insights_diagnostics, insights_readiness
from robottelo.utils.insights_readiness import TIMEOUT, poll_registration, select_client_core


def response(status, body=None):
    return SimpleNamespace(status_code=status, json=Mock(return_value=body))


class Clock:
    """Advance the polling clock without waiting in real time."""

    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now

    def wait(self, seconds):
        self.now += seconds


class StubHost:
    hostname = 'test-host'
    wait_for_insights_registration = ContentHost.wait_for_insights_registration
    check_insights_registration = ContentHost.check_insights_registration

    def __init__(self, results):
        self.execute = Mock(side_effect=results)
        self._settings = SimpleNamespace(SSH=SimpleNamespace(BACKEND='hussh'))
        self.os_version = SimpleNamespace(major=9)


@pytest.mark.parametrize(
    'transient',
    [
        [response(403)],
        [response(404)] * 599,
        [ReadTimeout('private details'), response(404)],
    ],
    ids=['403', '404-near-deadline', 'read-timeout'],
)
def test_positive_poll_waits_for_registration(transient, capsys):
    """Retry transient errors until the API confirms registration.

    :id: cab90283-9270-44c3-baff-ca81c3f33baf
    :steps: Poll temporary errors followed by a registered response.
    :expectedresults: Registration is confirmed within the deadline.
    """
    clock = Clock()
    session = SimpleNamespace(
        get=Mock(side_effect=transient + [response(200, {'unregistered_at': None})])
    )

    ready, message = poll_registration(session, 'https://example.test', TIMEOUT, clock, clock.wait)

    assert ready
    assert message == 'Insights API confirms registration'
    assert session.get.call_count == len(transient) + 1
    assert 'private details' not in capsys.readouterr().out


@pytest.mark.parametrize('transient', [403, 404, 'timeout'])
def test_negative_poll_stops_at_six_hundred_seconds(transient):
    """Bound polling when registration never appears.

    :id: a218f137-50ba-4383-87d3-88c7367a4cff
    :steps: Poll an endpoint that keeps returning a transient error.
    :expectedresults: The check fails at the deadline with the last response or error.
    """
    clock = Clock()
    get = (
        Mock(side_effect=ReadTimeout('private details'))
        if transient == 'timeout'
        else Mock(return_value=response(transient))
    )

    ready, message = poll_registration(
        SimpleNamespace(get=get), 'https://example.test', TIMEOUT, clock, clock.wait
    )

    assert not ready
    assert TIMEOUT == 600
    assert clock.now == 600
    assert get.call_count == 600
    assert (
        'last request ReadTimeout' if transient == 'timeout' else f'last HTTP {transient}'
    ) in message
    assert 'private details' not in message


def test_negative_poll_rejects_response_after_deadline():
    """Do not accept registration after the polling deadline.

    :id: 833dc081-9d20-4393-8260-e1760cefc287
    :steps: Return a successful response at the deadline.
    :expectedresults: The readiness check reports a timeout.
    """
    clock = Clock()

    def get(*args, **kwargs):
        clock.now = TIMEOUT
        return response(200, {'unregistered_at': None})

    ready, message = poll_registration(
        SimpleNamespace(get=get), 'https://example.test', TIMEOUT, clock
    )

    assert not ready
    assert 'Timed out' in message


@pytest.mark.parametrize(
    'result',
    [
        response(500),
        response(200, {}),
        response(200, {'unregistered_at': '2026-01-01'}),
        SSLError('private details'),
    ],
    ids=['server-error', 'missing-registration', 'unregistered', 'certificate-error'],
)
def test_negative_poll_rejects_nontransient_or_unregistered_response(result):
    """Do not treat server errors or unregistered responses as readiness.

    :id: 8a89b9b5-fc77-4454-98c9-d8cbf66d75e2
    :steps: Poll responses that do not confirm registration.
    :expectedresults: The check fails immediately without exposing error details.
    """
    get = Mock(side_effect=result) if isinstance(result, Exception) else Mock(return_value=result)
    wait = Mock()

    ready, message = poll_registration(
        SimpleNamespace(get=get), 'https://example.test', 10, lambda: 0, wait
    )

    assert not ready
    assert 'private details' not in message
    get.assert_called_once()
    wait.assert_not_called()


@pytest.mark.parametrize(
    'scenario',
    [
        'ready',
        'timeout',
        'missing-log',
        'transport-error',
        'artifact-unavailable',
        'pylibssh',
        'container',
    ],
)
def test_positive_status_is_checked_only_after_readiness(scenario, tmp_path, monkeypatch):
    """Run client status only after the non-mutating readiness check succeeds.

    :id: 5b2f5bbd-e194-4606-90e2-2649d414f675
    :steps: Check registration after a successful or failed readiness probe.
    :expectedresults: Status runs only after success; failures save sanitized diagnostics.
    """
    readiness_succeeded = scenario == 'ready'
    probe = SimpleNamespace(
        status=0 if readiness_succeeded else 1, stdout='Timed out waiting for Insights registration'
    )
    if scenario == 'transport-error':
        probe = RuntimeError('readiness transport error')
    status = SimpleNamespace(status=0, stdout='registered')
    package = SimpleNamespace(status=0, stdout='insights-client-3.9.3-1.el9.noarch')
    host = StubHost([probe, status if readiness_succeeded else package])
    if scenario == 'pylibssh':
        host._settings.SSH.BACKEND = 'pylibssh'
    client_log = (
        b'Registration started\n'
        b'RHSM Proxy: http://user:proxy-secret@example.test\n'
        b'Authorization: Bearer private-token\n'
        b'Connecting to https://alice:p@ss@example.test/\n'
        b'-----BEGIN PRIVATE KEY-----\nprivate-key-body\n-----END PRIVATE KEY-----\n'
        b'HTTP 404\n'
    )
    sftp_read = Mock(return_value=client_log)
    if scenario == 'missing-log':
        sftp_read.side_effect = FileNotFoundError('private details')
    if scenario == 'container':

        class ContainerSession:
            pass

        monkeypatch.setitem(
            sys.modules, 'broker.session', SimpleNamespace(ContainerSession=ContainerSession)
        )
        host.is_container = True
        data = BytesIO()
        with tarfile.open(fileobj=data, mode='w') as archive:
            member = tarfile.TarInfo(name=Path(insights_diagnostics.CLIENT_LOG).name)
            member.size = len(client_log)
            archive.addfile(member, BytesIO(client_log))
        sftp_read.return_value = data.getvalue()
        host.session = ContainerSession()
        host.session.sftp_read = sftp_read
    else:
        host.session = SimpleNamespace(sftp_read=sftp_read)
    monkeypatch.setattr(insights_diagnostics, 'robottelo_log_dir', tmp_path)
    if scenario == 'artifact-unavailable':
        monkeypatch.setattr(
            insights_diagnostics, 'NamedTemporaryFile', Mock(side_effect=PermissionError())
        )
    error = RuntimeError if scenario == 'transport-error' else ContentHostError
    message = 'readiness transport error' if scenario == 'transport-error' else 'Timed out waiting'
    expected = nullcontext() if readiness_succeeded else pytest.raises(error, match=message)

    with expected as caught:
        result = host.check_insights_registration(SimpleNamespace(iop_enabled=False))

    assert 'timeout -k 1s 601s ' in host.execute.call_args_list[0].args[0]
    if readiness_succeeded:
        assert result is status
        assert host.execute.call_args_list[1].args[0] == 'insights-client --status'
        sftp_read.assert_not_called()
        assert not list(tmp_path.glob('insights-readiness-*.log'))
    else:
        assert host.execute.call_args_list[1].args[0] == 'rpm -q insights-client'
        assert all(c.args[0] != 'insights-client --status' for c in host.execute.call_args_list)
        if scenario == 'container':
            sftp_read.assert_called_once_with(
                insights_diagnostics.CLIENT_LOG, destination='_raw', return_data=True
            )
        elif scenario == 'pylibssh':
            assert sftp_read.call_args.args == (insights_diagnostics.CLIENT_LOG,)
            assert sftp_read.call_args.kwargs['return_data'] is True
            assert not Path(sftp_read.call_args.kwargs['destination']).exists()
        else:
            sftp_read.assert_called_once_with(insights_diagnostics.CLIENT_LOG, return_data=True)
        artifacts = list(tmp_path.glob('insights-readiness-*.log'))
        if scenario == 'artifact-unavailable':
            assert not artifacts
            assert 'Diagnostics could not be saved' in str(caught.value)
            return
        assert len(artifacts) == 1
        assert artifacts[0].stat().st_mode & 0o777 == 0o600
        contents = artifacts[0].read_text()
        assert 'insights-client-3.9.3-1.el9.noarch' in contents
        if scenario == 'missing-log':
            assert 'Could not read client log (FileNotFoundError)' in contents
        else:
            assert 'Registration started' in contents
            assert 'HTTP 404' in contents
            assert 'proxy-secret' not in contents
            assert 'private-token' not in contents
            assert 'p@ss' not in contents
            assert 'private-key-body' not in contents
    assert host.execute.call_count == 2


@pytest.mark.parametrize('failure', ['nonzero', 'transport-error'])
def test_negative_client_status_failure_saves_diagnostics(failure, tmp_path, monkeypatch):
    """Capture diagnostics if status fails after readiness succeeds.

    :id: ec4f8286-8a68-4629-bb77-db8e0e24f1fd
    :steps: Simulate a failed client status after a successful readiness check.
    :expectedresults: A sanitized log and client version are saved without changing the result.
    """
    probe = SimpleNamespace(status=0, stdout='ready')
    status = SimpleNamespace(status=1, stdout='unregistered')
    status_result = (
        RuntimeError('status transport error') if failure == 'transport-error' else status
    )
    package = SimpleNamespace(status=0, stdout='insights-client-3.9.3-1.el9.noarch')
    host = StubHost([probe, status_result, package])
    host.session = SimpleNamespace(sftp_read=Mock(return_value=b'Client log\n'))
    monkeypatch.setattr(insights_diagnostics, 'robottelo_log_dir', tmp_path)
    expected = (
        pytest.raises(RuntimeError, match='status transport error')
        if failure == 'transport-error'
        else nullcontext()
    )

    with expected:
        result = host.check_insights_registration(SimpleNamespace(iop_enabled=False))

    if failure == 'nonzero':
        assert result is status
    assert host.execute.call_args_list[1].args[0] == 'insights-client --status'
    artifacts = list(tmp_path.glob('insights-readiness-*.log'))
    assert len(artifacts) == 1
    contents = artifacts[0].read_text()
    assert 'insights-client-3.9.3-1.el9.noarch' in contents
    assert 'Client log' in contents


@pytest.mark.parametrize('backend', ['hussh', 'ssh2-python', 'paramiko'])
def test_positive_readiness_uses_correct_ssh_timeout(backend):
    """Give each Broker SSH backend enough time for the bounded probe.

    :id: 22f31b01-8ddb-4e68-aec1-a11bafe71a1c
    :steps: Run readiness through each backend with a simulated SSH connection.
    :expectedresults: Each connection receives a 603-second transport timeout.
    """
    host = StubHost([])
    host._settings.SSH.BACKEND = backend
    if backend == 'hussh':
        session = object.__new__(HusshSession)
        session.session = Mock()
        session.session.execute.return_value = SimpleNamespace(status=0, stdout='ready', stderr='')
    elif backend == 'ssh2-python':
        session = object.__new__(SSH2Session)
        session.session = Mock()
        session._read = Mock(return_value=SimpleNamespace(status=0, stdout='ready', stderr=''))
    else:
        session = object.__new__(ParamikoSession)
        session.client = Mock()
        stdout = Mock()
        stdout.channel.exit_status = 0
        stdout.read.return_value = b'ready'
        stderr = Mock()
        stderr.read.return_value = b''
        session.client.exec_command.return_value = (None, stdout, stderr)

    host.execute.side_effect = lambda command, timeout=None: session.run(command, timeout=timeout)
    host.wait_for_insights_registration(SimpleNamespace(iop_enabled=False))

    assert 'timeout -k 1s 601s ' in host.execute.call_args.args[0]
    if backend == 'hussh':
        assert session.session.execute.call_args.kwargs['timeout'] == 603000
    elif backend == 'ssh2-python':
        session.session.set_timeout.assert_called_once_with(603000)
    else:
        assert session.client.exec_command.call_args.kwargs['timeout'] == 603


def test_positive_iop_does_not_poll_hosted_endpoint():
    """Keep IoP's existing status behavior.

    :id: 77d8f237-a480-4582-b8bb-90996d8b08ba
    :steps: Check registration on an IoP Satellite.
    :expectedresults: Status runs without the hosted readiness probe.
    """
    host = StubHost([SimpleNamespace(status=0, stdout='registered')])

    host.check_insights_registration(SimpleNamespace(iop_enabled=True))

    host.execute.assert_called_once_with('insights-client --status')


@pytest.mark.parametrize(
    ('iop_enabled', 'status', 'output', 'marker_status', 'accepted'),
    [
        pytest.param(False, 0, 'Insights API confirms registration.', None, True, id='legacy'),
        pytest.param(False, 0, 'This host is registered.', None, True, id='non-legacy'),
        pytest.param(
            False,
            1,
            'System is registered locally via .registered file',
            None,
            False,
            id='hosted-status-failed',
        ),
        pytest.param(True, 0, 'This host is registered.', None, True, id='iop-status-success'),
        pytest.param(True, 1, 'Insights API unavailable', 0, True, id='iop-local-registration'),
        pytest.param(
            True,
            1,
            'System is registered locally via .registered file',
            1,
            False,
            id='iop-not-registered',
        ),
    ],
)
def test_insights_fixture_registration_status(iop_enabled, status, output, marker_status, accepted):
    """Accept successful status in either mode and preserve IoP's local fallback.

    :id: 089be963-5490-4d61-9567-8267f15c7f87
    :steps: Check legacy, non-legacy, failed, and IoP status responses.
    :expectedresults: The fixture accepts successful status or an IoP local registration only.
    """
    host = SimpleNamespace(
        hostname='test-host',
        os_version=SimpleNamespace(major=9),
        configure_rex=Mock(),
        configure_insights_client=Mock(),
        check_insights_registration=Mock(
            return_value=SimpleNamespace(status=status, stdout=output)
        ),
        execute=Mock(return_value=SimpleNamespace(status=marker_status)),
    )
    satellite = SimpleNamespace(
        iop_enabled=iop_enabled, generate_inventory_report=Mock(), sync_inventory_status=Mock()
    )
    calls = Mock()
    calls.attach_mock(host.execute, 'check_marker')
    calls.attach_mock(host.check_insights_registration, 'check_status')
    org = Mock()
    expected = nullcontext() if accepted else pytest.raises(AssertionError, match='not registered')

    with expected:
        enable_insights(host, satellite, org, Mock())

    if iop_enabled:
        assert calls.mock_calls == [
            call.check_marker('test -f "${INSIGHTS_CONF_DIR:-/etc/insights-client}/.registered"'),
            call.check_status(satellite),
        ]
    else:
        assert calls.mock_calls == [call.check_status(satellite)]
    if accepted and not iop_enabled:
        satellite.generate_inventory_report.assert_called_once_with(org)
        satellite.sync_inventory_status.assert_called_once_with(org)
    else:
        satellite.generate_inventory_report.assert_not_called()
        satellite.sync_inventory_status.assert_not_called()


@pytest.mark.parametrize(
    'available_egg', ['/var/lib/insights/newest.egg', '/var/lib/insights/last_stable.egg']
)
def test_positive_selects_the_core_used_for_registration(tmp_path, monkeypatch, available_egg):
    """Use the Core location recorded for the registration upload.

    :id: 7bbeb0de-38ff-4468-a117-a9a20f9214b5
    :steps: Read a registration log that identifies a Core egg.
    :expectedresults: The matching egg is placed first on the import path.
    """
    log = tmp_path / 'insights-client.log'
    log.write_text(
        'path=/var/lib/insights/newest.egg/insights/client/client.py, '
        'version=3.8.4, phase=collect_and_output, arguments=--register\n'
    )
    monkeypatch.setattr(
        'robottelo.utils.insights_readiness.os.path.exists', lambda path: path == available_egg
    )
    monkeypatch.setattr(sys, 'path', list(sys.path))

    select_client_core(str(log))

    assert sys.path[0] == available_egg


@pytest.mark.parametrize('major', [7, 8, 9, 10])
def test_positive_readiness_uses_client_python(major):
    """Use Python 2 for RHEL 7 even when an optional Python 3 is installed.

    :id: 3faec50a-3e06-44eb-b32b-4c117acf0b15
    :steps: Build the readiness command for each supported RHEL major version.
    :expectedresults: RHEL 7 selects python2; newer hosts retain their interpreter lookup.
    """
    host = StubHost([SimpleNamespace(status=0, stdout='ready')])
    host.os_version.major = major

    host.wait_for_insights_registration(SimpleNamespace(iop_enabled=False))

    command = host.execute.call_args.args[0]
    assert shlex.split(command)[-3:] == [
        '$python_bin',
        '-c',
        Path(insights_readiness.__file__).read_text(),
    ]
    lookup = command.split(') ', 1)[0]
    if major == 7:
        assert lookup == 'python_bin=$(command -v /usr/bin/python2'
    else:
        assert lookup == (
            'python_bin=$(command -v /usr/libexec/platform-python || command -v python3 '
            '|| command -v python'
        )


@pytest.mark.parametrize('scenario', ['old-log', 'latest-bootstrap', 'modern-log', 'untrusted'])
def test_positive_selects_older_client_bootstrap_core(scenario, tmp_path, monkeypatch):
    """Recognize older client logs without weakening Core path validation.

    :id: a47107e1-7272-4653-bf98-2f1091954e00
    :steps: Select Core from old, mixed-format, or untrusted log entries.
    :expectedresults: The latest bootstrap is used only without an upload Core; unsafe paths fail.
    """
    log = tmp_path / 'client.log'
    contents = 'DEBUG root Loaded initial egg: /etc/insights-client/rpm.egg/insights\n'
    expected = '/etc/insights-client/rpm.egg'
    if scenario == 'latest-bootstrap':
        contents += 'DEBUG root Loaded initial egg: /var/lib/insights/last_stable.egg/insights\n'
        expected = '/var/lib/insights/last_stable.egg'
    if scenario == 'modern-log':
        contents += (
            'path=/var/lib/insights/last_stable.egg/insights/client/client.py, '
            'version=3.8.4, phase=collect_and_output, arguments=--register\n'
        )
        expected = '/var/lib/insights/last_stable.egg'
    if scenario == 'untrusted':
        contents = 'DEBUG root Loaded initial egg: /tmp/untrusted.egg/insights\n'
    log.write_text(contents)
    monkeypatch.setattr(insights_readiness.os.path, 'exists', lambda path: True)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    original_path = list(sys.path)

    if scenario == 'untrusted':
        with pytest.raises(RuntimeError, match='not allowed'):
            select_client_core(str(log))
        assert sys.path == original_path
    else:
        select_client_core(str(log))
        assert sys.path[0] == expected


@pytest.mark.parametrize('scenario', ['missing', 'unreadable', 'unknown', 'outside-tail'])
def test_negative_core_selection_requires_a_log_record(scenario, tmp_path, monkeypatch):
    """Never silently import a different Core from the default Python path.

    :id: 0a17a747-f06a-483f-a75f-23f8e6201eae
    :steps: Select Core from a missing, unreadable, or unrecognized client log.
    :expectedresults: Selection fails explicitly without modifying the Python path.
    """
    log = tmp_path / 'client.log'
    if scenario == 'unreadable':
        log.mkdir()
    elif scenario == 'unknown':
        log.write_text('Unrecognized client output\n')
    elif scenario == 'outside-tail':
        log.write_text(
            'Loaded initial egg: /etc/insights-client/rpm.egg/insights\n' + 'x' * (2 * 1024 * 1024)
        )
    monkeypatch.setattr(sys, 'path', list(sys.path))
    original_path = list(sys.path)

    with pytest.raises(RuntimeError, match='Core record'):
        select_client_core(str(log))

    assert sys.path == original_path


def test_positive_core_log_decoding_uses_python2_signature(monkeypatch):
    """Read an older log with Python 2-compatible decode arguments.

    :id: 555209ec-f685-4e92-9171-dee38dada9c0
    :steps: Read a log through a byte string whose decode accepts only positional arguments.
    :expectedresults: Invalid UTF-8 is replaced and the recorded egg is selected.
    """

    class Python2Bytes(bytes):
        def decode(self, encoding, errors, /):
            return super().decode(encoding, errors)

    stream = BytesIO(b'\xff DEBUG root Loaded initial egg: /etc/insights-client/rpm.egg/insights\n')
    read = stream.read
    stream.read = lambda: Python2Bytes(read())
    monkeypatch.setattr('builtins.open', Mock(return_value=stream))
    monkeypatch.setattr(insights_readiness.os.path, 'exists', lambda path: True)
    monkeypatch.setattr(sys, 'path', list(sys.path))

    select_client_core()

    assert sys.path[0] == '/etc/insights-client/rpm.egg'


def test_negative_core_import_failure_identifies_stage(monkeypatch, capsys):
    """Identify import failures without leaking exception details.

    :id: 3c9f3294-dcff-4a97-a6d4-b2422df36b73
    :steps: Run the helper with an unavailable Insights Core import.
    :expectedresults: Failure identifies the import stage but does not expose exception text.
    """
    monkeypatch.setattr(insights_readiness, 'select_client_core', Mock())
    monkeypatch.setitem(sys.modules, 'insights.client.auto_config', None)

    assert insights_readiness.main() == 1

    output = capsys.readouterr().out
    assert 'importing Insights Core (ModuleNotFoundError)' in output


def test_positive_older_core_nonlegacy_mode_does_not_poll(monkeypatch, capsys):
    """Allow an older bootstrapped Core to bypass the legacy-only lookup.

    :id: 6ef9c055-3535-42f7-93d5-b6ae706fa702
    :steps: Load client configuration that auto-configuration switches to non-legacy mode.
    :expectedresults: The helper succeeds without reading identity or constructing a connection.
    """
    config = SimpleNamespace(legacy_upload=True)
    auto_config = Mock(side_effect=lambda config: setattr(config, 'legacy_upload', False))
    connection = Mock()
    modules = {
        'insights.client.auto_config': SimpleNamespace(try_auto_configuration=auto_config),
        'insights.client.config': SimpleNamespace(
            InsightsConfig=Mock(return_value=SimpleNamespace(load_all=Mock(return_value=config)))
        ),
        'insights.client.connection': SimpleNamespace(InsightsConnection=connection),
        'insights.client.constants': SimpleNamespace(InsightsConstants=SimpleNamespace()),
    }
    monkeypatch.setattr(insights_readiness, 'select_client_core', Mock())
    monkeypatch.setattr(sys, 'argv', ['readiness'])
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)

    assert insights_readiness.main() == 0

    connection.assert_not_called()
    assert 'non-legacy mode; no legacy lookup is needed' in capsys.readouterr().out
