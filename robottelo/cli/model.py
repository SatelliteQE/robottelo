# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer model [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Create a model.
    info                          Show a model.
    list                          List all models.
    update                        Update a model.
    delete                        Delete a model.
"""

from robottelo.cli.base import Base


class Model(Base):
    """
    Manipulates Foreman's hardware model.
    """

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
        self.command_base = "model"
