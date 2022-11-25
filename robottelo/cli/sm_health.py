"""
Usage:
    satellite-maintain health [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    list                          List the checks based on criteria
    list-tags                     List the tags to use for filtering checks
    check                         Run the health checks against the system

Options:
    -h, --help                    print help
"""
from robottelo.cli.base import Base


class Health(Base):
    """Manipulates Satellite-maintain's health command"""

    command_base = 'health'

    @classmethod
    def check(cls, options=None, env_var=None):
        """Build satellite-maintain health check"""
        cls.command_sub = 'check'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def list(cls, options=None, env_var=None):
        """Build satellite-maintain health list"""
        cls.command_sub = 'list'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def list_tags(cls, options=None, env_var=None):
        """Build satellite-maintain health list-tags"""
        cls.command_sub = 'list-tags'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)
