"""Utility module to handle the shared ssh connection."""
import logging
from contextlib import contextmanager

import paramiko
import re

from robottelo.cli import hammer
from robottelo.config import settings

logger = logging.getLogger(__name__)


class SSHCommandResult(object):
    """Structure that returns in all ssh commands results."""

    def __init__(
            self, stdout=None, stderr=None, return_code=0, output_format=None):
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.output_format = output_format
        #  Does not make sense to return suspicious output if ($? <> 0)
        if output_format and self.return_code == 0:
            if output_format == 'csv':
                self.stdout = hammer.parse_csv(stdout) if stdout else {}
            if output_format == 'json':
                self.stdout = hammer.parse_json(stdout) if stdout else None


def _call_paramiko_sshclient():
    """Call ``paramiko.SSHClient``.

    This function does not alter the behaviour of ``paramiko.SSHClient``. It
    exists soley for the sake of easing unit testing: it can be overridden for
    mocking purposes.

    """
    return paramiko.SSHClient()


@contextmanager
def _get_connection(hostname=None, username=None, password=None,
                    key_filename=None, timeout=10):
    """Yield an ssh connection object.

    The connection will be configured with the specified arguments or will
    fall-back to server configuration in the configuration file.

    Yield this SSH connection. The connection is automatically closed when the
    caller is done using it using ``contextlib``, so clients should use the
    ``with`` statement to handle the object::

        with _get_connection() as connection:
            ...

    :param str hostname: The hostname of the server to establish connection. If
        it is ``None`` ``hostname`` from configuration's ``server`` section
        will be used.
    :param str username: The username to use when connecting. If it is ``None``
        ``ssh_username`` from configuration's ``server`` section will be used.
    :param str password: The password to use when connecting. If it is ``None``
        ``ssh_password`` from configuration's ``server`` section will be used.
        Should be applied only in case ``key_filename`` is not set
    :param str key_filename: The path of the ssh private key to use when
        connecting to the server. If it is ``None`` ``key_filename`` from
        configuration's ``server`` section will be used.
    :param int timeout: Time to wait for establish the connection.

    :return: An SSH connection.
    :rtype: paramiko.SSHClient

    """
    if hostname is None:
        hostname = settings.server.hostname
    if username is None:
        username = settings.server.ssh_username
    if key_filename is None:
        key_filename = settings.server.ssh_key
    if password is None:
        password = settings.server.ssh_password

    client = _call_paramiko_sshclient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=hostname,
        username=username,
        key_filename=key_filename,
        password=password,
        timeout=timeout
    )
    client_id = hex(id(client))
    try:
        logger.info('Instantiated Paramiko client {0}'.format(client_id))
        yield client
    finally:
        logger.info('Destroying Paramiko client {0}'.format(client_id))
        client.close()
        logger.info('Destroyed Paramiko client {0}'.format(client_id))


def upload_file(local_file, remote_file, hostname=None):
    """Upload a local file to a remote machine

    :param local_file: either a file path or a file-like object to be uploaded.
    :param remote_file: a remote file path where the uploaded file will be
        placed.
    :param hostname: target machine hostname. If not provided will be used the
        ``server.hostname`` from the configuration.
    """
    with _get_connection(hostname=hostname) as connection:
        try:
            sftp = connection.open_sftp()
            # Check if local_file is a file-like object and use the proper
            # paramiko function to upload it to the remote machine.
            if hasattr(local_file, 'read'):
                sftp.putfo(local_file, remote_file)
            else:
                sftp.put(local_file, remote_file)
        finally:
            sftp.close()


def download_file(remote_file, local_file=None, hostname=None):
    """Download a remote file to the local machine. If ``hostname`` is not
    provided will be used the server.

    """
    if local_file is None:
        local_file = remote_file
    with _get_connection(hostname=hostname) as connection:
        try:
            sftp = connection.open_sftp()
            sftp.get(remote_file, local_file)
        finally:
            sftp.close()


def command(cmd, hostname=None, output_format=None, timeout=None):
    """
    Executes SSH command(s) on remote hostname.
    Defaults to main.server.hostname.
    """

    # Set a default timeout of 120 seconds
    if timeout is None:
        timeout = 120

    # Variable to hold results returned from the command
    stdout = stderr = errorcode = None

    # Remove escape code for colors displayed in the output
    regex = re.compile(r'\x1b\[\d\d?m')

    hostname = hostname or settings.server.hostname

    logger.debug('>>> [%s] %s', hostname, cmd)

    with _get_connection(hostname=hostname) as connection:
        _, stdout, stderr = connection.exec_command(cmd, timeout)
        errorcode = stdout.channel.recv_exit_status()
        stdout = stdout.read()
        stderr = stderr.read()

    if stdout:
        # Convert to unicode string
        stdout = stdout.decode('utf-8')
        logger.debug('<<< stdout\n%s', stdout)
    if stderr:
        # Convert to unicode string and remove all color codes characters
        stderr = regex.sub('', stderr.decode('utf-8'))
        logger.debug('<<< stderr\n%s', stderr)

    if stdout and output_format != 'json':
        # For output we don't really want to see all of Rails traffic
        # information, so strip it out.
        # Empty fields are returned as "" which gives us u'""'
        stdout = stdout.replace('""', '')
        stdout = u''.join(stdout).split('\n')
        stdout = [
            regex.sub('', line) for line in stdout if not line.startswith('[')
        ]

    return SSHCommandResult(
        stdout, stderr, errorcode, output_format)
