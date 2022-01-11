"""
Usage:
    foreman-maintain health [OPTIONS] SUBCOMMAND [ARG] ...

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
    """Manipulates Foreman-maintain's health command"""

    command_base = 'health'

    @classmethod
    def check(cls, options=None):
        """Build foreman-maintain health check"""
        cls.command_sub = 'check'
        options = options or {}
        return cls.fm_execute(cls._construct_command(options))

    @classmethod
    def list(cls, options=None):
        """Build foreman-maintain health list"""
        cls.command_sub = 'list'
        options = options or {}
        return cls.fm_execute(cls._construct_command(options))

    @classmethod
    def list_tags(cls, options=None):
        """Build foreman-maintain health list-tags"""
        cls.command_sub = 'list-tags'
        options = options or {}
        return cls.fm_execute(cls._construct_command(options))
