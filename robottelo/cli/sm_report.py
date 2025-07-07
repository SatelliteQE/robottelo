"""
Usage:
    satellite-maintain report [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND       subcommand
    [ARG] ...        subcommand arguments

Subcommands:
    generate         Generates the usage reports

Options:
    --output FILE    Output the generate report into FILE
    -h, --help       print help

"""

from robottelo.cli.base import Base


class SatelliteMaintainReport(Base):
    """Manipulates Satellite-maintain's report command"""

    command_base = 'report'

    @classmethod
    def generate(cls, options=None, env_var=None):
        """Build satellite-maintain report generate"""
        cls.command_sub = 'generate'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)
