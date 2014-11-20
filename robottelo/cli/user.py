# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage::

    hammer user [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add-role                      Assign a user role
    create                        Create an user.
    delete                        Delete an user.
    info                          Show an user.
    list                          List all users.
    remove-role                   Remove a user role
    update                        Update an user.
"""

from robottelo.cli.base import Base


class User(Base):
    """
    Manipulates Foreman's users.
    """

    command_base = 'user'
