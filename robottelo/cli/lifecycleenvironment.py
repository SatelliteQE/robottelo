# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer lifecycle-environment [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    list                          List environments in an organization
    update                        Update an environment
    create                        Create an environment
    delete                        Destroy an environment
    info                          Show an environment
"""

from robottelo.cli.base import Base


class LifecycleEnvironment(Base):
    """
    Manipulates Katello engine's lifecycle-environment command.
    """

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
        self.command_base = "lifecycle-environment"
