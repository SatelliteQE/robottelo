# -*- encoding: utf-8 -*-
"""
Usage::

    hammer proxy [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a smart proxy.
    delete                        Delete a smart_proxy.
    import_classes                Import puppet classes from puppet proxy.
    info                          Show a smart proxy.
    list                          List all smart_proxies.
    refresh-features              Refresh smart proxy features
    update                        Update a smart proxy.
"""
import contextlib
import logging

from robottelo import ssh
from robottelo.cli.base import Base
from robottelo.config import settings
from time import sleep


class SSHTunnelError(Exception):
    """Raised when ssh tunnel creation fails."""


@contextlib.contextmanager
def default_url_on_new_port(oldport, newport):
    """Creates context where the default smart-proxy is forwarded on a new port
    REQUIRES GatewayPorts yes in sshd_config

    :param int oldport: Port to be forwarded.
    :param int newport: New port to be used to forward `oldport`.

    :return: A string containing the new capsule URL with port.
    :rtype: str

    """
    logger = logging.getLogger('robottelo')
    command_timeout = 2
    domain = settings.server.hostname
    user = settings.server.ssh_username
    key = settings.server.ssh_key
    ssh.upload_file(key, '/tmp/dsa_{0}'.format(newport))
    ssh.command('chmod 700 /tmp/dsa_{0}'.format(newport))

    with ssh._get_connection() as connection:
        command = (
            u'ssh -i {0} -o StrictHostKeyChecking=no -R {1}:{2}:{3} {4}@{5}'
        ).format(
            '/tmp/dsa_{0}'.format(newport),
            newport, domain, oldport, user, domain)
        logger.debug('Creating tunnel {0}'.format(command))
        transport = connection.get_transport()
        channel = transport.open_session()
        channel.exec_command(command)
        # if exit_status appears until command_timeout, throw error
        for _ in range(command_timeout):
            if channel.exit_status_ready():
                if channel.recv_exit_status() != 0:
                    stderr = u''
                    while channel.recv_stderr_ready():
                        stderr += channel.recv_stderr(1)
                    logger.debug('Tunnel failed: {0}'.format(stderr))
                    # Something failed, so raise an exception.
                    raise SSHTunnelError(stderr)
            sleep(1)
        yield 'https://{0}:{1}'.format(domain, newport)
        ssh.command('rm -f /tmp/dsa_{0}'.format(newport))


class Proxy(Base):
    """Manipulates Foreman's smart proxies. """

    command_base = 'proxy'

    @classmethod
    def importclasses(cls, options=None):
        """Import puppet classes from puppet proxy."""
        cls.command_sub = 'import-classes'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def refresh_features(cls, options=None):
        """Refreshes smart proxy features"""
        cls.command_sub = 'refresh-features'
        return cls.execute(cls._construct_command(options))
