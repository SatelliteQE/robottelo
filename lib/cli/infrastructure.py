# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

'''
Module for the following classes:
- SmartProxy
- ComputeResource
- Subnet
- Domain
'''
from lib.cli.base import Base
from lib.common.helpers import generate_ip3, generate_name


class Subnet(Base):
    '''
    Usage:
        hammer subnet [OPTIONS] SUBCOMMAND [ARG] ...

    Parameters:
        SUBCOMMAND                    subcommand
        [ARG] ...                     subcommand arguments

    Subcommands:
        list                          List of subnets
        update                        Update a subnet
        delete                        Delete a subnet
        create                        Create a subnet
        info                          Show a subnet.
    '''

    OUT_SUBNET_DELETED = "Subnet deleted"

    def __init__(self, conn):
        self.conn = conn
        self.command_base = "subnet"

    def create_minimal(self, name=generate_name(8, 8), network=generate_ip3()):
        options = {}
        options['name'] = name
        options['network'] = network
        options['mask'] = '255.255.255.0'
        return self.create(options)
