# -*- encoding: utf-8 -*-
"""
Usage::

    hammer product [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a product
    delete                        Destroy a product
    info                          Show a product
    list                          List products in an environment
    remove_sync_plan              Delete assignment sync plan and product.
    set_sync_plan                 Assign sync plan to product.
    synchronize                   Sync a repository
    update                        Update a product
"""

from robottelo.cli.base import Base


class Product(Base):
    """
    Manipulates Katello engine's product command.
    """

    command_base = 'product'
    command_requires_org = True

    @classmethod
    def remove_sync_plan(cls, options=None):
        """
        Delete assignment sync plan and product.
        """

        cls.command_sub = 'remove-sync-plan'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def set_sync_plan(cls, options=None):
        """
        Assign sync plan to product.
        """

        cls.command_sub = 'set-sync-plan'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def synchronize(cls, options=None):
        """Synchronize a product."""
        cls.command_sub = 'synchronize'
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
        )
