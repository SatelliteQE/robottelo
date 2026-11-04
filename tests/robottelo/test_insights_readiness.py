"""Tests for the non-mutating Insights registration readiness check."""

import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from pytest_fixtures.component.rh_cloud import enable_insights
from robottelo.exceptions import ContentHostError
from robottelo.hosts import ContentHost
from robottelo.utils.insights_readiness import poll_registration, select_client_core


def response(status, body=None):
    return SimpleNamespace(status_code=status, json=Mock(return_value=body))


@pytest.mark.parametrize('transient_status', [403, 404])
def test_poll_waits_for_registration(transient_status):
    """Wait for a transient response to become a confirmed registration.

    :id: cab90283-9270-44c3-baff-ca81c3f33baf
    :steps: Poll after a temporary error followed by a successful response.
    :expectedresults: Registration is confirmed without changing client state.
    """
    session = SimpleNamespace(
        get=Mock(side_effect=[response(transient_status), response(200, {'unregistered_at': None})])
    )
    now = [0]

    def wait(seconds):
        now[0] += seconds

    ready, message = poll_registration(session, 'https://example.test', 10, lambda: now[0], wait)

    assert ready
    assert message == 'Insights API confirms registration'
    assert session.get.call_count == 2


def test_poll_stops_at_ten_seconds():
    """Bound polling when registration never appears.

    :id: a218f137-50ba-4383-87d3-88c7367a4cff
    :steps: Poll an endpoint that always returns 404.
    :expectedresults: The check fails at the deadline with the last response.
    """
    session = SimpleNamespace(get=Mock(return_value=response(404)))
    now = [0]

    def wait(seconds):
        now[0] += seconds

    ready, message = poll_registration(session, 'https://example.test', 10, lambda: now[0], wait)

    assert not ready
    assert 'last HTTP 404' in message
    assert now[0] == 10
    assert session.get.call_count == 10


def test_poll_rejects_response_after_deadline():
    """Do not accept registration after the polling deadline.

    :id: 833dc081-9d20-4393-8260-e1760cefc287
    :steps: Return a successful response after the ten-second deadline.
    :expectedresults: The readiness check reports a timeout.
    """
    now = [0]

    def get(*args, **kwargs):
        now[0] = 10
        return response(200, {'unregistered_at': None})

    ready, message = poll_registration(
        SimpleNamespace(get=get), 'https://example.test', 10, lambda: now[0]
    )

    assert not ready
    assert 'Timed out' in message


@pytest.mark.parametrize(
    'result',
    [response(500), response(200, {}), response(200, {'unregistered_at': '2026-01-01'})],
)
def test_poll_rejects_nontransient_or_unregistered_response(result):
    """Do not treat server errors or unregistered responses as readiness.

    :id: 8a89b9b5-fc77-4454-98c9-d8cbf66d75e2
    :steps: Poll responses that do not confirm registration.
    :expectedresults: The check fails immediately.
    """
    session = SimpleNamespace(get=Mock(return_value=result))
    ready, _ = poll_registration(session, 'https://example.test', 10, lambda: 0, Mock())

    assert not ready
    assert session.get.call_count == 1


class StubHost:
    hostname = 'test-host'
    wait_for_insights_registration = ContentHost.wait_for_insights_registration
    check_insights_registration = ContentHost.check_insights_registration

    def __init__(self, results):
        self.execute = Mock(side_effect=results)


def test_status_is_checked_only_after_readiness():
    """Run the mutating client status command only after the read-only check.

    :id: 5b2f5bbd-e194-4606-90e2-2649d414f675
    :steps: Check hosted registration with a successful readiness probe.
    :expectedresults: The probe runs before the status command.
    """
    status = SimpleNamespace(status=0, stdout='registered')
    host = StubHost([SimpleNamespace(status=0, stdout='ready'), status])

    result = host.check_insights_registration(SimpleNamespace(iop_enabled=False))

    assert result is status
    assert 'timeout -k 1s 11s' in host.execute.call_args_list[0].args[0]
    assert host.execute.call_args_list[1].args[0] == 'insights-client --status'


def test_failed_readiness_never_runs_status():
    """Preserve local registration if the readiness check fails.

    :id: d8f9d511-16c0-49d2-b8bb-c5df24d28f08
    :steps: Check hosted registration when the readiness probe fails.
    :expectedresults: The error is reported and status is not executed.
    """
    host = StubHost([SimpleNamespace(status=1, stdout='last HTTP 404')])

    with pytest.raises(ContentHostError, match='last HTTP 404'):
        host.check_insights_registration(SimpleNamespace(iop_enabled=False))

    assert host.execute.call_count == 1


def test_iop_does_not_poll_hosted_endpoint():
    """Keep IoP's existing status behavior.

    :id: 77d8f237-a480-4582-b8bb-90996d8b08ba
    :steps: Check registration on an IoP Satellite.
    :expectedresults: Status runs without the hosted readiness probe.
    """
    host = StubHost([SimpleNamespace(status=0, stdout='registered')])

    host.check_insights_registration(SimpleNamespace(iop_enabled=True))

    host.execute.assert_called_once_with('insights-client --status')


def test_hosted_fixture_requires_api_confirmation():
    """Do not accept a local marker after a failed hosted status check.

    :id: 2ea52304-8eff-4c09-b27c-39c05f110831
    :steps: Return a failed status with the local-registration message.
    :expectedresults: The hosted fixture fails instead of accepting the marker.
    """
    host = SimpleNamespace(
        hostname='test-host',
        os_version=SimpleNamespace(major=9),
        configure_rex=Mock(),
        configure_insights_client=Mock(),
        check_insights_registration=Mock(
            return_value=SimpleNamespace(
                status=1, stdout='System is registered locally via .registered file'
            )
        ),
    )

    with pytest.raises(AssertionError, match='not registered'):
        enable_insights(host, SimpleNamespace(iop_enabled=False), Mock(), Mock())


def test_iop_fixture_accepts_local_registration():
    """Preserve the IoP fixture's local-registration check.

    :id: 089be963-5490-4d61-9567-8267f15c7f87
    :steps: Return the IoP local-registration message.
    :expectedresults: The fixture accepts the existing IoP behavior.
    """
    host = SimpleNamespace(
        hostname='test-host',
        os_version=SimpleNamespace(major=9),
        configure_rex=Mock(),
        configure_insights_client=Mock(),
        check_insights_registration=Mock(
            return_value=SimpleNamespace(
                status=1, stdout='System is registered locally via .registered file'
            )
        ),
    )

    enable_insights(host, SimpleNamespace(iop_enabled=True), Mock(), Mock())

    host.check_insights_registration.assert_called_once()


@pytest.mark.parametrize(
    'available_egg', ['/var/lib/insights/newest.egg', '/var/lib/insights/last_stable.egg']
)
def test_selects_the_core_used_for_registration(tmp_path, monkeypatch, available_egg):
    """Use the actual Core location recorded for the registration upload.

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
