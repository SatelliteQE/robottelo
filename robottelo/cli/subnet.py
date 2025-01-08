"""
Usage::

    hammer subnet [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a subnet
    delete                        Delete a subnet
    info                          Show a subnet.
    list                          List of subnets
    update                        Update a subnet

"""

from robottelo.cli.base import Base


class Subnet(Base):
    """
    Manipulates Foreman's subnets.
    """

    command_base = 'subnet'
