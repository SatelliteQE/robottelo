# -*- encoding: utf-8 -*-
"""
Usage::

    hammer sunscription [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    delete-manifest               Delete manifest from Red Hat provider
    list                          List organization subscriptions
    manifest-history              obtain manifest history for subscriptions
    refresh-manifest              Refresh previously imported manifest for
                                  Red Hat provider
    upload                        Upload a subscription manifest

"""

from robottelo.cli.base import Base
from robottelo.decorators import affected_by_bz


class Subscription(Base):
    """
    Manipulates Katello engine's subscription command.
    """

    command_base = 'subscription'

    @classmethod
    def upload(cls, options=None):
        """Upload a subscription manifest."""
        cls.command_sub = 'upload'
        timeout = 900 if affected_by_bz(1339696) else 300
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
            timeout=timeout,
        )

    @classmethod
    def delete_manifest(cls, options=None):
        """Deletes a subscription manifest."""
        cls.command_sub = 'delete-manifest'
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
        )

    @classmethod
    def refresh_manifest(cls, options=None):
        """Refreshes a subscription manifest."""
        cls.command_sub = 'refresh-manifest'
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
        )

    @classmethod
    def manifest_history(cls, options=None):
        """Provided history for subscription manifest"""
        cls.command_sub = 'manifest-history'
        return cls.execute(cls._construct_command(options))
