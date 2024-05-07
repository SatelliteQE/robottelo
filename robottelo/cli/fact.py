"""
Usage::

    hammer fact [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    list                          List all fact values.
"""

from robottelo.cli.base import Base


class Fact(Base):
    """
    Searches Foreman's facts.
    """

    command_base = 'fact'
