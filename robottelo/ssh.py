"""Utility module to handle the shared ssh connection."""
import base64
import logging
import os
import re
import time

import paramiko
import six

from fnmatch import fnmatch
from contextlib import contextmanager
from robottelo.cli import hammer
from robottelo.config import settings

logger = logging.getLogger(__name__)


class SSHCommandTimeoutError(Exception):
    """Raised when the SSH command has not finished executing after a
    predefined period of time.
    """


def decode_to_utf8(text):  # pragma: no cover
    """Paramiko returns bytes object and we need to ensure it is utf-8 before
    parsing
    """
    try:
        return text.decode('utf-8')
    except (AttributeError, UnicodeEncodeError):
        return text


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

    def __repr__(self):
        tmpl = u'SSHCommandResult(stdout={stdout!r}, stderr={stderr!r}, ' + \
               u'return_code={return_code!r}, output_format={output_format!r})'
        return tmpl.format(**self.__dict__)


class SSHClient(paramiko.SSHClient):
    """Extended SSHClient allowing custom methods"""

    def run(self, cmd, *args, **kwargs):
        """This method exists to allow the reuse of existing connections when
        running multiple ssh commands as in the following example of use:

            with robotello.ssh.get_connection() as connection:
                connection.run('ls /tmp')
                connection.run('another command')

        `self` is always passed as the connection when used in context manager
        only when using `ssh.get_connection` function.

        Note: This method is named `run` to avoid conflicts with existing
        `exec_command` and local function `execute_command`.
        """
        return execute_command(cmd, self, *args, **kwargs)


def _call_paramiko_sshclient():  # pragma: no cover
    """Call ``paramiko.SSHClient``.

    This function does not alter the behaviour of ``paramiko.SSHClient``. It
    exists solely for the sake of easing unit testing: it can be overridden for
    mocking purposes.

    """
    return SSHClient()


def get_client(hostname=None, username=None, password=None,
               key_filename=None, timeout=None):
    """Returns a SSH client connected to given hostname"""
    if hostname is None:
        hostname = settings.server.hostname
    if username is None:
        username = settings.server.ssh_username
    if key_filename is None and password is None:
        key_filename = settings.server.ssh_key
    if password is None:
        password = settings.server.ssh_password
    if timeout is None:
        timeout = settings.ssh_client.connection_timeout
    client = _call_paramiko_sshclient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=hostname,
        username=username,
        key_filename=key_filename,
        password=password,
        timeout=timeout
    )
    client._id = hex(id(client))
    return client


@contextmanager
def get_connection(hostname=None, username=None, password=None,
                   key_filename=None, timeout=None):
    """Yield an ssh connection object.

    The connection will be configured with the specified arguments or will
    fall-back to server configuration in the configuration file.

    Yield this SSH connection. The connection is automatically closed when the
    caller is done using it using ``contextlib``, so clients should use the
    ``with`` statement to handle the object::

        with get_connection() as connection:
            ...

    :param str hostname: The hostname of the server to establish connection.If
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
    :rtype: ``paramiko.SSHClient``

    """
    if timeout is None:
        timeout = settings.ssh_client.connection_timeout
    client = get_client(
        hostname, username, password, key_filename, timeout
    )
    try:
        logger.debug('Instantiated Paramiko client {0}'.format(client._id))
        logger.info('Connected to [%s]', hostname)
        yield client
    finally:
        client.close()
        logger.debug('Destroyed Paramiko client {0}'.format(client._id))


@contextmanager
def get_sftp_session(hostname=None, username=None,
                     password=None, key_filename=None, timeout=None):
    """Yield a SFTP session object.

    The session will be configured with the host whose hostname is
    passed as
    argument.

    Yield this SFTP Session. The session is automatically closed when
    the caller is done using it using ``contextlib``, so clients should use
    the``with`` statement to handle the object::

      with get_sftp_session() as session:
      ...
    :param str hostname: The hostname of the server to establish connection.If
        it is ``None`` ``hostname`` from configuration's ``server`` section
        will be used.
    :param str username: The username to use when connecting.If it is ``None``
    `   `ssh_username`` from configuration's ``server`` section will be used.
    :param str password: The password to use when connecting. If it is
        ``None``  ``ssh_password`` from configuration's ``server`` section
        will be used. Should be applied only in case ``key_filename`` is not
        set
    :param str key_filename: The path of the ssh private key to use when
        connecting to the server. If it is ``None`` ``key_filename`` from
        configuration's ``server`` section will be used.
    :param int timeout: Time to wait for establish the connection.
       """
    with get_connection(hostname=hostname, username=username,
                        password=password, key_filename=key_filename,
                        timeout=timeout) as connection:
        try:
            sftp = connection.open_sftp()
            yield sftp
        finally:
            sftp.close()


def add_authorized_key(key, hostname=None, username=None, password=None,
                       key_filename=None, timeout=None):
    """Appends a local public ssh key to remote authorized keys

    refer to: remote_execution_ssh_keys provisioning template

    :param key: either a file path, key string or a file-like obj to append.
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
    """

    if getattr(key, 'read', None):  # key is a file-like object
        key_content = key.read()  # pragma: no cover
    elif is_ssh_pub_key(key):  # key is a valid key-string
        key_content = key
    elif os.path.exists(key):  # key is a path to a pub key-file
        with open(key, 'r') as key_file:  # pragma: no cover
            key_content = key_file.read()
    else:
        raise AttributeError('Invalid key')

    if timeout is None:
        timeout = settings.ssh_client.connection_timeout

    key_content = key_content.strip()
    ssh_path = '~/.ssh'
    auth_file = os.path.join(ssh_path, 'authorized_keys')

    with get_connection(hostname=hostname, username=username,
                        password=password, key_filename=key_filename,
                        timeout=timeout) as con:

        # ensure ssh directory exists
        execute_command('mkdir -p %s' % ssh_path, con)

        # append the key if doesn't exists
        add_key = "grep -q '{key}' {dest} || echo '{key}' >> {dest}".format(
            key=key_content, dest=auth_file)
        execute_command(add_key, con)

        # set proper permissions
        execute_command('chmod 700 %s' % ssh_path, con)
        execute_command('chmod 600 %s' % auth_file, con)
        ssh_user = username or settings.server.ssh_username
        execute_command('chown -R %s %s' % (ssh_user, ssh_path), con)

        # Restore SELinux context with restorecon, if it's available:
        cmd = 'command -v restorecon && restorecon -RvF %s || true' % ssh_path
        execute_command(cmd, con)


def upload_file(local_file, remote_file, key_filename=None, hostname=None):
    """Upload a local file to a remote machine

    :param local_file: either a file path or a file-like object to be uploaded.
    :param remote_file: a remote file path where the uploaded file will be
        placed.
    :param hostname: target machine hostname. If not provided will be used the
        ``server.hostname`` from the configuration.
    :param str key_filename: The path of the ssh private key to use when
        connecting to the server. If it is ``None`` ``key_filename`` from
        configuration's ``server`` section will be used.
    """

    with get_sftp_session(hostname=hostname,
                          key_filename=key_filename) as sftp:
        _upload_file(sftp, local_file, remote_file)


def upload_files(local_dir, remote_dir, file_search="*.txt",
                 hostname=None, key_filename=None):
    """ Upload all files from directory to a remote directory
    :param local_dir: all files from local path to be uploaded.
    :param remote_dir: a remote path where the uploaded files will be
           placed.
    :param file_search: filter only files contains the type extension
    :param hostname: target machine hostname. If not provided will be used the
        ``server.hostname`` from the configuration.
    :param str key_filename: The path of the ssh private key to use when
        connecting to the server. If it is ``None`` ``key_filename`` from
        configuration's ``server`` section will be used.
    """
    command("mkdir -p {}".format(remote_dir))
    # making only one SFTP Session to transfer all files
    with get_sftp_session(hostname=hostname,
                          key_filename=key_filename) as sftp:
        for root, dirs, files in os.walk(local_dir):
            for local_filename in files:
                if fnmatch(local_filename, file_search):
                    remote_file = "{0}/{1}".format(remote_dir, local_filename)
                    local_file = os.path.join(local_dir, local_filename)
                    _upload_file(sftp, local_file, remote_file)


def _upload_file(sftp, local_file, remote_file):
    """ Upload a file using existent sftp session
    :param sftp: sftp session object
    :param local_file: either a file path or a file-like object to be uploaded.
    :param remote_file: a remote file path where the uploaded file will be
        placed.

    """
    # Check if local_file is a file-like object and use the proper
    # paramiko function to upload it to the remote machine.
    if hasattr(local_file, 'read'):
        sftp.putfo(local_file, remote_file)
    else:
        sftp.put(local_file, remote_file)


def download_file(remote_file, local_file=None, hostname=None):
    """Download a remote file to the local machine. If ``hostname`` is not
    provided will be used the server.

    """
    if local_file is None:  # pragma: no cover
        local_file = remote_file
    with get_connection(
        hostname=hostname,
    ) as connection:  # pragma: no cover
        try:
            sftp = connection.open_sftp()
            sftp.get(remote_file, local_file)
        finally:
            sftp.close()


def command(cmd, hostname=None, output_format=None, username=None,
            password=None, key_filename=None, timeout=None,
            connection_timeout=None):
    """Executes SSH command(s) on remote hostname.

    :param str cmd: The command to run
    :param str output_format: json, csv or None
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
    :param int timeout: Time to wait for the ssh command to finish.
    :param connection_timeout: Time to wait for establishing the connection.
    """
    hostname = hostname or settings.server.hostname
    if timeout is None:
        timeout = settings.ssh_client.command_timeout
    if connection_timeout is None:
        connection_timeout = settings.ssh_client.connection_timeout
    with get_connection(hostname=hostname, username=username,
                        password=password, key_filename=key_filename,
                        timeout=connection_timeout) as connection:
        return execute_command(
            cmd, connection, output_format, timeout, connection_timeout)


def execute_command(cmd, connection, output_format=None, timeout=None,
                    connection_timeout=None):
    """Execute a command via ssh in the given connection

    :param cmd: a command to be executed via ssh
    :param connection: SSH Paramiko client connection
    :param output_format: plain|json|csv|list valid only for hammer commands
    :param timeout: Time to wait for the ssh command to finish.
    :param connection_timeout: Time to wait for establishing the connection.
    :return: SSHCommandResult
    """
    if timeout is None:
        timeout = settings.ssh_client.command_timeout
    if connection_timeout is None:
        connection_timeout = settings.ssh_client.connection_timeout
    logger.info('>>> %s', cmd)
    _, stdout, stderr = connection.exec_command(
        cmd, timeout=connection_timeout)
    if timeout:
        # wait for the exit status ready
        end_time = time.time() + timeout
        while time.time() < end_time:
            if stdout.channel.exit_status_ready():
                break
            time.sleep(1)
        else:
            logger.error('ssh command did not respond in the predefined time'
                         ' (timeout=%s) and will be interrupted', timeout)
            stdout.channel.close()
            stderr.channel.close()
            logger.error(
                    '[Captured stdout]\n{0}\n-----\n'.format(stdout.read())
            )
            logger.error(
                    '[Captured stderr]\n{0}\n-----\n'.format(stderr.read())
            )
            raise SSHCommandTimeoutError(
                'ssh command: {0} \n did not respond in the predefined time '
                '(timeout={1})'.format(cmd, timeout)
            )

    errorcode = stdout.channel.recv_exit_status()

    stdout = stdout.read()
    stderr = stderr.read()
    # Remove escape code for colors displayed in the output
    regex = re.compile(r'\x1b\[\d\d?m')
    if stdout:
        # Convert to unicode string
        stdout = decode_to_utf8(stdout)
        logger.info('<<< stdout\n%s', stdout)
    if stderr:
        # Convert to unicode string and remove all color codes characters
        stderr = regex.sub('', decode_to_utf8(stderr))
        logger.info('<<< stderr\n%s', stderr)
    # we don't want a list as output of 'plain' just pure text
    if stdout and output_format not in ('json', 'plain'):
        # Mostly only for hammer commands
        # for output we don't really want to see all of Rails traffic
        # information, so strip it out.
        # Empty fields are returned as "" which gives us u'""'
        stdout = stdout.replace('""', '')
        stdout = u''.join(stdout).split('\n')
        stdout = [
            regex.sub('', line)
            for line in stdout
            if not line.startswith('[')
        ]
    return SSHCommandResult(
        stdout, stderr, errorcode, output_format)


def is_ssh_pub_key(key):
    """Validates if a string is in valid ssh pub key format

    :param key: A string containing a ssh public key encoded in base64
    :return: Boolean
    """

    if not isinstance(key, six.string_types):
        raise ValueError(
            "Key should be a string type, received: %s" % type(key))

    # 1) a valid pub key has 3 parts separated by space
    try:
        key_type, key_string, comment = key.split()
    except ValueError:  # need more than one value to unpack
        return False

    # 2) The second part (key string) should be a valid base64
    try:
        base64.decodebytes(key_string.encode('ascii'))
    except base64.binascii.Error:
        return False

    # 3) The first part, the type, should be one of below
    return key_type in (
        'ecdsa-sha2-nistp256', 'ssh-dss', 'ssh-rsa', 'ssh-ed25519'
    )
