# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer host-collection [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    copy
    create                        Create a host collection
    delete                        Destroy a host collection
    info                          Show a host collection
    list                          List host collections
"""

from robottelo.cli.base import Base


class HostCollection(Base):
    """
    Manipulates Katello engine's host-collection command.
    """

    command_base = "host-collection"
