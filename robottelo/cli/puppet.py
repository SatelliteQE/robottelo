# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer puppet_class [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    sc_params                     List all smart class parameters
    info                          Show a puppetclass
    list                          List all puppetclasses.
"""

from robottelo.cli.base import Base


class Puppet(Base):
    """
    Search Foreman's puppet modules.
    """

    command_base = "puppet-class"
