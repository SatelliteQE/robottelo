# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer subnet [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Create a subnet
    info                          Show a subnet.
    list                          List of subnets
    update                        Update a subnet
    delete                        Delete a subnet

"""

from robottelo.cli.base import Base


class Subnet(Base):
    """
    Manipulates Foreman's subnets.
    """

    command_base = "subnet"

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
