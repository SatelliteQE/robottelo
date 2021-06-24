"""
Usage::

    hammer proxy [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a smart proxy.
    delete                        Delete a smart_proxy.
    import_classes                Import puppet classes from puppet proxy.
    info                          Show a smart proxy.
    list                          List all smart_proxies.
    refresh-features              Refresh smart proxy features
    update                        Update a smart proxy.
"""
from robottelo.cli.base import Base


class CapsuleTunnelError(Exception):
    """Raised when tunnel creation fails."""


class Proxy(Base):
    """Manipulates Foreman's smart proxies."""

    command_base = 'proxy'

    @classmethod
    def import_classes(cls, options=None):
        """Import puppet classes from puppet proxy."""
        cls.command_sub = 'import-classes'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def refresh_features(cls, options=None):
        """Refreshes smart proxy features"""
        cls.command_sub = 'refresh-features'
        return cls.execute(cls._construct_command(options))
