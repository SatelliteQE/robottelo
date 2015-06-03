# -*- encoding: utf-8 -*-
"""
Usage::

    hammer content-host [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    available-incremental-updates Given a set of systems and errata, lists the
                                  content view versions and environments that
                                  need updating.
    create                        Register a content host
    delete                        Unregister a content host
    errata                        Manage errata on your content hosts
    info                          Show a content host
    list                          List content hosts
    package                       Manage packages on your content hosts
    package-group                 Manage package-groups on your content hosts
    tasks
    update                        Update content host information

"""
from robottelo.cli.base import Base


class ContentHost(Base):
    """Manipulates Katello engine's content-host command."""
    command_base = 'content-host'

    @classmethod
    def errata_apply(cls, options):
        """Schedule errata for installation"""
        cls.command_sub = 'errata apply'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def errata_info(cls, options):
        """Retrieve a single errata for a system"""
        cls.command_sub = 'errata info'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def errata_list(cls, options):
        """List errata available for the content host."""
        cls.command_sub = 'errata list'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def package_install(cls, options):
        """Install packages remotely."""
        cls.command_sub = 'package install'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def package_remove(cls, options):
        """Uninstall packages remotely."""
        cls.command_sub = 'package remove'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def package_upgrade(cls, options):
        """Update packages remotely."""
        cls.command_sub = 'package upgrade'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def package_upgrade_all(cls, options):
        """Update all packages remotely."""
        cls.command_sub = 'package upgrade-all'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def package_group_install(cls, options):
        """Install package groups remotely."""
        cls.command_sub = 'package-group install'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def package_group_remove(cls, options):
        """Uninstall package groups remotely."""
        cls.command_sub = 'package-group remove'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def tasks(cls, options=None):
        """Lists async tasks for a content host."""
        cls.command_sub = 'tasks'
        return cls.execute(
            cls._construct_command(options), output_format='csv')
