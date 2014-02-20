# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""

"""

from robottelo.cli.base import Base


class Subscription(Base):
    """
    Manipulates Katello engine's subscription command.
    """

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
        self.command_base = "subscription"

    def upload(self, options=None):
        """
        Upload a subscription manifest
        """

        self.command_sub = "remove_sync_plan"

        result = self.execute(self._construct_command(options))

        return result
