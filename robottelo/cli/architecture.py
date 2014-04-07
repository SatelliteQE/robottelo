# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer architecture [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    remove_operatingsystem        Disassociate a resource
    create                        Create an architecture.
    add_operatingsystem           Associate a resource
    info                          Show an architecture.
    list                          List all architectures.
    update                        Update an architecture.
    delete                        Delete an architecture.
"""

from robottelo.cli.base import Base


class Architecture(Base):
    """
    Manipulates Foreman's architecture.
    """

    command_base = "architecture"
