"""
Usage:
    foreman-maintain service [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    start                         Start applicable services
    stop                          Stop applicable services
    restart                       Restart applicable services
    status                        Get statuses of applicable services
    list                          List applicable services
    enable                        Enable applicable services
    disable                       Disable applicable services

Options:
    -h, --help                    print help
"""
from robottelo.cli.base import Base


class Service(Base):
    """Manipulates Foreman-maintain's service command"""

    command_base = "service"

    @classmethod
    def service_start(cls, options=None):
        """Build foreman-maintain service start"""
        cls.command_sub = "start"
        if options is None:
            options = {}
        return cls.fm_execute(cls._construct_command(options))

    @classmethod
    def service_stop(cls, options=None):
        """Build foreman-maintain service stop"""
        cls.command_sub = "stop"
        if options is None:
            options = {}
        return cls.fm_execute(cls._construct_command(options))

    @classmethod
    def service_restart(cls, options=None):
        """Build foreman-maintain service"""
        cls.command_sub = "restart"
        if options is None:
            options = {}
        return cls.fm_execute(cls._construct_command(options))

    @classmethod
    def service_status(cls, options=None):
        """Build foreman-maintain service status"""
        cls.command_sub = "status"
        if options is None:
            options = {}
        return cls.fm_execute(cls._construct_command(options))

    @classmethod
    def service_enable(cls, options=None):
        """Build foreman-maintain service enable"""
        cls.command_sub = "enable"
        if options is None:
            options = {}
        return cls.fm_execute(cls._construct_command(options))

    @classmethod
    def service_disable(cls, options=None):
        """Build foreman-maintain service disable"""
        cls.command_sub = "disable"
        if options is None:
            options = {}
        return cls.fm_execute(cls._construct_command(options))

    @classmethod
    def service_list(cls, options=None):
        """Build foreman-maintain service list"""
        cls.command_sub = "list"
        if options is None:
            options = {}
        return cls.fm_execute(cls._construct_command(options))
