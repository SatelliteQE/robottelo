# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer content-host [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Register a system
    delete                        Unregister a system
    info                          Show a system
    list                          List systems
    tasks                         List async tasks for the system
    update                        Update system information
"""

from robottelo.cli.base import Base


class ContentHost(Base):
    """
    Manipulates Katello engine's content-host command.
    """

    command_base = "content-host"

    @classmethod
    def tasks(cls, options=None):
        """
        Lists async tasks for a content host
        """

        cls.command_sub = "tasks"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result
