"""
Usage::

    hammer partition-table [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add_operatingsystem           Associate a resource
    create                        Create a ptable.
    delete                        Delete a ptable.
    dump                          View partition table content.
    info                          Show a ptable.
    list                          List all ptables.
    remove_operatingsystem        Disassociate a resource
    update                        Update a ptable.
"""

from robottelo.cli.base import Base


class PartitionTable(Base):
    """
    Manipulates Foreman's partition tables.
    """

    command_base = 'partition-table'
