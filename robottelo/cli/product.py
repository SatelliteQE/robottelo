# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer product [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    list                          List products in an environment
    update                        Update a product
    create                        Create a product
    delete                        Destroy a product
    info                          Show a product
    remove_sync_plan              Delete assignment sync plan and product.
    set_sync_plan                 Assign sync plan to product.
"""

from robottelo.cli.base import Base


class Product(Base):
    """
    Manipulates Katello engine's product command.
    """

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
        self.command_base = "product"

    def remove_sync_plan(self, options=None):
        """
        Delete assignment sync plan and product.
        """

        self.command_sub = "remove_sync_plan"

        result = self.execute(self._construct_command(options))

        return result

    def set_sync_plan(self, options=None):
        """
        Assign sync plan to product.
        """

        self.command_sub = "set_sync_plan"

        result = self.execute(self._construct_command(options))

        return result
