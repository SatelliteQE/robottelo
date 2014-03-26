# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer model [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    add-subnet                    Associate a resource
    update                        Update an organization
    add-domain                    Associate a resource
    add-user                      Associate a resource
    add-hostgroup                 Associate a resource
    remove_computeresource        Disassociate a resource
    remove_medium                 Disassociate a resource
    remove_configtemplate         Disassociate a resource
    delete                        Delete an organization
    remove_environment            Disassociate a resource
    remove_smartproxy             Disassociate a resource
    add-computeresource           Associate a resource
    add-medium                    Associate a resource
    add-configtemplate            Associate a resource
    create                        Create an organization
    add-environment               Associate a resource
    info                          Show an organization
    remove_subnet                 Disassociate a resource
    remove_domain                 Disassociate a resource
    remove_user                   Disassociate a resource
    remove_hostgroup              Disassociate a resource
    add-smartproxy                Associate a resource
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

        cls.command_sub = "add-subnet"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_subnet(cls, options=None):
        """
        Removes a subnet from an org
        """

        cls.command_sub = "remove-subnet"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_domain(cls, options=None):
        """
        Adds a domain to an org
        """

        cls.command_sub = "add-domain"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_domain(cls, options=None):
        """
        Removes a domain from an org
        """

        cls.command_sub = "remove-domain"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_user(cls, options=None):
        """
        Adds an user to an org
        """

        cls.command_sub = "add-user"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_user(cls, options=None):
        """
        Removes an user from an org
        """

        cls.command_sub = "remove-user"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_hostgroup(cls, options=None):
        """
        Adds a hostgroup to an org
        """

        cls.command_sub = "add-hostgroup"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_hostgroup(cls, options=None):
        """
        Removes a hostgroup from an org
        """

        cls.command_sub = "remove-hostgroup"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_computeresource(cls, options=None):
        """
        Adds a computeresource to an org
        """

        cls.command_sub = "add-compute-resource"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_computeresource(cls, options=None):
        """
        Removes a computeresource from an org
        """

        cls.command_sub = "remove-compute-resource"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_medium(cls, options=None):
        """
        Adds a medium to an org
        """

        cls.command_sub = "add-medium"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_medium(cls, options=None):
        """
        Removes a medium from an org
        """

        cls.command_sub = "remove-medium"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_configtemplate(cls, options=None):
        """
        Adds a configtemplate to an org
        """

        cls.command_sub = "add-config-template"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_configtemplate(cls, options=None):
        """
        Removes a configtemplate from an org
        """

        cls.command_sub = "remove-config-template"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_environment(cls, options=None):
        """
        Adds an environment to an org
        """

        cls.command_sub = "add-environment"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_environment(cls, options=None):
        """
        Removes an environment from an org
        """

        cls.command_sub = "remove-environment"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_smartproxy(cls, options=None):
        """
        Adds a smartproxy to an org
        """

        cls.command_sub = "add-smart-proxy"

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_smartproxy(cls, options=None):
        """
        Removes a smartproxy from an org
        """

        cls.command_sub = "remove-smart-proxy"

        return cls.execute(cls._construct_command(options))
