# -*- encoding: utf-8 -*-
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

    @classmethod
    def add_role(cls, options=None):
        """Add a role to a user."""
        cls.command_sub = 'add-role'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def remove_role(cls, options=None):
        """Remove a role from user."""
        cls.command_sub = 'remove-role'
        return cls.execute(cls._construct_command(options), output_format='csv')
