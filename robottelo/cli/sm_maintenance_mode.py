"""
Usage:
    satellite-maintain maintenance-mode [OPTIONS] SUBCOMMAND [ARG] ...
Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments
Subcommands:
    start                         Start maintenance-mode
    stop                          Stop maintenance-mode
    status                        Get maintenance-mode status
    is-enabled                    Get maintenance-mode status code
Options:
    -h, --help                    print help
"""
from robottelo.cli.base import Base


class MaintenanceMode(Base):
    """Manipulates Satellite-maintain's maintenance-mode command"""

    command_base = 'maintenance-mode'

    @classmethod
    def start(cls, options=None):
        """satellite-maintain maintenance-mode start [OPTIONS]"""
        cls.command_sub = 'start'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def stop(cls, options=None):
        """satellite-maintain maintenance-mode stop [OPTIONS]"""
        cls.command_sub = 'stop'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def status(cls, options=None):
        """satellite-maintain maintenance-mode status [OPTIONS]"""
        cls.command_sub = 'status'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))

    @classmethod
    def is_enabled(cls, options=None):
        """satellite-maintain maintenance-mode is-enabled [OPTIONS]"""
        cls.command_sub = 'is-enabled'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options))
