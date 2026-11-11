"""Capture host-side diagnostics when an Insights registration check fails."""

from io import BytesIO
from pathlib import Path
import re
import tarfile
from tempfile import NamedTemporaryFile, TemporaryDirectory

from robottelo.logging import logger, robottelo_log_dir

CLIENT_LOG = '/var/log/insights-client/insights-client.log'
SENSITIVE_LINE = re.compile(
    r'password|passwd|token|secret|authorization|credential|private[ _-]?key|'
    r'api[ _-]?key|x-rh-identity|x-forwarded-identity|cookie|proxy',
    re.IGNORECASE,
)
CREDENTIAL_URL = re.compile(r'\b[a-z][a-z0-9+.-]*://[^\s/]+@', re.IGNORECASE)


def _redact_client_log(data):
    """Remove common credential-bearing lines and private-key blocks."""
    if isinstance(data, bytes):
        data = data.decode('utf-8', errors='replace')
    result = []
    in_private_key = False
    for line in data.splitlines():
        if re.search(r'-----BEGIN [A-Z ]*PRIVATE KEY-----', line):
            in_private_key = True
        if in_private_key or SENSITIVE_LINE.search(line) or CREDENTIAL_URL.search(line):
            result.append('[redacted sensitive line]')
        else:
            result.append(line)
        if re.search(r'-----END [A-Z ]*PRIVATE KEY-----', line):
            in_private_key = False
    return '\n'.join(result)


def capture_insights_diagnostics(host, failure_details):
    """Save a sanitized client log and package version before host teardown.

    PRT archives ``logs/*.log``, so diagnostics must be files directly in that
    directory. Capture failures are recorded without masking the readiness error.
    """
    try:
        timeout = 15 if host._settings.SSH.BACKEND == 'paramiko' else '15s'
        result = host.execute('rpm -q insights-client', timeout=timeout)
        version = result.stdout.strip() if result.status == 0 else f'rpm exited {result.status}'
    except Exception as exc:
        version = f'Could not read package version ({type(exc).__name__})'

    try:
        is_container_session = False
        if getattr(host, 'is_container', False) or getattr(host, '_cont_inst', None):
            from broker.session import ContainerSession

            is_container_session = isinstance(host.session, ContainerSession)

        if is_container_session:
            # Avoid the container backend's unredacted temporary tar in the working directory.
            data = host.session.sftp_read(CLIENT_LOG, destination='_raw', return_data=True)
            with tarfile.open(fileobj=BytesIO(data), mode='r:*') as archive:
                client_log = archive.extractfile(Path(CLIENT_LOG).name).read()
        elif host._settings.SSH.BACKEND == 'pylibssh':
            # This backend downloads to a local file even when returning data.
            with TemporaryDirectory(prefix='insights-client-') as tmp:
                client_log = host.session.sftp_read(
                    CLIENT_LOG, destination=str(Path(tmp) / 'client.log'), return_data=True
                )
        else:
            client_log = host.session.sftp_read(CLIENT_LOG, return_data=True)
        client_log = _redact_client_log(client_log)
    except Exception as exc:
        client_log = f'Could not read client log ({type(exc).__name__})'
        logger.warning('Could not read Insights client log (%s)', type(exc).__name__)

    try:
        robottelo_log_dir.mkdir(parents=True, exist_ok=True)
        hostname = re.sub(r'[^A-Za-z0-9_.-]', '_', host.hostname)[:80]
        with NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=robottelo_log_dir,
            prefix=f'insights-readiness-{hostname}-',
            suffix='.log',
            delete=False,
        ) as output:
            output.write(f'Host: {hostname}\nPackage: {version}\n\n')
            output.write(f'Failure details:\n{_redact_client_log(failure_details or "")}\n\n')
            output.write('Client log (credential-bearing lines redacted):\n')
            output.write(client_log + '\n')
            path = Path(output.name)
        logger.info('Saved Insights readiness diagnostics to %s', path)
        return path
    except Exception as exc:
        logger.warning('Could not save Insights readiness diagnostics (%s)', type(exc).__name__)
        return None
