"""Wait for the hosted Insights legacy registration lookup without changing client state.

This module also runs on the content host. It uses the same Insights Core
connection as the client, including its certificate and proxy configuration.
"""

# The remote client can run Python 2 on RHEL 7 content hosts.
# ruff: noqa: UP010, UP024, UP032

from __future__ import print_function

import os
import re
import sys
import threading
import time
import uuid

TIMEOUT = 15
DIAGNOSTIC_TIMEOUT = 60
DIAGNOSTIC_INTERVAL = 2
POLL_INTERVAL = 1
REQUEST_TIMEOUT = 2
MONOTONIC = getattr(time, 'monotonic', time.time)


def select_client_core(log_path='/var/log/insights-client/insights-client.log'):
    """Select the Core that handled the initial upload, when recorded in the log."""
    try:
        with open(log_path, 'rb') as stream:
            stream.seek(0, os.SEEK_END)
            stream.seek(max(0, stream.tell() - 2 * 1024 * 1024))
            log = stream.read().decode('utf-8', errors='replace')
    except (IOError, OSError):
        return None

    pattern = (
        r'path=(\S+)/insights/client/client\.py, version=([^,\s]+), '
        r'phase=collect_and_output, arguments=[^\n]*--register\b'
    )
    matches = list(re.finditer(pattern, log))
    if not matches:
        return None
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
        return matches[-1].group(2)
    raise RuntimeError('The Insights Core used for registration is unavailable: {}'.format(root))


def poll_registration(session, url, deadline, clock=MONOTONIC, wait=None):
    """Poll only transient 403/404 responses; never invoke the mutating status check."""
    wait = wait or threading.Event().wait
    last_status = None
    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            return False, 'Timed out waiting for Insights registration (last HTTP {})'.format(
                last_status or 'none'
            )
        try:
            response = session.get(url, timeout=min(REQUEST_TIMEOUT, remaining))
        except Exception as exc:
            return False, 'Insights registration request failed ({})'.format(type(exc).__name__)
        last_status = response.status_code
        print('Insights registration lookup: HTTP {}'.format(last_status))
        sys.stdout.flush()
        if clock() >= deadline:
            return False, 'Timed out waiting for Insights registration (last HTTP {})'.format(
                last_status
            )
        if last_status == 200:
            try:
                body = response.json()
            except (ValueError, TypeError):
                return False, 'Insights returned an invalid registration response'
            if (
                isinstance(body, dict)
                and 'unregistered_at' in body
                and body['unregistered_at'] is None
            ):
                return True, 'Insights API confirms registration'
            return False, 'Insights returned an unexpected or unregistered response'
        if last_status not in (403, 404):
            return False, 'Insights registration lookup returned HTTP {}'.format(last_status)
        remaining = deadline - clock()
        if remaining > 0:
            wait(min(POLL_INTERVAL, remaining))


def diagnose_registration(session, url, started, clock=MONOTONIC, wait=None):
    """Temporarily continue read-only polling after a failed readiness check."""
    wait = wait or threading.Event().wait
    deadline = clock() + DIAGNOSTIC_TIMEOUT
    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            return False, 'Diagnostic ended without confirmed registration'
        try:
            response = session.get(url, timeout=min(REQUEST_TIMEOUT, remaining))
        except Exception as exc:
            print(
                'Diagnostic +{:.2f}s: request failed ({})'.format(
                    clock() - started, type(exc).__name__
                )
            )
        else:
            print('Diagnostic +{:.2f}s: HTTP {}'.format(clock() - started, response.status_code))
            if response.status_code == 200:
                try:
                    body = response.json()
                except (ValueError, TypeError):
                    body = None
                if (
                    isinstance(body, dict)
                    and 'unregistered_at' in body
                    and body['unregistered_at'] is None
                ):
                    return True, 'Diagnostic confirmed registration after the initial failure'
                print('Diagnostic HTTP 200 did not confirm registration')
        sys.stdout.flush()
        remaining = deadline - clock()
        if remaining > 0:
            wait(min(DIAGNOSTIC_INTERVAL, remaining))


def summarize_client_log(log):
    """Extract known events without archiving credentials or response bodies."""
    if isinstance(log, bytes):
        log = log.decode('utf-8', errors='replace')
    log = log[-2 * 1024 * 1024 :]
    events = ['Selected Insights client log events; other lines omitted.']
    known_events = (
        ('successfully registered host', 'Host registration succeeded'),
        ('successfully uploaded report', 'Insights upload succeeded'),
        ('uploading insights data', 'Insights upload started'),
        ('all attempts to upload have failed', 'Insights upload failed'),
        ('connection timed out', 'Connection timed out'),
    )
    for line in log.splitlines():
        timestamp = re.match(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[,.]\d+)?', line)
        if not timestamp:
            continue
        event = None
        version = re.search(r'(?i)\b(client|core) version:\s*([0-9][\w.+-]{0,39})', line)
        core = re.search(r'\bversion=([0-9][\w.+-]{0,39}), phase=collect_and_output', line)
        status = re.search(
            r'(?i)\b(?:http (?:status|response)(?: code)?|status code|received code|'
            r'bad status from server)\s*[:=]?\s*([1-5]\d{2})\b',
            line,
        )
        if version:
            event = '{} version: {}'.format(version.group(1).capitalize(), version.group(2))
        elif core and '--register' in line:
            event = 'Registration Core version: {}'.format(core.group(1))
        elif status:
            event = 'HTTP status: {}'.format(status.group(1))
        else:
            for phrase, label in known_events:
                if phrase in line.lower():
                    event = label
                    break
        if event:
            events.append('{} {}'.format(timestamp.group(), event))
    return '\n'.join(events) + '\n'


def main():
    started = MONOTONIC()
    deadline = started + TIMEOUT
    try:
        core_version = select_client_core()
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
        ready, message = poll_registration(connection.session, url, deadline)
        print(message)
        if ready:
            return 0
        print('Insights Core from registration log: {}'.format(core_version or 'unknown'))
        print('Continuing read-only diagnostics for up to 60 seconds; the test will still fail')
        _, diagnostic_message = diagnose_registration(connection.session, url, started)
        print(diagnostic_message)
        return 1
    except RuntimeError as exc:
        print('Could not safely check Insights registration: {}'.format(exc))
        return 1
    except Exception as exc:
        # Avoid printing HTTP responses, machine IDs, or proxy credentials.
        print('Could not safely check Insights registration ({})'.format(type(exc).__name__))
        return 1


if __name__ == '__main__':
    sys.exit(main())
