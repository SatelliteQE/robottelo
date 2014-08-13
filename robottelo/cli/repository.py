# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage::

    hammer repository [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

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
    command_requires_org = True

    @classmethod
    def create(cls, options=None):
        cls.command_requires_org = False

        try:
            result = super(Repository, cls).create(options)
        finally:
            cls.command_requires_org = True

        return result

    @classmethod
    def info(cls, options=None):
        cls.command_requires_org = False

        try:
            result = super(Repository, cls).info(options)
        finally:
            cls.command_requires_org = True

        return result

    @classmethod
    def synchronize(cls, options):
        """
        Synchronizes a repository.
        """

        cls.command_sub = "synchronize"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result
