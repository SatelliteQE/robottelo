"""
Usage:
    satellite-maintain service [OPTIONS] SUBCOMMAND [ARG] ...

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
    """Manipulates Satellite-maintain's service command"""

    command_base = 'service'

    @classmethod
    def start(cls, options=None, env_var=None):
        """Build satellite-maintain service start"""
        cls.command_sub = 'start'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def stop(cls, options=None, env_var=None):
        """Build satellite-maintain service stop"""
        cls.command_sub = 'stop'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def restart(cls, options=None, env_var=None):
        """Build satellite-maintain service"""
        cls.command_sub = 'restart'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def status(cls, options=None, env_var=None):
        """Build satellite-maintain service status"""
        cls.command_sub = 'status'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def enable(cls, options=None, env_var=None):
        """Build satellite-maintain service enable"""
        cls.command_sub = 'enable'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def disable(cls, options=None, env_var=None):
        """Build satellite-maintain service disable"""
        cls.command_sub = 'disable'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def list(cls, options=None, env_var=None):
        """Build satellite-maintain service list"""
        cls.command_sub = 'list'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)
