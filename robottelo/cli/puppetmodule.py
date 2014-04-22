# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer puppet-module [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    info                          Show a puppet module
    list                          List puppet modules
"""

from robottelo.cli.base import Base


class PuppetModule(Base):
    """
    To list OR show puppet modules.
    """

    command_base = "puppet-module"
