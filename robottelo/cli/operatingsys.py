#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.cli.base import Base


class OperatingSys(Base):

    def __init__(self):
        self.command_base = "os"

    def add_architecture(self, options=None):
        """
        Adds existing architecture to OS.
        """

        self.command_sub = "add_architecture"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def add_configtemplate(self, options=None):
        """
        Adds existing template to OS.
        """

        self.command_sub = "add_configtemplate "

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def add_ptable(self, options=None):
        """
        Adds existing partitioning table to OS.
        """

        self.command_sub = "add_ptable"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def delete_parameter(self, options=None):
        """
        Deletes parameter from OS.
        """

        self.command_sub = "delete_parameter"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def remove_architecture(self, options=None):
        """
        Removes architecture from OS.
        """

        self.command_sub = "remove_architecture"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def remove_configtemplate(self, options=None):
        """
        Removes template from OS.
        """

        self.command_sub = "remove_configtemplate"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def remove_ptable(self, options=None):
        """
        Removes partitioning table from OS.
        """

        self.command_sub = "os remove_ptable "

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def set_parameter(self, options=None):
        """
        Adds a new parameter to the OS.
        """

        self.command_sub = "set_parameter"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True
