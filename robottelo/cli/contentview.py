# -*- encoding: utf-8 -*-
"""
Usage::

    hammer content-view [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add-repository                Associate a resource
    add-version                   Associate a resource
    create                        Create a content view
    filter                        View and manage filters
    info                          Show a content view
    list                          List content views
    publish                       Publish a content view
    puppet-module                 View and manage puppet modules
    remove                        Remove versions and/or environments from a
                                  content view and reassign systems and keys
    remove-from-environment       Remove a content view from an environment
    remove-repository             Disassociate a resource
    remove-version                Disassociate a resource
    update                        Update a content view
    version                       View and manage content view versions

Options::

    -h, --help                    print help
"""

from robottelo.cli import hammer
from robottelo.cli.base import Base


class ContentView(Base):
    """Manipulates Foreman's content view."""

    command_base = 'content-view'

    @classmethod
    def add_repository(cls, options):
        """Associate repository to a selected CV."""
        cls.command_sub = 'add-repository'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def add_version(cls, options):
        """Associate version to a selected CV."""
        cls.command_sub = 'add-version'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def publish(cls, options, timeout=None):
        """Publishes a new version of content-view."""
        cls.command_sub = 'publish'

        # Publishing can take a while so try to wait a bit longer
        if timeout is None:
            timeout = 120

        return cls.execute(cls._construct_command(options), timeout=timeout)

    @classmethod
    def version_info(cls, options):
        """Provides version info related to content-view's version."""
        cls.command_sub = 'version info'

        if options is None:
            options = {}

        result = cls.execute(cls._construct_command(options))
        result.stdout = hammer.parse_info(result.stdout)
        return result

    @classmethod
    def puppet_module_add(cls, options):
        """Associate puppet_module to selected CV"""
        cls.command_sub = 'puppet-module add'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def puppet_module_info(cls, options):
        """Provides puppet-module info related to content-view's version."""
        cls.command_sub = 'puppet-module info'

        if options is None:
            options = {}

        result = cls.execute(cls._construct_command(options))
        result.stdout = hammer.parse_info(result.stdout)
        return result

    @classmethod
    def filter_info(cls, options):
        """Provides filter info related to content-view's version."""

        cls.command_sub = 'filter info'

        if options is None:
            options = {}

        result = cls.execute(cls._construct_command(options))
        result.stdout = hammer.parse_info(result.stdout)
        return result

    @classmethod
    def filter_create(cls, options):
        """Provides filter info related to content-view's version."""
        cls.command_sub = 'filter create'

        if options is None:
            options = {}

        return cls.execute(cls._construct_command(options))

    @classmethod
    def filter_rule_create(cls, options):
        """Provides filter info related to content-view's version."""
        cls.command_sub = 'filter rule create'

        if options is None:
            options = {}

        return cls.execute(cls._construct_command(options))

    @classmethod
    def version_list(cls, options):
        """Lists content-view's versions."""
        cls.command_sub = 'version list'

        if options is None:
            options = {}

        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def version_promote(cls, options):
        """Promotes content-view version to next env."""
        cls.command_sub = 'version promote'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def version_delete(cls, options):
        """Removes content-view version."""
        cls.command_sub = 'version delete'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_from_environment(cls, options=None):
        """Remove content-view from an enviornment"""
        cls.command_sub = 'remove-from-environment'
        return cls.execute(cls._construct_command(options))
