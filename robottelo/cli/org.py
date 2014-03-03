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

    command_base = "organization"

    def __init__(self):
        """
        Sets the base command for class
        """
        Base.__init__(self)

    @classmethod
    def add_subnet(cls, options=None):
        """
        Adds existing subnet to an org
        """

        cls.command_sub = "add_subnet"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_subnet(cls, options=None):
        """
        Removes a subnet from an org
        """

        cls.command_sub = "remove_subnet"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_domain(cls, options=None):
        """
        Adds a domain to an org
        """

        cls.command_sub = "add_domain"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_domain(cls, options=None):
        """
        Removes a domain from an org
        """

        cls.command_sub = "remove_domain"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_user(cls, options=None):
        """
        Adds an user to an org
        """

        cls.command_sub = "add_user"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_user(cls, options=None):
        """
        Removes an user from an org
        """

        cls.command_sub = "remove_user"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_hostgroup(cls, options=None):
        """
        Adds a hostgroup to an org
        """

        cls.command_sub = "add_hostgroup"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_hostgroup(cls, options=None):
        """
        Removes a hostgroup from an org
        """

        cls.command_sub = "remove_hostgroup"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_computeresource(cls, options=None):
        """
        Adds a computeresource to an org
        """

        cls.command_sub = "add_computeresource"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_computeresource(cls, options=None):
        """
        Removes a computeresource from an org
        """

        cls.command_sub = "remove_computeresource"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_medium(cls, options=None):
        """
        Adds a medium to an org
        """

        cls.command_sub = "add_medium"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_medium(cls, options=None):
        """
        Removes a medium from an org
        """

        cls.command_sub = "remove_medium"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_configtemplate(cls, options=None):
        """
        Adds a configtemplate to an org
        """

        cls.command_sub = "add_configtemplate"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_configtemplate(cls, options=None):
        """
        Removes a configtemplate from an org
        """

        cls.command_sub = "remove_configtemplate"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_environment(cls, options=None):
        """
        Adds an environment to an org
        """

        cls.command_sub = "add_environment"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_environment(cls, options=None):
        """
        Removes an environment from an org
        """

        cls.command_sub = "remove_environment"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_smartproxy(cls, options=None):
        """
        Adds a smartproxy to an org
        """

        cls.command_sub = "add_smartproxy"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_smartproxy(cls, options=None):
        """
        Removes a smartproxy from an org
        """

        cls.command_sub = "remove_smartproxy"

        return cls.execute(cls._construct_command(options))
