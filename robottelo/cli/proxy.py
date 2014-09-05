# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage::

    hammer proxy [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a smart proxy.
    info                          Show a smart proxy.
    list                          List all smart_proxies.
    update                        Update a smart proxy.
    import_classes                Import puppet classes from puppet proxy.
    delete                        Delete a smart_proxy.
"""

from robottelo.cli.base import Base
from robottelo.common import conf, ssh
import contextlib
import logging


def SSHTunnelError(Exception):
    """Raised when ssh tunnel creation fails."""


@contextlib.contextmanager
def default_url_on_new_port(oldport, newport):
    """Creates context where the default smart-proxy is forwarded on a new port.

    :param int oldport: Port to be forwarded.
    :param int newport: New port to be used to forward `oldport`.

    :return: A string containing the new capsule URL with port.
    :rtype: str

    """
    logger = logging.getLogger("robottelo")
    domain = conf.properties['main.server.hostname']
    user = conf.properties['main.server.ssh.username']
    key = conf.properties['main.server.ssh.key_private']
    ssh.upload_file(key, "/tmp/dsa_%s" % newport)
    ssh.command("chmod 700 /tmp/dsa_%s" % newport)

    with ssh._get_connection() as connection:
        command = u"ssh -i {0} -L {1}:{2}:{3} {4}@{5}".format(
            "/tmp/dsa_{0}".format(newport),
            newport, domain, oldport, user, domain)
        logger.debug("Creating tunell %s", command)
        # Run command and timeout in 30 seconds.
        _, _, stderr = connection.exec_command(command, 30)

        stderr = stderr.read()
        if len(stderr) > 0:
            logger.debug("Tunell failed: %s", stderr)
            # Something failed, so raise an exception.
            raise SSHTunnelError(stderr)
        yield "https://{0}:{1}".format(domain, newport)


class Proxy(Base):
    """
    Manipulates Foreman's smart proxies.
    """

    command_base = "proxy"

    @classmethod
    def importclasses(cls, options=None):
        """
        Import puppet classes from puppet proxy.
        """

        cls.command_sub = "import-classes"

        result = cls.execute(cls._construct_command(options))

        return result
