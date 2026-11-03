"""Capture Insights client failures and probe the legacy registration endpoint."""

import logging
import re
import shlex
import time

logger = logging.getLogger(__name__)

_LOG_PATH = '/var/log/insights-client/insights-client.log'
_CA_PATH = '/etc/rhsm/ca/katello-server-ca.pem'
_CERT_PATH = '/etc/pki/consumer/cert.pem'
_KEY_PATH = '/etc/pki/consumer/key.pem'


def _last_client_phase(client_log, arguments):
    """Return the failed command's phase only if it reached post-update."""
    marker = re.compile(
        rf'(?m)^.*\bphase=(?P<phase>[^,\s]+), arguments={re.escape(arguments)}[ \t]*$'
    )
    matches = list(marker.finditer(client_log))
    if not matches or matches[-1].group('phase') != 'post_update':
        return ''
    section = client_log[matches[-1].end() :]
    return re.split(r'(?m)^.*\bphase=[^,\n]+,\s*arguments=', section, maxsplit=1)[0]


def _legacy_registration_url(section):
    """Extract a URL only when the logged connection matches the replay settings."""
    required = (
        'Setting authmethod to CERT',
        f'Attempting to auto configure CA cert: {_CA_PATH}',
        'Attempting to auto configure proxy: None',
        f"Found subscription-manager UUID in '{_CERT_PATH}'",
    )
    if (
        not all(item in section for item in required)
        or 'Could not auto configure' in section
        or re.search(r'\b(?:ENV|CONF) Proxy:', section)
    ):
        return None
    match = re.search(r'\bGET\s+(https://\S+/v1/systems/[0-9a-fA-F-]{36})(?=\s|$)', section)
    return match.group(1) if match else None


def _redact_url_credentials(text):
    """Avoid exposing proxy credentials that may appear in the client log."""
    return re.sub(r'(?i)\b(https?://)[^\s/@]+@', r'\1<redacted>@', text)


def capture_insights_failure(host, *, arguments):
    """Log client details and compare the original legacy GET with a delayed GET.

    Call only after a failure. Never rerun insights-client: its status command
    can delete the machine ID and alter the local registration state.
    """
    try:
        client_log = host.session.sftp_read(_LOG_PATH, return_data=True)
        if isinstance(client_log, bytes):
            client_log = client_log.decode('utf-8', errors='replace')
        logger.error(
            'Insights client log for %s:\n%s', host.hostname, _redact_url_credentials(client_log)
        )

        section = _last_client_phase(client_log, arguments)
        url = _legacy_registration_url(section)
        if not url:
            logger.warning(
                'Insights registration GET not replayed: matching request or connection '
                'settings were not captured for %s',
                host.hostname,
            )
            return

        # The URL, RHSM client certificate, Satellite CA and direct connection
        # match the logged configuration. curl's User-Agent may differ.
        command = (
            "curl -q -sS -i --location --max-time 15 --noproxy '*' "
            f'--cert {_CERT_PATH} --key {_KEY_PATH} --cacert {_CA_PATH} '
            "-H 'Accept: application/json' " + shlex.quote(url)
        )
        for delay in (0, 5):
            if delay:
                time.sleep(delay)
            response = host.execute(command)
            logger.warning(
                'Insights registration GET %ss after first replay for %s (curl exit %s):\n%s\n%s',
                delay,
                host.hostname,
                response.status,
                response.stdout,
                response.stderr,
            )
    except Exception:
        # Diagnostics must never replace the original test failure.
        logger.exception('Unable to capture Insights diagnostics for %s', host.hostname)
