"""
Usage:
    hammer srpm [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    Subcommand
 [ARG] ...                     Subcommand arguments

Subcommands:
 info                          Show a SRPM Details
 list                          List srpms
"""
from robottelo.cli.base import Base


class Srpm(Base):
    """
    Manipulates Katello engine's srpm command.
    """

    command_base = 'srpm'

    @classmethod
    def info(cls, options=None):
        """Show a SRPM Info"""
        cls.command_sub = 'info'

        result = cls.execute(cls._construct_command(options), output_format='csv')

        return result

    @classmethod
    def list(cls, options=None):
        """List SRPMs"""
        cls.command_sub = 'list'

        result = cls.execute(cls._construct_command(options), output_format='csv')

        return result
