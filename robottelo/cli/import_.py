# -*- encoding: utf-8 -*-
"""
Usage::

    hammer import [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    activation-key                Import Activation Keys
                                  (from spacewalk-report activation-keys).
    all                           Load ALL data from a specified directory
                                  that is in spacewalk-export format.
    config-file                   Create puppet-modules from Configuration
                                  Channel content (from spacewalk-report
                                  config-files-latest).
    content-host                  Import Content Hosts
                                  (from spacewalk-report system-profiles).
    content-view                  Create Content Views based on local/cloned
                                  Channels (from spacewalk-export-channels).
    host-collection               Import Host Collections
                                  (from spacewalk-report system-groups).
    organization                  Import Organizations
                                  (from spacewalk-report users).
    repository                    Import repositories
                                  (from spacewalk-report repositories).
    repository-enable             Enable any Red Hat repositories
                                  accessible to any Organization
                                  (from spacewalk-report channels).
    template-snippet              Import template snippets
                                  (from spacewalk-report kickstart-scripts).
    user                          Import Users (from spacewalk-report users).

"""
from robottelo.cli.base import Base


class Import(Base):
    """Imports configurations from another Satellite instances."""
    command_base = 'import'

    @classmethod
    def activation_key(cls, options=None):
        """Import Activation Keys (from spacewalk-report activation-keys).
        Requires organization.

        """
        cls.command_sub = 'activation-key'
        return cls.execute(
            cls._construct_command(options),
            output_format='csv'
        )

    @classmethod
    def organization(cls, options=None):
        """Import Organizations (from spacewalk-report users)."""
        cls.command_sub = 'organization'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def user(cls, options=None):
        """Import Users (from spacewalk-report users)."""
        cls.command_sub = 'user'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def host_collection(cls, options=None):
        """Import Host Collections (from spacewalk-report system-groups)."""
        cls.command_sub = 'host-collection'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def config_file(cls, options=None):
        """Create puppet-modules from Configuration Channel content (from
        spacewalk-report config-files-latest).

        """
        cls.command_sub = 'config-file'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def content_host(cls, options=None):
        """Import Content Hosts (from spacewalk-report system-profiles)."""
        cls.command_sub = 'content-host'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def content_view(cls, options=None):
        """Create Content Views based on local/cloned Channels (from
        spacewalk-export-channels).

        """
        cls.command_sub = 'content-view'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def repository(cls, options=None):
        """Import repositories (from spacewalk-report repositories)."""
        cls.command_sub = 'repository'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def repository_enable(cls, options=None):
        """Enable any Red Hat repositories accessible to any Organization
        (from spacewalk-report channels).

        """
        cls.command_sub = 'repository-enable'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def template_snippet(cls, options=None):
        """Import template snippets (from spacewalk-report
        kickstart-scripts).

        """
        cls.command_sub = 'template-snippet'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )

    @classmethod
    def all(cls, options=None):
        """Load ALL data from a specified directory that is in spacewalk-export
        format.

        """
        cls.command_sub = 'all'
        return cls.execute(
            cls._construct_command(options),
            output_format=''
        )
