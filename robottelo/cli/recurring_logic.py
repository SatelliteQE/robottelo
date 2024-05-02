"""
Usage:
    hammer recurring-logic [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    subcommand
 [ARG] ...                     subcommand arguments

Subcommands:
 cancel                        Cancel recurring logic
 info                          Show recurring logic details
 list                          List recurring logics
"""

from robottelo.cli.base import Base


class RecurringLogic(Base):
    """
    Manipulate recurring logics
    """

    command_base = 'recurring-logic'
