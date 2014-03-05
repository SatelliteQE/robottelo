# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer global_parameter [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    set                           Set a global parameter.
    list                          List all common parameters.
    delete                        Delete a common_parameter
"""

from robottelo.cli.base import Base


class GlobalParameter(Base):
    """
    Manipulates Foreman's global parameters.
    """

    command_base = "global_parameter"

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)

    @classmethod
    def set(cls, options=None):
        """ Set global parameter """
        cls.command_sub = "set"
        return cls.execute(cls._construct_command(options))
