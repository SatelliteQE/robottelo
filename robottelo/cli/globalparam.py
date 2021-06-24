"""
Usage::

    hammer global-parameter [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    delete                        Delete a common_parameter
    list                          List all common parameters.
    set                           Set a global parameter.
"""
from robottelo.cli.base import Base


class GlobalParameter(Base):
    """
    Manipulates Foreman's global parameters.
    """

    command_base = 'global-parameter'

    @classmethod
    def set(cls, options=None):
        """Set global parameter"""
        cls.command_sub = 'set'
        return cls.execute(cls._construct_command(options))
