"""
Usage:
    satellite-maintain packages [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    lock                          Prevent packages from automatic update
    unlock                        Enable packages for automatic update
    status                        Check if packages are protected against update
    check-update                  Check for available package updates
    install                       Install packages in an unlocked session
    update                        Update packages in an unlocked session
    is-locked                     Check if update of packages is allowed

Options:
    -h, --help                    print help
"""
from robottelo.cli.base import Base


class Packages(Base):
    """Manipulates Satellite-maintain's packages command"""

    command_base = 'packages'

    @classmethod
    def lock(cls, options=None):
        """Build satellite-maintain packages lock"""
        cls.command_sub = 'lock'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def unlock(cls, options=None):
        """Build satellite-maintain packages unlock"""
        cls.command_sub = 'unlock'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def is_locked(cls, options=None):
        """Build satellite-maintain packages is-locked"""
        cls.command_sub = 'is-locked'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def status(cls, options=None):
        """Build satellite-maintain packages status"""
        cls.command_sub = 'status'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def install(cls, packages='', options=None):
        """Build satellite-maintain packages install"""
        cls.command_sub = 'install'
        cls.command_end = packages
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def update(cls, packages='', options=None):
        """Build satellite-maintain packages update"""
        cls.command_sub = 'update'
        cls.command_end = packages
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def check_update(cls, options=None):
        """Build satellite-maintain packages check-update"""
        cls.command_sub = 'check-update'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))
