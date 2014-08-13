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


@contextlib.contextmanager
def default_url_on_new_port(oldport, newport):
    """
    Creates context where the default smart-proxy is forwarded on a new port
    """
    logger = logging.getLogger("robottelo")
    domain = conf.properties['main.server.hostname']
    user = conf.properties['main.server.ssh.username']
    key = conf.properties['main.server.ssh.key_private']
    ssh.upload_file(key, "/tmp/dsa_%s" % newport)
    ssh.command("chmod 700 /tmp/dsa_%s" % newport)
    with ssh._get_connection() as connection:
        command = "ssh -i %s -L %s:%s:%s %s@%s" % (
            "/tmp/dsa_%s" % newport, newport, domain, oldport, user, domain
        )
        logger.debug("Creating tunell %s", command)
        _, _, stderr = connection.exec_command(command, 1000)
        if len(stderr) > 0:
            logger.debug("Tunell failed %s", stderr)
        yield "https://%s:%s" % (domain, newport)


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
