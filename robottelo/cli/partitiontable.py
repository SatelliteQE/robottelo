# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer partition_table [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    remove_operatingsystem        Disassociate a resource
    dump                          View partition table content.
    create                        Create a ptable.
    add_operatingsystem           Associate a resource
    info                          Show a ptable.
    list                          List all ptables.
    update                        Update a ptable.
    delete                        Delete a ptable.
"""

from robottelo.cli.base import Base


class PartitionTable(Base):
    """
    Manipulates Foreman's partition tables.
    """

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
        self.command_base = "partition_table"
