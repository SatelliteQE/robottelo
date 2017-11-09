# -*- encoding: utf-8 -*-
"""
Usage::

    policy [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

     SUBCOMMAND                    subcommand
     [ARG] ...                     subcommand arguments

Subcommands::

     create                        Create a Policy
     delete                        Delete a Policy
     info                          Show a Policy
     list                          List Policies
     update                        Update a Policy
"""
from robottelo.cli.base import Base


class Policy(Base):
    """
    Manipulates Satellite's policy.
    """
    command_base = 'policy'
