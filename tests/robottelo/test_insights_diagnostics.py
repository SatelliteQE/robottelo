"""Tests for capturing Insights registration diagnostics after a failure."""

import logging
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from robottelo.utils import insights_diagnostics as diagnostics


def client_phase(arguments, url=None, extra=''):
    """Build a representative client log phase."""
    request = f'NETWORK GET {url}\n' if url else ''
    return (
        f'DEBUG phase=post_update, arguments={arguments}\n'
        'Setting authmethod to CERT\n'
        'Attempting to auto configure CA cert: /etc/rhsm/ca/katello-server-ca.pem\n'
        'Attempting to auto configure proxy: None\n'
        "Found subscription-manager UUID in '/etc/pki/consumer/cert.pem'\n"
        f'{extra}{request}'
    )


def test_replays_failed_status_url_without_rerunning_status(monkeypatch, caplog):
    """Record immediate and delayed GETs with the original host identity."""
    original_url = f'https://satellite.example/redhat_access/r/insights/v1/systems/{uuid4()}'
    host = SimpleNamespace(
        hostname='client',
        session=SimpleNamespace(
            sftp_read=Mock(return_value=client_phase('--status', original_url))
        ),
        execute=Mock(
            side_effect=[
                SimpleNamespace(status=0, stdout='HTTP/1.1 404 Not Found', stderr=''),
                SimpleNamespace(status=0, stdout='HTTP/1.1 200 OK', stderr=''),
            ]
        ),
    )
    sleep = Mock()
    monkeypatch.setattr(diagnostics.time, 'sleep', sleep)

    with caplog.at_level(logging.WARNING):
        diagnostics.capture_insights_failure(host, arguments='--status')

    commands = [call.args[0] for call in host.execute.call_args_list]
    assert len(commands) == 2
    assert commands[0] == commands[1]
    assert original_url in commands[0]
    assert '--cert /etc/pki/consumer/cert.pem' in commands[0]
    assert '--key /etc/pki/consumer/key.pem' in commands[0]
    assert '--cacert /etc/rhsm/ca/katello-server-ca.pem' in commands[0]
    assert 'insights-client --status' not in commands[0]
    sleep.assert_called_once_with(5)
    assert '404 Not Found' in caplog.text
    assert '200 OK' in caplog.text


def test_missing_latest_request_does_not_replay_an_older_url(monkeypatch):
    """A missing request in the failing invocation must not reuse an earlier URL."""
    old_url = f'https://satellite.example/redhat_access/r/insights/v1/systems/{uuid4()}'
    client_log = client_phase('--status', old_url) + client_phase('--status')
    host = SimpleNamespace(
        hostname='client',
        session=SimpleNamespace(sftp_read=Mock(return_value=client_log)),
        execute=Mock(),
    )
    sleep = Mock()
    monkeypatch.setattr(diagnostics.time, 'sleep', sleep)

    diagnostics.capture_insights_failure(host, arguments='--status')

    host.execute.assert_not_called()
    sleep.assert_not_called()


def test_failed_pre_update_does_not_replay_previous_status_request():
    """A later status command can fail before reaching its post-update phase."""
    old_url = f'https://satellite.example/redhat_access/r/insights/v1/systems/{uuid4()}'
    client_log = client_phase('--status', old_url) + 'DEBUG phase=pre_update, arguments=--status\n'
    assert diagnostics._last_client_phase(client_log, '--status') == ''


@pytest.mark.parametrize(
    'extra',
    ['ENV Proxy: http://proxy.example:3128\n', 'Could not auto configure\n'],
)
def test_unverified_connection_settings_are_not_replayed(extra):
    """Avoid a direct request when the client's connection may have differed."""
    url = f'https://satellite.example/redhat_access/r/insights/v1/systems/{uuid4()}'
    section = diagnostics._last_client_phase(client_phase('--status', url, extra), '--status')
    assert diagnostics._legacy_registration_url(section) is None


def test_capture_plain_client_invocation_without_reusing_status_request(monkeypatch):
    """The Capsule failure uses a plain insights-client command."""
    status_url = f'https://satellite.example/redhat_access/r/insights/v1/systems/{uuid4()}'
    capsule_url = f'https://capsule.example/redhat_access/r/insights/v1/systems/{uuid4()}'
    client_log = client_phase('--status', status_url) + client_phase('', capsule_url)
    host = SimpleNamespace(
        hostname='client',
        session=SimpleNamespace(sftp_read=Mock(return_value=client_log)),
        execute=Mock(return_value=SimpleNamespace(status=0, stdout='HTTP/1.1 200 OK', stderr='')),
    )
    monkeypatch.setattr(diagnostics.time, 'sleep', Mock())

    diagnostics.capture_insights_failure(host, arguments='')

    assert host.execute.call_count == 2
    assert capsule_url in host.execute.call_args_list[0].args[0]


def test_missing_client_log_does_not_raise():
    """Diagnostics must not replace the original test failure."""
    host = SimpleNamespace(
        hostname='client',
        session=SimpleNamespace(sftp_read=Mock(side_effect=OSError('missing'))),
        execute=Mock(),
    )
    diagnostics.capture_insights_failure(host, arguments='--status')
    host.execute.assert_not_called()


def test_redacts_proxy_credentials_in_client_log():
    """Client logs may contain authenticated proxy URLs."""
    assert diagnostics._redact_url_credentials('proxy http://user:secret@proxy:3128') == (
        'proxy http://<redacted>@proxy:3128'
    )
