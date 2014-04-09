# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer system-group [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    copy
    create                        Create a system group
    info                          Show a system group
    list                          List system groups
"""

from robottelo.cli.base import Base


class SystemGroup(Base):
    """
    Manipulates Katello engine's system-group command.
    """

    command_base = "system-group"
    command_requires_org = True
