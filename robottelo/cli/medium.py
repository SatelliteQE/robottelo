# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer medium [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    remove_operatingsystem        Disassociate a resource
    create                        Create a medium.
    add_operatingsystem           Associate a resource
    info                          Show a medium.
    list                          List all media.
    update                        Update a medium.
    delete                        Delete a medium.
"""

from robottelo.cli.base import Base


class Medium(Base):
    """
    Manipulates Foreman's installation media.
    """

    command_base = "medium"
