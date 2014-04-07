# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""

"""

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

        cls.command_sub = "remove_sync_plan"

        result = cls.execute(cls._construct_command(options))

        return result
