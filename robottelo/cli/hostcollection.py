# -*- encoding: utf-8 -*-
"""
Usage::

    hammer host-collection [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

 SUBCOMMAND                    subcommand
 [ARG] ...                     subcommand arguments

Subcommands::

 add-host                      Add host to the host collection
 copy                          Make copy of a host collection
 create                        Create a host collection
 delete                        Destroy a host collection
 erratum                       Manipulate errata for a host collection
 hosts
 info                          Show a host collection
 list                          List host collections
 package                       Manipulate packages for a host collection
 package-group                 Manipulate package-groups for a host collection
 remove-host                   Remove hosts from the host collection
 update                        Update a host collection

"""

from robottelo.cli.base import Base


class HostCollection(Base):
    """Manipulates Katello engine's host-collection command."""

    command_base = 'host-collection'

    @classmethod
    def add_host(cls, options=None):
        """Add host to the host collection"""
        cls.command_sub = 'add-host'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_host(cls, options=None):
        """Remove hosts from the host collection"""
        cls.command_sub = 'remove-host'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def hosts(cls, options=None):
        """
        List content-hosts added to the host collection

        Usage::

            hammer host-collection content-hosts [OPTIONS]

        Options::

            --id ID                       Id of the host collection
            --name NAME                   Host collection name to search by
            --organization ORGANIZATION_NAME Organization name to search by
            --organization-id ORGANIZATION_ID
            --organization-label Organization label to search by
        """
        cls.command_sub = 'hosts'
        return cls.execute(
            cls._construct_command(options), output_format='csv')
