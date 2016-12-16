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
 hosts                         List all hosts
 info                          Show a host collection
 list                          List host collections
 package                       Manipulate packages for a host collection
 package-group                 Manipulate package-groups for a host collection
 remove-host                   Remove hosts from the host collection
 update                        Update a host collection
"""

from robottelo.cli.base import Base
from robottelo.cli.contenthost import ContentHost
from robottelo.cli.host import Host


class HostCollection(Base):
    """Manipulates Katello engine's host-collection command."""

    command_base = 'host-collection'

    @classmethod
    def transform_ids(cls, options=None):
        """Workaround host unification feature not being completed to use host
        id instead content host uuid
        """
        if 'host-ids' in options:
            host_ids = [
                host_id if host_id.isdigit() else
                Host.info({
                    'name': ContentHost.info({'id': host_id})['name'].lower()
                })['id']
                for host_id in options.get('host-ids').split(',')
            ]
            if host_ids:
                options['host-ids'] = ','.join(host_ids)

    @classmethod
    def add_host(cls, options=None):
        """Add host to the host collection"""
        cls.command_sub = 'add-host'
        cls.transform_ids(options)
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_host(cls, options=None):
        """Remove hosts from the host collection"""
        cls.command_sub = 'remove-host'
        cls.transform_ids(options)
        return cls.execute(cls._construct_command(options))

    @classmethod
    def hosts(cls, options=None):
        """
        List hosts added to the host collection

        Usage::

            hammer host-collection hosts [OPTIONS]

        Options::

             --environment ENVIRONMENT_NAME          Name to search by
             --environment-id ENVIRONMENT_ID
             --hostgroup HOSTGROUP_NAME              Name to search by
             --hostgroup-id HOSTGROUP_ID
             --id HOST_COLLECTION_ID                 Host Collection ID
             --location LOCATION_NAME                Name to search by
             --location-id LOCATION_ID
             --name HOST_COLLECTION_NAME             Host Collection Name
             --order ORDER                           sort results
             --organization ORGANIZATION_NAME        Organization name to
                                                     search by
             --organization-id ORGANIZATION_ID       organization ID
             --organization-label ORGANIZATION_LABEL Organization label to
                                                     search by
             --page PAGE                             paginate results
             --per-page PER_PAGE                     number of entries per
                                                     request
             --search SEARCH                         filter results
             -h, --help                              print help
        """
        cls.command_sub = 'hosts'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def erratum_install(cls, options):
        """Schedule errata for installation"""
        cls.command_sub = 'erratum install'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def package_install(cls, options):
        """Schedule package for installation"""
        cls.command_sub = 'package install'
        return cls.execute(
            cls._construct_command(options), output_format='csv')
