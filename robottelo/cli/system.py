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

    @classmethod
    def list(cls, organization_id, options=None):
        """
        Lists available systems
        """

        cls.command_sub = "list"

        if options is None:
            options = {}
            options['per-page'] = 10000

        # Katello subcommands require the organization-id
        options['organization-id'] = organization_id

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def tasks(cls, organization_id, options=None):
        """
        Lists async tasks for a system
        """

        cls.command_sub = "list"

        if options is None:
            options = {}
            options['per-page'] = 10000

        # Katello subcommands require the organization-id
        options['organization-id'] = organization_id

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def update(cls, organization_id, options=None):
        """
        Update system information
        """

        cls.command_sub = "list"

        if options is None:
            options = {}
            options['per-page'] = 10000

        # Katello subcommands require the organization-id
        options['organization-id'] = organization_id

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result
