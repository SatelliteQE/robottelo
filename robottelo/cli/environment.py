# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage::

    hammer environment [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create an environment.
    info                          Show an environment.
    list                          List all environments.
    update                        Update an environment.
    sc_params                     List all smart class parameters
    delete                        Delete an environment.
"""

from robottelo.cli.base import Base


class Environment(Base):
    """
    Manipulates Foreman's environments.
    """

    command_base = "environment"
