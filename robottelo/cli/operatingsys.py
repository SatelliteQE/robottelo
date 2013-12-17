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

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
        self.command_base = "os"

    def add_architecture(self, options=None):
        """
        Adds existing architecture to OS.
        """

        self.command_sub = "add_architecture"

        result = self.execute(self._construct_command(options))

        return result

    def add_configtemplate(self, options=None):
        """
        Adds existing template to OS.
        """

        self.command_sub = "add_configtemplate "

        result = self.execute(self._construct_command(options))

        return result

    def add_ptable(self, options=None):
        """
        Adds existing partitioning table to OS.
        """

        self.command_sub = "add_ptable"

        result = self.execute(self._construct_command(options))

        return result

    def remove_architecture(self, options=None):
        """
        Removes architecture from OS.
        """

        self.command_sub = "remove_architecture"

        result = self.execute(self._construct_command(options))

        return result

    def remove_configtemplate(self, options=None):
        """
        Removes template from OS.
        """

        self.command_sub = "remove_configtemplate"

        result = self.execute(self._construct_command(options))

        return result

    def remove_ptable(self, options=None):
        """
        Removes partitioning table from OS.
        """

        self.command_sub = "os remove_ptable "

        result = self.execute(self._construct_command(options))

        return result
