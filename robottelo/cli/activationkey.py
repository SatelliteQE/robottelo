"""
Usage::

    hammer activation-key [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add-host-collection           Associate a resource
    add-subscription              Add subscription
    content-override              Override product content defaults
    copy                          Copy an activation key
    create                        Create an activation key
    delete                        Destroy an activation key
    host-collections              List associated host collections
    info                          Show an activation key
    list                          List activation keys
    product-content               List associated products
    remove-host-collection        Disassociate a resource
    remove-subscription           Remove subscription
    subscriptions                 List associated subscriptions
    update                        Update an activation key
"""

from robottelo.cli.base import Base


class ActivationKey(Base):
    """Manipulates Katello's activation-key."""

    command_base = 'activation-key'

    @classmethod
    def add_host_collection(cls, options=None):
        """Associate a resource"""
        cls.command_sub = 'add-host-collection'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_subscription(cls, options=None):
        """Add subscription"""
        cls.command_sub = 'add-subscription'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def content_override(cls, options=None):
        """Override product content defaults"""
        cls.command_sub = 'content-override'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def copy(cls, options=None):
        """Copy an activation key"""
        cls.command_sub = 'copy'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def host_collection(cls, options=None):
        """List associated host collections"""
        cls.command_sub = 'host-collections'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def product_content(cls, options=None):
        """List associated products"""
        cls.command_sub = 'product-content'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def remove_host_collection(cls, options=None):
        """Remove the associated resource"""
        cls.command_sub = 'remove-host-collection'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_repository(cls, options=None):
        """Disassociate a resource"""
        cls.command_sub = 'remove-repository'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_subscription(cls, options=None):
        """Remove subscription"""
        cls.command_sub = 'remove-subscription'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def subscriptions(cls, options=None, output_format=None):
        """List associated subscriptions"""
        cls.command_sub = 'subscriptions'
        return cls.execute(cls._construct_command(options), output_format=output_format)
