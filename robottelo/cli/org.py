#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer model [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    add_subnet                    Associate a resource
    update                        Update an organization
    add_domain                    Associate a resource
    add_user                      Associate a resource
    add_hostgroup                 Associate a resource
    remove_computeresource        Disassociate a resource
    remove_medium                 Disassociate a resource
    remove_configtemplate         Disassociate a resource
    delete                        Delete an organization
    remove_environment            Disassociate a resource
    remove_smartproxy             Disassociate a resource
    add_computeresource           Associate a resource
    add_medium                    Associate a resource
    add_configtemplate            Associate a resource
    create                        Create an organization
    add_environment               Associate a resource
    info                          Show an organization
    remove_subnet                 Disassociate a resource
    remove_domain                 Disassociate a resource
    remove_user                   Disassociate a resource
    remove_hostgroup              Disassociate a resource
    add_smartproxy                Associate a resource
    list                          List all organizations
"""

from robottelo.cli.base import Base


class Org(Base):
    """
    Manipulates Foreman's Organizations
    """

    def __init__(self):
        """
        Sets the base command for class
        """
        Base.__init__(self)
        self.command_base = "organization"

    def add_subnet(self, options=None):
        """
        Adds existing subnet to an org
        """

        self.command_sub = "add_subnet"

        return self.execute(self._construct_command(options))

    def remove_subnet(self, options=None):
        """
        Removes a subnet from an org
        """

        self.command_sub = "remove_subnet"

        return self.execute(self._construct_command(options))

    def add_domain(self, options=None):
        """
        Adds a domain to an org
        """

        self.command_sub = "add_domain"

        return self.execute(self._construct_command(options))

    def remove_domain(self, options=None):
        """
        Removes a domain from an org
        """

        self.command_sub = "remove_domain"

        return self.execute(self._construct_command(options))

    def add_user(self, options=None):
        """
        Adds an user to an org
        """

        self.command_sub = "add_user"

        return self.execute(self._construct_command(options))

    def remove_user(self, options=None):
        """
        Removes an user from an org
        """

        self.command_sub = "remove_user"

        return self.execute(self._construct_command(options))

    def add_hostgroup(self, options=None):
        """
        Adds a hostgroup to an org
        """

        self.command_sub = "add_hostgroup"

        return self.execute(self._construct_command(options))

    def remove_hostgroup(self, options=None):
        """
        Removes a hostgroup from an org
        """

        self.command_sub = "remove_hostgroup"

        return self.execute(self._construct_command(options))

    def add_computeresource(self, options=None):
        """
        Adds a computeresource to an org
        """

        self.command_sub = "add_computeresource"

        return self.execute(self._construct_command(options))

    def remove_computeresource(self, options=None):
        """
        Removes a computeresource from an org
        """

        self.command_sub = "remove_computeresource"

        return self.execute(self._construct_command(options))

    def add_medium(self, options=None):
        """
        Adds a medium to an org
        """

        self.command_sub = "add_medium"

        return self.execute(self._construct_command(options))

    def remove_medium(self, options=None):
        """
        Removes a medium from an org
        """

        self.command_sub = "remove_medium"

        return self.execute(self._construct_command(options))

    def add_configtemplate(self, options=None):
        """
        Adds a configtemplate to an org
        """

        self.command_sub = "add_configtemplate"

        return self.execute(self._construct_command(options))

    def remove_configtemplate(self, options=None):
        """
        Removes a configtemplate from an org
        """

        self.command_sub = "remove_configtemplate"

        return self.execute(self._construct_command(options))

    def add_environment(self, options=None):
        """
        Adds an environment to an org
        """

        self.command_sub = "add_environment"

        return self.execute(self._construct_command(options))

    def remove_environment(self, options=None):
        """
        Removes an environment from an org
        """

        self.command_sub = "remove_environment"

        return self.execute(self._construct_command(options))

    def add_smartproxy(self, options=None):
        """
        Adds a smartproxy to an org
        """

        self.command_sub = "add_smartproxy"

        return self.execute(self._construct_command(options))

    def remove_smartproxy(self, options=None):
        """
        Removes a smartproxy from an org
        """

        self.command_sub = "remove_smartproxy"

        return self.execute(self._construct_command(options))
