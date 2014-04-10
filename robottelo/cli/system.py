# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer system [OPTIONS] SUBCOMMAND [ARG] ...

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


class System(Base):
    """
    Manipulates Katello engine's system command.
    """

    command_base = "system"
    command_requires_org = True

    @classmethod
    def tasks(cls, options=None):
        """
        Lists async tasks for a system
        """

        cls.command_sub = "list"

        if options is None:
            options = {}

        if 'per-page' not in options:
            options['per-page'] = 10000

        if cls.command_requires_org and 'organization-id' not in options:
            raise Exception(
                'organization-id option is required for %s.tasks' %
                cls.__name__)

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def update(cls, options=None):
        """
        Update system information
        """

        cls.command_sub = "list"

        if options is None:
            options = {}

        if 'per-page' not in options:
            options['per-page'] = 10000

        if cls.command_requires_org and 'organization-id' not in options:
            raise Exception(
                'organization-id option is required for %s.update' %
                cls.__name__)

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result
