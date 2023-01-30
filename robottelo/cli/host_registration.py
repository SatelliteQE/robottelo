"""
Usage:
    hammer host-registration [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    Subcommand
 [ARG] ...                     Subcommand arguments

Subcommands:
 generate-command              Generate global registration command

Options:
 -h, --help                    Print help

"""
from robottelo.cli.base import Base


class HostRegistration(Base):
    """Manipulates hammer host-registration command"""

    command_base = 'host-registration'

    @classmethod
    def generate_command(cls, options):
        """Generate global registration command"""
        cls.command_sub = 'generate-command'
        return cls.execute(cls._construct_command(options))
