"""Tests for the non-mutating Insights registration readiness check."""

from contextlib import nullcontext
import sys
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


@pytest.mark.parametrize(
    'transient',
    [
        [response(403)],
        [response(404)] * 59,
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
def test_negative_poll_stops_at_sixty_seconds(transient):
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
    assert TIMEOUT == 60
    assert clock.now == 60
    assert get.call_count == 60
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


@pytest.mark.parametrize('readiness_succeeded', [True, False])
def test_positive_status_is_checked_only_after_readiness(readiness_succeeded):
    """Run client status only after the non-mutating readiness check succeeds.

    :id: 5b2f5bbd-e194-4606-90e2-2649d414f675
    :steps: Check registration after a successful or failed readiness probe.
    :expectedresults: Status runs after success and never runs after failure.
    """
    probe = SimpleNamespace(status=0 if readiness_succeeded else 1, stdout='probe result')
    status = SimpleNamespace(status=0, stdout='registered')
    host = StubHost([probe, status])
    expected = nullcontext() if readiness_succeeded else pytest.raises(ContentHostError)

    with expected:
        result = host.check_insights_registration(SimpleNamespace(iop_enabled=False))

    assert 'timeout -k 1s 61s ' in host.execute.call_args_list[0].args[0]
    if readiness_succeeded:
        assert result is status
        assert host.execute.call_args_list[1].args[0] == 'insights-client --status'
    assert host.execute.call_count == (2 if readiness_succeeded else 1)


@pytest.mark.parametrize('backend', ['hussh', 'ssh2-python', 'paramiko'])
def test_positive_readiness_uses_correct_ssh_timeout(backend):
    """Give each Broker SSH backend enough time for the bounded probe.

    :id: 22f31b01-8ddb-4e68-aec1-a11bafe71a1c
    :steps: Run readiness through each backend with a simulated SSH connection.
    :expectedresults: Each connection receives a 63-second transport timeout.
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

    assert 'timeout -k 1s 61s ' in host.execute.call_args.args[0]
    if backend == 'hussh':
        assert session.session.execute.call_args.kwargs['timeout'] == 63000
    elif backend == 'ssh2-python':
        session.session.set_timeout.assert_called_once_with(63000)
    else:
        assert session.client.exec_command.call_args.kwargs['timeout'] == 63


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
