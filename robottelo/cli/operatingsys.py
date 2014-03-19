# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer os [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    set_parameter                 Create or update parameter for an
                                  operating system.
    remove_configtemplate         Disassociate a resource
    create                        Create an OS.
    info                          Show an OS.
    add_configtemplate            Associate a resource
    remove_architecture           Disassociate a resource
    list                          List all operating systems.
    remove_ptable                 Disassociate a resource
    update                        Update an OS.
    add_architecture              Associate a resource
    add_ptable                    Associate a resource
    delete                        Delete an OS.
    delete_parameter              Delete parameter for an operating system.
"""

from robottelo.cli.base import Base


class OperatingSys(Base):
    """
    Manipulates Foreman's operating systems.
    """

    command_base = "os"

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)

    @classmethod
    def add_architecture(cls, options=None):
        """
        Adds existing architecture to OS.
        """

        cls.command_sub = "add-architecture"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def add_configtemplate(cls, options=None):
        """
        Adds existing template to OS.
        """

        cls.command_sub = "add-configtemplate "

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def add_ptable(cls, options=None):
        """
        Adds existing partitioning table to OS.
        """

        cls.command_sub = "add-ptable"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def remove_architecture(cls, options=None):
        """
        Removes architecture from OS.
        """

        cls.command_sub = "remove-architecture"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def remove_configtemplate(cls, options=None):
        """
        Removes template from OS.
        """

        cls.command_sub = "remove-configtemplate"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def remove_ptable(cls, options=None):
        """
        Removes partitioning table from OS.
        """

        cls.command_sub = "remove-ptable "

        result = cls.execute(cls._construct_command(options))

        return result
