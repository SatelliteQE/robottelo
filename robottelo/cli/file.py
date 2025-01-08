"""
Usage::

    hammer file [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    info                          Show a file
    list                          List files
"""

from robottelo.cli.base import Base


class File(Base):
    """
    Manipulates files command.
    """

    command_base = 'file'
