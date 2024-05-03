"""
Usage:
    hammer admin [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    Subcommand
 [ARG] ...                     Subcommand arguments

Subcommands:
 logging                       Logging verbosity level setup

Options:
 -h, --help                    Print help
"""

from robottelo.cli.base import Base


class Admin(Base):
    """Administrative server-side tasks"""

    command_base = 'admin'

    @classmethod
    def logging(cls, options=None):
        """Logging verbosity level setup"""
        cls.command_sub = 'logging'
        return cls.execute(cls._construct_command(options), output_format='csv')
