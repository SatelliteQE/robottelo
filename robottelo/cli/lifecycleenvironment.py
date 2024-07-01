"""
Usage::

    hammer lifecycle-environment [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    list                          List environments in an organization
    update                        Update an environment
    create                        Create an environment
    delete                        Destroy an environment
    info                          Show an environment
"""

from robottelo.cli.base import Base


class LifecycleEnvironment(Base):
    """
    Manipulates Katello engine's lifecycle-environment command.
    """

    command_base = 'lifecycle-environment'
    command_requires_org = True

    @classmethod
    def list(cls, options=None, per_page=False):
        return super().list(options, per_page=per_page)

    @classmethod
    def paths(cls, options=None):
        cls.command_sub = 'paths'
        return cls.execute(cls._construct_command(options))
