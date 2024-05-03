"""
Usage::

    hammer erratum [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

 SUBCOMMAND                    subcommand
 [ARG] ...                     subcommand arguments

Subcommands::

 info                          Show an erratum
 list                          List errata
"""

from robottelo.cli.base import Base


class Erratum(Base):
    """Manipulates Foreman's erratum."""

    command_base = 'erratum'
