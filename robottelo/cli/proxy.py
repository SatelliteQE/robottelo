# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer proxy [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Create a smart proxy.
    info                          Show a smart proxy.
    list                          List all smart_proxies.
    update                        Update a smart proxy.
    import_classes                Import puppet classes from puppet proxy.
    delete                        Delete a smart_proxy.
"""

from robottelo.cli.base import Base


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
