"""Wait for the hosted Insights legacy registration lookup without changing client state.

This module also runs on the content host. It uses the same Insights Core
connection as the client, including its certificate and proxy configuration.

If registration is not ready, collect a snapshot of three views of the host:
legacy registration, platform Inventory, and Advisor. A separate connection
keeps these diagnostic requests from affecting the readiness check. Snapshots
are optional: failures, rate limits, and time limits never decide readiness.
"""

# The remote client can run Python 2 on RHEL 7 content hosts.
# ruff: noqa: UP010, UP024, UP032

from __future__ import print_function

import json
import os
import re
import signal
import sys
import threading
import time
import uuid

TIMEOUT = 600
POLL_INTERVAL = 1
REQUEST_TIMEOUT = 2
MONOTONIC = getattr(time, 'monotonic', time.time)
DIAGNOSTIC_INTERVAL = 60
DIAGNOSTIC_TIMEOUT = 4


# These fields are safe to include in CI logs. Never log complete responses: they
# can contain facts, identity headers, or error messages that echo credentials.
RESPONSE_HEADERS = ('x-rh-insights-request-id', 'x-request-id', 'content-type')
HOST_IDS = ('id', 'insights_id', 'subscription_manager_id', 'satellite_id', 'owner_id')
HOST_TIMESTAMPS = (
    'created',
    'updated',
    'last_check_in',
    'stale_timestamp',
    'stale_warning_timestamp',
    'culled_timestamp',
)
UNREGISTERED_TIMESTAMP = re.compile(
    r'^[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt ][0-9]{2}:[0-9]{2}:[0-9]{2}'
    r'(?:\.[0-9]{1,9})?(?:[Zz]|[+-][0-9]{2}:?[0-9]{2})?\Z'
)


def response_summary(response):
    """Keep HTTP status, safe request IDs and a few known response fields."""
    summary = {'status': response.status_code}
    for name in RESPONSE_HEADERS:
        value = getattr(response, 'headers', {}).get(name, '')
        if value and re.match(r'^[A-Za-z0-9_.:/;= -]{1,160}$', value):
            summary[name] = value

    try:
        body = response.json()
    except (ValueError, TypeError):
        summary['body_kind'] = 'non-JSON'
        return summary
    if not isinstance(body, dict):
        summary['body_kind'] = 'non-object JSON'
        return summary

    # Classify known errors rather than logging the upstream error text.
    detail = body.get('detail', '')
    if hasattr(detail, 'startswith'):  # Also accepts Python 2 unicode strings.
        if 'No AdvisorInventoryHost matches' in detail:
            summary['error_kind'] = 'advisor-host-not-found'
        elif 'System with insights_id' in detail and 'not found' in detail:
            summary['error_kind'] = 'legacy-system-not-found'

    for key in ('total', 'count', 'unregistered_at'):
        if key in body and (body[key] is None or isinstance(body[key], (int, float))):
            summary[key] = body[key]
    value = body.get('unregistered_at')
    if hasattr(value, 'startswith') and UNREGISTERED_TIMESTAMP.match(value):
        summary['unregistered_at'] = value
    return summary


def safe_uuid(value):
    """Normalize an ID, or record that it was invalid without logging its value."""
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return 'invalid UUID'


def host_summary(host):
    """Keep inventory correlation IDs and freshness fields, but not facts or tags."""
    summary = {}
    for key in HOST_IDS:
        value = host.get(key)
        if value is not None:
            summary[key] = safe_uuid(value)

    org_id = str(host.get('org_id', ''))
    if org_id.isdigit():
        summary['org_id'] = org_id
    for key in HOST_TIMESTAMPS:
        if key in host:
            value = host[key]
            if value is None or re.match(r'^[0-9TtZz: .+-]{1,50}$', str(value)):
                summary[key] = value

    reporters = host.get('per_reporter_staleness') or {}
    if isinstance(reporters, dict) and isinstance(reporters.get('puptoo'), dict):
        summary['puptoo'] = host_summary(reporters['puptoo'])
    profile = host.get('system_profile') or {}
    if isinstance(profile, dict) and 'owner_id' in profile:
        owner_id = profile['owner_id']
        summary['system_profile'] = {} if owner_id is None else {'owner_id': safe_uuid(owner_id)}
    return summary


def log_diagnostic(name, data):
    """Print one labeled, structured line for the archived readiness log."""
    print('Insights diagnostic {}: {}'.format(name, json.dumps(data, sort_keys=True)))


class DiagnosticTimeout(BaseException):
    """Escape HTTP-library exception handling when the wall-clock budget expires."""


def interrupt_diagnostic(signum, frame):
    raise DiagnosticTimeout()


class RegistrationDiagnostics(object):  # noqa: UP004 - runs on Python 2 content hosts
    """Collect occasional snapshots without changing the registration polling session."""

    def __init__(self, connection_factory, machine_id, deadline, clock=MONOTONIC):
        self.connection_factory = connection_factory
        self.machine_id = machine_id
        self.deadline = deadline
        self.clock = clock
        self.next_snapshot = 0

    def collect(self, registration_response=None, error=None, recovered=False):
        """Collect at most once a minute on failure, and once more on recovery."""
        now = self.clock()
        if not recovered and now < self.next_snapshot:
            return
        if self.deadline - now < DIAGNOSTIC_TIMEOUT + 1:
            print('Insights diagnostic snapshot skipped: readiness deadline is near')
            return
        if signal.getitimer(signal.ITIMER_REAL)[0]:
            print('Insights diagnostic snapshot skipped: another timer is active')
            return

        # A requests timeout only limits socket inactivity. DNS, redirects and
        # streaming can take longer, so bound the whole snapshot with SIGALRM.
        # This helper runs on the main thread of a dedicated Linux process.
        previous_handler = signal.signal(signal.SIGALRM, interrupt_diagnostic)
        try:
            signal.setitimer(signal.ITIMER_REAL, DIAGNOSTIC_TIMEOUT)
            self.next_snapshot = now + DIAGNOSTIC_INTERVAL
            self._collect_snapshot(registration_response, error, recovered)
        except DiagnosticTimeout:
            print('Insights diagnostic snapshot exceeded its wall-clock budget')
        except Exception as exc:
            print('Insights diagnostic snapshot failed ({})'.format(type(exc).__name__))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)
            sys.stdout.flush()

    def _collect_snapshot(self, registration_response, error, recovered):
        """Compare legacy registration with Inventory and Advisor visibility."""
        log_diagnostic(
            'snapshot',
            {
                'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'machine_id': self.machine_id,
                'recovered': recovered,
            },
        )
        registration = (
            response_summary(registration_response)
            if registration_response is not None
            else {'error': error}
        )
        log_diagnostic('registration', registration)

        # Use the client's configuration and identity, but a fresh session so
        # diagnostic cookies or interrupted requests cannot affect polling.
        connection = self.connection_factory()
        try:
            # Keep the legacy root and Satellite forwarding route, like Insights Core.
            base = connection.api_url + '/platform'
            inventory = connection.session.get(
                base + '/inventory/v1/hosts',
                params={'insights_id': self.machine_id, 'fields[system_profile]': 'owner_id'},
                timeout=REQUEST_TIMEOUT,
            )
            log_diagnostic('inventory', response_summary(inventory))
            if inventory.status_code != 200:
                return

            hosts = inventory.json().get('results', [])
            log_diagnostic(
                'correlation',
                {
                    'machine_id': self.machine_id,
                    'hosts': [host_summary(host) for host in hosts[:5]],
                },
            )
            if not hosts or self.deadline - self.clock() < REQUEST_TIMEOUT + 1:
                return

            inventory_id = str(uuid.UUID(hosts[0]['id']))
            advisor = connection.session.get(
                base + '/insights/v1/system/' + inventory_id,
                timeout=REQUEST_TIMEOUT,
            )
            log_diagnostic('advisor', response_summary(advisor))
        finally:
            connection.session.close()


def select_client_core(log_path='/var/log/insights-client/insights-client.log'):
    """Select the Core that handled the initial upload, when recorded in the log."""
    try:
        with open(log_path, 'rb') as stream:
            stream.seek(0, os.SEEK_END)
            stream.seek(max(0, stream.tell() - 2 * 1024 * 1024))
            log = stream.read().decode('utf-8', errors='replace')
    except (IOError, OSError):
        return

    pattern = (
        r'path=(\S+)/insights/client/client\.py, version=[^,]+, '
        r'phase=collect_and_output, arguments=[^\n]*--register\b'
    )
    matches = list(re.finditer(pattern, log))
    if not matches:
        return
    root = matches[-1].group(1)
    if root == '/var/lib/insights/newest.egg' and not os.path.exists(root):
        # A successful upload moves the new Core to last_stable.egg.
        root = '/var/lib/insights/last_stable.egg'
    allowed_eggs = (
        '/var/lib/insights/newest.egg',
        '/var/lib/insights/last_stable.egg',
        '/etc/insights-client/rpm.egg',
    )
    system_site = re.match(r'^/usr/(?:local/)?lib(?:64)?/python[\d.]+/site-packages$', root)
    if (root in allowed_eggs or system_site) and os.path.exists(root):
        sys.path.insert(0, root)
    else:
        raise RuntimeError(
            'The Insights Core used for registration is unavailable: {}'.format(root)
        )


def poll_registration(
    session, url, deadline, clock=MONOTONIC, wait=None, started=None, diagnostics=None
):
    """Poll transient responses and read timeouts without changing client state."""
    from requests.exceptions import ReadTimeout

    wait = wait or threading.Event().wait
    started = clock() if started is None else started
    last_status = None
    last_error = None
    had_failure = False

    def diagnose(response=None, error=None, recovered=False):
        if diagnostics is None:
            return
        try:
            diagnostics(response, error=error, recovered=recovered)
        except Exception as exc:
            print('Insights diagnostics failed ({})'.format(type(exc).__name__))

    def timeout_message():
        detail = 'last HTTP {}'.format(last_status or 'none')
        if last_error:
            detail += '; last request {}'.format(last_error)
        return 'Timed out waiting for Insights registration ({})'.format(detail)

    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            return False, timeout_message()
        try:
            response = session.get(url, timeout=min(REQUEST_TIMEOUT, remaining))
        except ReadTimeout:
            last_error = 'ReadTimeout'
            print('Insights registration lookup: ReadTimeout (+{:.2f}s)'.format(clock() - started))
            sys.stdout.flush()
            had_failure = True
            diagnose(error='ReadTimeout')
        except Exception as exc:
            error = type(exc).__name__
            diagnose(error=error)
            return False, 'Insights registration request failed ({})'.format(error)
        else:
            last_error = None
            last_status = response.status_code
            print(
                'Insights registration lookup: HTTP {} (+{:.2f}s)'.format(
                    last_status, clock() - started
                )
            )
            sys.stdout.flush()
            if clock() >= deadline:
                return False, timeout_message()
            # Decide readiness from this response before collecting diagnostics.
            # First-request success adds no diagnostic traffic or status delay.
            if last_status == 200:
                try:
                    body = response.json()
                except (ValueError, TypeError):
                    diagnose(response)
                    return False, 'Insights returned an invalid registration response'
                if (
                    isinstance(body, dict)
                    and 'unregistered_at' in body
                    and body['unregistered_at'] is None
                ):
                    if had_failure:
                        diagnose(response, recovered=True)
                    return True, 'Insights API confirms registration'
                diagnose(response)
                return False, 'Insights returned an unexpected or unregistered response'
            had_failure = True
            diagnose(response)
            if last_status not in (403, 404):
                return False, 'Insights registration lookup returned HTTP {}'.format(last_status)
        remaining = deadline - clock()
        if remaining > 0:
            wait(min(POLL_INTERVAL, remaining))


def main():
    started = MONOTONIC()
    deadline = started + TIMEOUT
    try:
        select_client_core()
        from insights.client.auto_config import try_auto_configuration
        from insights.client.config import InsightsConfig
        from insights.client.connection import InsightsConnection
        from insights.client.constants import InsightsConstants

        # load_all reads sys.argv; the helper takes no client command-line options.
        sys.argv = ['insights-client']
        config = InsightsConfig().load_all()
        config.http_timeout = REQUEST_TIMEOUT
        try_auto_configuration(config)
        if not config.legacy_upload:
            print('Insights client uses non-legacy mode; no legacy lookup is needed')
            return 0
        with open(InsightsConstants.machine_id_file) as stream:
            machine_id = str(uuid.UUID(stream.read().strip(), version=4))
        connection = InsightsConnection(config)
        url = connection.api_url + '/v1/systems/' + machine_id
        diagnostics = RegistrationDiagnostics(
            lambda: InsightsConnection(config), machine_id, deadline
        )
        ready, message = poll_registration(
            connection.session, url, deadline, started=started, diagnostics=diagnostics.collect
        )
        print(message)
        return 0 if ready else 1
    except RuntimeError as exc:
        print('Could not safely check Insights registration: {}'.format(exc))
        return 1
    except Exception as exc:
        # Avoid printing HTTP responses, machine IDs, or proxy credentials.
        print('Could not safely check Insights registration ({})'.format(type(exc).__name__))
        return 1


if __name__ == '__main__':
    sys.exit(main())
