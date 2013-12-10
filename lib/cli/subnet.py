#!/usr/bin/env python
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
from lib.cli.base import Base
from lib.common.helpers import generate_ipaddr
from lib.common.helpers import generate_name


class Subnet(Base):

    def __init__(self):
        self.command_base = "subnet"

    def create_minimal(self, name=None, network=None):
        options = {}
        options['name'] = name if name else generate_name(8, 8)
        options['network'] = network if network else generate_ipaddr(ip3=True)
        options['mask'] = '255.255.255.0'
        return self.create(options)
