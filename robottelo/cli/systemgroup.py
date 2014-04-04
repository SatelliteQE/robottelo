# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer system-group [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    copy
    create                        Create a system group
    info                          Show a system group
    list                          List system groups
"""

from robottelo.cli.base import Base


class SystemGroup(Base):
    """
    Manipulates Katello engine's system-group command.
    """

    command_base = "system-group"

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)

    @classmethod
    def list(cls, organization_id, options=None):
        """
        Lists available system groups
        """

        cls.command_sub = "list"

        if options is None:
            options = {}
            options['per-page'] = 10000

        # Katello subcommands require the organization-id
        options['organization-id'] = organization_id

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result
