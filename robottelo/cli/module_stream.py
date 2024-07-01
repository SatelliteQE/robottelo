"""
Usage::

    hammer module-stream [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    info                          Show a module-stream
    list                          List module-streams
"""

from robottelo.cli.base import Base


class ModuleStream(Base):
    """
    Manipulates module-stream command.
    """

    command_base = 'module-stream'
