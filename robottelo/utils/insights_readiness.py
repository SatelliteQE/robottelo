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


def main():
    deadline = MONOTONIC() + TIMEOUT
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
        ready, message = poll_registration(connection.session, url, deadline)
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
