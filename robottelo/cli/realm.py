"""
Usage:
    hammer realm [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    subcommand
 [ARG] ...                     subcommand arguments

Subcommands:
 create                        Create a realm
 delete                        Delete a realm
 info                          Show a realm
 list                          List of realms
 update                        Update a realm

Options:
 -h, --help                    print help
"""

from robottelo.cli.base import Base


class Realm(Base):
    """Manipulates Realm subcommand"""

    command_base = 'realm'
