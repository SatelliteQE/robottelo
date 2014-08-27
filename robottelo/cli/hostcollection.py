# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage::

    hammer host-collection [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    copy
    create                        Create a host collection
    delete                        Destroy a host collection
    info                          Show a host collection
    list                          List host collections
"""

from robottelo.cli.base import Base


class HostCollection(Base):
    """
    Manipulates Katello engine's host-collection command.
    """

    command_base = "host-collection"

    @classmethod
    def add_content_host(cls, options=None):
        """
        Associate a content-host
        """
        cls.command_sub = "add-content-host"
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_content_host(cls, options=None):
        """
        Remove a content-host
        """
        cls.command_sub = "remove-content-host"
        return cls.execute(cls._construct_command(options))

    @classmethod
    def content_hosts(cls, options=None):
        """
        List content-hosts added to the host collection
        Usage::

        hammer host-collection content-hosts [OPTIONS]

        Options::

        --id ID                       Id of the host collection
        --name NAME                   Host collection name to search by
        --organization ORGANIZATION_NAME Organization name to search by
        --organization-id ORGANIZATION_ID
        --organization-label ORGANIZATION_LABEL Organization label to search by
        """
        cls.command_sub = "content-hosts"
        return cls.execute(cls._construct_command(options), expect_csv=True)
