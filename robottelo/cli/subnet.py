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
from robottelo.common.helpers import generate_ipaddr, generate_name


class Subnet(Base):
    """
    Manipulates Foreman's subnets.
    """

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
        self.command_base = "subnet"

    #TODO: switch to use factory make_subnet
    def create_minimal(self, name=None, network=None):
        """
        Creates a minimal subnet object.
        """
        options = {}
        options['name'] = name if name else generate_name(8, 8)
        options['network'] = network if network else generate_ipaddr(ip3=True)
        options['mask'] = '255.255.255.0'
        return self.create(options)
