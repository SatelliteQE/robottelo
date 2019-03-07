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
from robottelo.decorators import bz_bug_is_open


class Subscription(Base):
    """
    Manipulates Katello engine's subscription command.
    """

    command_base = 'subscription'

    @classmethod
    def upload(cls, options=None, timeout=None):
        """Upload a subscription manifest."""
        cls.command_sub = 'upload'
        if bz_bug_is_open(1669186) and (timeout is None or timeout < 1500):
            timeout = 1500
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
            timeout=timeout,
        )

    @classmethod
    def delete_manifest(cls, options=None, timeout=None):
        """Deletes a subscription manifest."""
        cls.command_sub = 'delete-manifest'
        if bz_bug_is_open(1669186) and (timeout is None or timeout < 1500):
            timeout = 1500
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
            timeout=timeout,
        )

    @classmethod
    def refresh_manifest(cls, options=None, timeout=None):
        """Refreshes a subscription manifest."""
        cls.command_sub = 'refresh-manifest'
        if bz_bug_is_open(1669186) and (timeout is None or timeout < 1500):
            timeout = 1500
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
            timeout=timeout,
        )

    @classmethod
    def manifest_history(cls, options=None):
        """Provided history for subscription manifest"""
        cls.command_sub = 'manifest-history'
        return cls.execute(cls._construct_command(options))
