"""
Utility module to handle the shared ssh connection
"""

import logging
import re
import socket
import sys
import time

from robottelo.common import conf
from robottelo.common.helpers import csv_to_dictionary
from select import select

try:
    import paramiko
except ImportError:
    print "Please install paramiko."
    sys.exit(-1)


class CommandTimeOut(Exception):
    """
    Exception for Paramiko timeouts
    """
    pass


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


def _get_connection(timeout=10):
    """
    Constructs a ssh connection to the host provided in config.
    """
    # Hide base logger from paramiko
    logging.getLogger("paramiko").setLevel(logging.ERROR)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host = conf.properties['main.server.hostname']
    root = conf.properties['main.server.ssh.username']
    key_filename = conf.properties['main.server.ssh.key_private']
    client.connect(
        host, username=root, key_filename=key_filename, timeout=timeout)
    logging.getLogger('robottelo').info(
        "Paramiko instance prepared (and would be reused): %s"
        % hex(id(client))
    )
    return client


# Define the shared ssh connection
connection = _get_connection()


def upload_file(local_file, remote_file=None):
    """
    Uploads a remote file to a server.
    """

    if not remote_file:
        remote_file = local_file

    sftp = connection.open_sftp()
    sftp.put(local_file, remote_file)
    sftp.close()


def command(cmd, hostname=None, expect_csv=False, timeout=50):
    """
    Executes SSH command(s) on remote hostname.
    Defaults to main.server.hostname.
    """

    # Start the timer
    start = time.time()
    # Variable to hold results returned from the command
    stdout = stderr = errorcode = None

    # Remove escape code for colors displayed in the output
    regex = re.compile(r'\x1b\[\d\d?m')

    logger = logging.getLogger('robottelo')
    logger.debug(cmd)

    hostname = hostname or conf.properties['main.server.hostname']

    channel = connection.get_transport().open_session()
    channel.settimeout(timeout)
    channel.exec_command(cmd)

    while True:
        try:
            rlist, wlist, elist = select([channel], [], [], float(timeout))

            if rlist is not None and len(rlist) > 0:
                if channel.exit_status_ready():
                    if channel.recv_ready():
                        stdout = channel.recv(1048576)
                    if channel.recv_stderr_ready():
                        stderr = channel.recv_stderr(1048576)
                    errorcode = channel.recv_exit_status()
                    break
            elif elist is not None and len(elist) > 0:
                if channel.recv_stderr_ready():
                    stderr = channel.recv_stderr(1048576)
                    break

            if time.time() - start > timeout:
                logger.debug("Command timeout exceeded.")
                raise CommandTimeOut('Command timeout exceeded')
        except socket.timeout:
            logger.debug("SSH channel timeout exceeded.")
            raise CommandTimeOut('SSH channel timeout exceeded.')

    # For output we don't really want to see all of Rails traffic
    # information, so strip it out.

    if stdout:
        stdout = "".join(stdout).split("\n")
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
        logger.debug(output)
    if errors:
        errors = regex.sub('', "".join(errors))
        logger.debug(errors)

    return SSHCommandResult(
        output, errors, errorcode, expect_csv)
