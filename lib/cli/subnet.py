# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.cli.base import Base


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

    def __init__(self, conn):
        self.conn = conn
        self.command_base = "subnet"

    def create(self, options=None):
        '''
        Usage:
            hammer subnet create [OPTIONS]

        Options:
            --name NAME                   Subnet name
            --network NETWORK             Subnet network
            --mask MASK                   Netmask for this subnet
            --gateway GATEWAY             Primary DNS for this subnet
            --dns-primary DNS_PRIMARY     Primary DNS for this subnet
            --dns-secondary DNS_SECONDARY Secondary DNS for this subnet
            --from FROM                   Starting IP Address for
                IP auto suggestion
            --to TO                       Ending IP Address for
                IP auto suggestion
            --vlanid VLANID               VLAN ID for this subnet
            --domain-ids DOMAIN_IDS       Domains in which this subnet is part
                                          Comma separated list of values.
            --dhcp-id DHCP_ID             DHCP Proxy to use within this subnet
            --tftp-id TFTP_ID             TFTP Proxy to use within this subnet
            --dns-id DNS_ID               DNS Proxy to use within this subnet
            -h, --help                    print help
        '''
        if options is None:
            options = {}
        self.command_sub = "create"
        return self.execute(self._construct_command(options))
