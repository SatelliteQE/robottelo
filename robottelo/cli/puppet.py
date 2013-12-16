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

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
        self.command_base = "puppet_class"
