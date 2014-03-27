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

    command_base = "product"

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)

    @classmethod
    def list(cls, organization_id, options=None):
        """
        Lists available products.
        """

        cls.command_sub = "list"

        if options is None:
            options = {}
            options['per-page'] = 10000

        # Katello subcommands require the organization-id
        options['organization-id'] = organization_id

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def remove_sync_plan(cls, options=None):
        """
        Delete assignment sync plan and product.
        """

        cls.command_sub = "remove_sync_plan"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def set_sync_plan(cls, options=None):
        """
        Assign sync plan to product.
        """

        cls.command_sub = "set_sync_plan"

        result = cls.execute(cls._construct_command(options))

        return result
