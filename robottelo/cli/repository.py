# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer repository [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Create a repository
    delete                        Destroy a repository
    info                          Show a repository
    list                          List of repositories
    synchronize                   Sync a repository
    update                        Update a repository
"""

from robottelo.cli.base import Base


class Repository(Base):
    """
    Manipulates Katello engine's repository command.
    """

    command_base = "repository"

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)

    @classmethod
    def list(cls, organization_id, options=None):
        """
        Lists available repositories.
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
    def synchronize(cls, options):
        """
        Synchronizes a repository.
        """

        cls.command_sub = "synchronize"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result
