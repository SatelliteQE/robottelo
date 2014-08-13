# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

# FIXME: add a module docstring

from robottelo.cli.base import Base


class Subscription(Base):
    """
    Manipulates Katello engine's subscription command.
    """

    command_base = "subscription"

    @classmethod
    def upload(cls, options=None):
        """
        Upload a subscription manifest
        """

        cls.command_sub = "upload"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def delete_manifest(cls, options=None):
        """
        Deletes a subscription manifest
        """

        cls.command_sub = "delete-manifest"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def refresh_manifest(cls, options=None):
        """
        Refreshes a subscription manifest
        """

        cls.command_sub = "refresh-manifest"

        result = cls.execute(cls._construct_command(options))

        return result
