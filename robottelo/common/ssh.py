"""
Utility module to handle the shared ssh connection
"""

import logging
import re
import sys

from contextlib import contextmanager
from robottelo.common import conf
from robottelo.common.helpers import csv_to_dictionary

try:
    import paramiko
except ImportError:
    print "Please install paramiko."
    sys.exit(-1)


class SSHCommandResult(object):
    """
    Structure that returns in all ssh commands results.
    """

    def __init__(self, stdout=None, stderr=None,
                 return_code=0, transform_csv=False):
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.transform_csv = transform_csv
        #  Does not make sense to return suspicious CSV if ($? <> 0)
        if transform_csv and self.return_code == 0:
            self.stdout = csv_to_dictionary(stdout) if stdout else {}


@contextmanager
def _get_connection(timeout=10):
    """Yield an ssh connection object.

    Create an SSH connection using the following parameters from the ``main``
    section of the configuration file:

    * ``server.hostname``
    * ``server.ssh.username``
    * ``server.ssh.key_private``

    Yield this SSH connection. The connection is automatically closed when the
    caller is done using it using ``contextlib``, so clients should use the
    ``with`` statement to handle the object::

        with _get_connection() as connection:
            ...

    :return: An SSH connection.
    :rtype: paramiko.SSHClient

    """
    # Hide base logger from paramiko
    logging.getLogger('paramiko').setLevel(logging.ERROR)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=conf.properties['main.server.hostname'],
        username=conf.properties['main.server.ssh.username'],
        key_filename=conf.properties['main.server.ssh.key_private'],
        timeout=timeout
    )

    robo_logger = logging.getLogger('robottelo')
    client_id = hex(id(client))
    try:
        robo_logger.info('Instantiated Paramiko client {0}'.format(client_id))
        yield client
    finally:
        robo_logger.info('Destroying Paramiko client {0}'.format(client_id))
        client.close()
        robo_logger.info('Destroyed Paramiko client {0}'.format(client_id))


def upload_file(local_file, remote_file=None):
    """
    Uploads a remote file to a normal server or
    uploads a file to sauce labs via VPN tunnel.
    """

    remote = int(conf.properties['main.remote'])

    if not remote_file:
        remote_file = local_file

    if not remote:
        with _get_connection() as connection:
            sftp = connection.open_sftp()
            sftp.put(local_file, remote_file)
            sftp.close()
    # TODO: Upload file to sauce labs via VPN tunnel in the else part.


def download_file(remote_file, local_file=None):
    """Download a remote file using sftp"""

    if local_file is None:
        local_file = remote_file

    with _get_connection() as connection:
        sftp = connection.open_sftp()
        sftp.get(remote_file, local_file)
        sftp.close()


def command(cmd, hostname=None, expect_csv=False, timeout=None):
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

    logger = logging.getLogger('robottelo')
    logger.debug(">>> %s" % cmd)

    hostname = hostname or conf.properties['main.server.hostname']

    with _get_connection() as connection:
        _, stdout, stderr = connection.exec_command(cmd, timeout)
        errorcode = stdout.channel.recv_exit_status()
        stdout = stdout.read()
        stderr = stderr.read()

    # For output we don't really want to see all of Rails traffic
    # information, so strip it out.

    if stdout:
        # Empty fields are returned as "" which gives us u'""'
        stdout = stdout.replace('""', '')
        stdout = stdout.decode('utf-8')
        stdout = u"".join(stdout).split("\n")
        output = [
            regex.sub('', line) for line in stdout if not line.startswith("[")
            ]
    else:
        output = []

    # Ignore stderr if errorcode == 0. This is necessary since
    # we're running Foreman in verbose mode which generates a lot
    # of output return as stderr.
    errors = [] if errorcode == 0 else stderr

    if output:
        logger.debug("<<<\n%s" % '\n'.join(output[:-1]))
    if errors:
        errors = regex.sub('', "".join(errors))
        logger.debug("<<< %s" % errors)

    return SSHCommandResult(
        output, errors, errorcode, expect_csv)
