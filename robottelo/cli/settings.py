"""
Usage::

    hammer settings [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    list                          List all settings
    set                           Update a setting
"""

from robottelo.cli.base import Base


class Settings(Base):
    """Manipulates Foreman's settings."""

    command_base = 'settings'

    @classmethod
    def set(cls, options=None):
        """Update a setting"""
        cls.command_sub = 'set'

        return cls.execute(cls._construct_command(options))
