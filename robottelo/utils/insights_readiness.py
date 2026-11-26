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

TIMEOUT = 600
POLL_INTERVAL = 1
REQUEST_TIMEOUT = 2
MONOTONIC = getattr(time, 'monotonic', time.time)


def select_client_core(log_path='/var/log/insights-client/insights-client.log'):
    """Select the recorded upload Core, or the older client's bootstrap Core."""
    try:
        with open(log_path, 'rb') as stream:
            stream.seek(0, os.SEEK_END)
            stream.seek(max(0, stream.tell() - 2 * 1024 * 1024))
            # Python 2's str.decode does not accept keyword arguments.
            log = stream.read().decode('utf-8', 'replace')
    except (IOError, OSError):
        # Python 2 cannot use explicit exception chaining.
        raise RuntimeError('Could not read the Insights client Core record')  # noqa: B904

    pattern = (
        r'path=(\S+)/insights/client/client\.py, version=[^,]+, '
        r'phase=collect_and_output, arguments=[^\n]*--register\b'
    )
    matches = list(re.finditer(pattern, log))
    if matches:
        root = matches[-1].group(1)
    else:
        # Older clients (including RHEL 7's 3.1.9) load Core from an egg,
        # but do not log the per-phase Core path. Use their recorded bootstrap
        # Core to read configuration, rather than guessing an installed egg.
        matches = list(re.finditer(r'Loaded initial egg: (\S+)/insights\s*$', log, re.MULTILINE))
        if not matches:
            raise RuntimeError('No Insights client Core record found in the log tail')
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
        print('Insights readiness Core: {}'.format(root))
    else:
        raise RuntimeError('The recorded Insights Core is unavailable or not allowed')


def poll_registration(session, url, deadline, clock=MONOTONIC, wait=None, started=None):
    """Poll transient responses and read timeouts without changing client state."""
    from requests.exceptions import ReadTimeout

    wait = wait or threading.Event().wait
    started = clock() if started is None else started
    last_status = None
    last_error = None

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
        except Exception as exc:
            return False, 'Insights registration request failed ({})'.format(type(exc).__name__)
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


def main():
    started = MONOTONIC()
    deadline = started + TIMEOUT
    stage = 'selecting Insights Core'
    try:
        print('Insights readiness Python: {}.{}'.format(*sys.version_info[:2]))
        select_client_core()
        stage = 'importing Insights Core'
        from insights.client.auto_config import try_auto_configuration
        from insights.client.config import InsightsConfig
        from insights.client.connection import InsightsConnection
        from insights.client.constants import InsightsConstants

        # load_all reads sys.argv; the helper takes no client command-line options.
        stage = 'loading client configuration'
        sys.argv = ['insights-client']
        config = InsightsConfig().load_all()
        config.http_timeout = REQUEST_TIMEOUT
        try_auto_configuration(config)
        if not config.legacy_upload:
            print('Insights client uses non-legacy mode; no legacy lookup is needed')
            return 0
        stage = 'reading machine identity'
        with open(InsightsConstants.machine_id_file) as stream:
            machine_id = str(uuid.UUID(stream.read().strip(), version=4))
        stage = 'checking registration'
        connection = InsightsConnection(config)
        url = connection.api_url + '/v1/systems/' + machine_id
        ready, message = poll_registration(connection.session, url, deadline, started=started)
        print(message)
        return 0 if ready else 1
    except Exception as exc:
        # Avoid printing HTTP responses, machine IDs, or proxy credentials.
        print(
            'Could not safely check Insights registration while {} ({})'.format(
                stage, type(exc).__name__
            )
        )
        return 1


if __name__ == '__main__':
    sys.exit(main())
