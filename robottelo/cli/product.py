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
    command_requires_org = True

    @classmethod
    def info(cls, options=None):
        """
        Gets information by provided: options dictionary.
        @param options: ID (sometimes name or id).
        """
        cls.command_sub = "info"

        # Use the 'base' output adapter
        result = cls.execute(cls._construct_command(options), expect_csv=False)

        # This will hold our GPG key dictionary
        gpg_key = {}

        for items in result.stdout:
            # Break each item splitting at the ':'
            # Example:  Organization: dTVfLkUhHIDiwPIQHqRn
            item = items.split(':')
            # Get rid of empty items
            if len(item) == 2:
                # Strip leading whitespace, use dashes and lower keys
                key = item[0].lstrip().replace(' ', '-').lower()
                # Strip leading whitespaces from values
                value = item[1].lstrip()
                # Build the dictionary
                gpg_key[key] = value

        # Update result.stdout
        result.stdout = gpg_key

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
