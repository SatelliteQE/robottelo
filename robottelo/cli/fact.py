# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer fact [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    list                          List all fact values.
"""

from robottelo.cli.base import Base


class Fact(Base):
    """
    Searches Foreman's facts.
    """

    command_base = "fact"

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
