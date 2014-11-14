# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implementing the repository-set hammer command

Usage::

    hammer repository-set [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    available-repositories        Get list or available repositories for
                                  the repository set
    disable                       Disable a repository
    enable                        Enable a repository
    info                          Show a repository
    list                          List of repositories
"""

from robottelo.cli.base import Base


class RepositorySet(Base):
    """
    Manipulates Katello engine's repository command.
    """

    command_base = 'repository-set'

    @classmethod
    def enable(cls, options):
        """Enables a repository."""
        cls.command_sub = 'enable'
        return cls.execute(cls._construct_command(options), expect_csv=True)

    @classmethod
    def disable(cls, options):
        """Disables a repository."""
        cls.command_sub = 'disable'
        return cls.execute(cls._construct_command(options), expect_csv=True)
