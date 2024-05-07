"""
Usage::

    hammer package [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    info                          Show a package
    list                          List packages
"""

from robottelo.cli.base import Base


class Package(Base):
    """
    Manipulates packages command.
    """

    command_base = 'package'
