"""
Usage::

    hammer medium [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add_operatingsystem           Associate a resource
    create                        Create a medium.
    delete                        Delete a medium.
    info                          Show a medium.
    list                          List all media.
    remove_operatingsystem        Disassociate a resource
    update                        Update a medium.
"""

from robottelo.cli.base import Base


class Medium(Base):
    """
    Manipulates Foreman's installation media.
    """

    command_base = 'medium'
