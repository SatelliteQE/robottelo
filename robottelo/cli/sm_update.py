"""
Usage:
    satellite-maintain update [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND    subcommand
    [ARG] ...     subcommand arguments

Subcommands:
    check         Run pre-update checks before updating
    run           Run an update

Options:
    -h, --help    print help
"""

from robottelo.cli.base import Base


class Update(Base):
    """Manipulates Satellite-maintain's update command"""

    command_base = 'update'

    @classmethod
    def check(cls, options=None, env_var=None):
        """Build satellite-maintain update check"""
        cls.command_sub = 'check'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def run(cls, options=None, env_var=None):
        """Build satellite-maintain update run"""
        cls.command_sub = 'run'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)
