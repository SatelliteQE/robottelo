# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer user [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Create an user.
    info                          Show an user.
    list                          List all users.
    update                        Update an user.
    delete                        Delete an user.
"""

from robottelo.cli.base import Base


class User(Base):
    """
    Manipulates Foreman's users.
    """

    command_base = "user"

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
