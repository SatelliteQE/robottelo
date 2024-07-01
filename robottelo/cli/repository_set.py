"""
Implementing the repository-set hammer command

Usage::

    hammer repository-set [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    available-repositories        Get list or available repositories for
                                  the repository set
    disable                       Disable a repository
    enable                        Enable a repository
    info                          Show a repository
    list                          List of repositories
"""

from robottelo.cli.base import Base


class RepositorySet(Base):
    """
    Manipulates Katello engine's repository command.
    """

    command_base = 'repository-set'

    @classmethod
    def enable(cls, options):
        """Enables a repository."""
        cls.command_sub = 'enable'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def disable(cls, options):
        """Disables a repository."""
        cls.command_sub = 'disable'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def available_repositories(cls, options):
        """Lists the available repositories.

        hammer repository-set available-repositories --help

        Usage::

            hammer repository-set available-repositories [OPTIONS]

        Options::

            --id ID                                 ID of the repository set
            --name NAME                             Repository set
                                                    name to search by
            --organization ORGANIZATION_NAME        Organization
                                                    name to search by
            --organization-id ORGANIZATION_ID       organization ID
            --organization-label ORGANIZATION_LABEL Organization label
                                                    to search by
            --product PRODUCT_NAME                  Product name
                                                    to search by
            --product-id PRODUCT_ID                 product numeric identifier
            -h, --help                              print help

        """
        cls.command_sub = 'available-repositories'
        return cls.execute(cls._construct_command(options), output_format='csv')
