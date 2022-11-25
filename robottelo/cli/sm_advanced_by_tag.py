"""
Usage:
    satellite-maintain advanced procedure by-tag [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    backup                        Run procedures tagged #backup
    maintenance-mode-off          Run procedures tagged #maintenance_mode_off
    maintenance-mode-on           Run procedures tagged #maintenance_mode_on
    post-migrations               Run procedures tagged #post_migrations
    pre-migrations                Run procedures tagged #pre_migrations
    restore                       Run procedures tagged #restore

Options:
    -h, --help                    print help
"""
from robottelo.cli.base import Base


class AdvancedByTag(Base):
    """Manipulates Satellite-maintain's advanced procedure by-tag command"""

    command_base = 'advanced procedure by-tag'

    @classmethod
    def post_migrations(cls, options=None):
        """Build satellite-maintain advanced procedure by-tag post-migrations"""
        cls.command_sub = 'post-migrations'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def pre_migrations(cls, options=None):
        """Build satellite-maintain advanced procedure by-tag pre-migrations"""
        cls.command_sub = 'pre-migrations'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def restore(cls, options=None):
        """Build satellite-maintain advanced procedure by-tag restore"""
        cls.command_sub = 'restore'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))
