"""
Usage::

    hammer architecture [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add_operatingsystem           Associate a resource
    create                        Create an architecture.
    delete                        Delete an architecture.
    info                          Show an architecture.
    list                          List all architectures.
    remove_operatingsystem        Disassociate a resource
    update                        Update an architecture.
"""

from robottelo.cli.base import Base


class Architecture(Base):
    """
    Manipulates Foreman's architecture.
    """

    command_base = 'architecture'
