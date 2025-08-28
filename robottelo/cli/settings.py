"""
Usage::

    hammer settings [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    list                          List all settings
    set                           Update a setting
    info                          Show a setting
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

    @classmethod
    def info(cls, options=None, output_format=None, return_raw_response=None):
        """Show setting info"""
        cls.command_sub = 'info'

        return cls.execute(
            cls._construct_command(options),
            output_format=output_format,
            return_raw_response=return_raw_response,
        )
