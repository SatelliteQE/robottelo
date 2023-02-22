"""
Usage::

    hammer simple-content-access [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    disable                       Disable simple content access for a manifest
    enable                        Enable simple content access for a manifest
    status                        Check if the specified organization has
                                  Simple Content Access enabled

"""
from robottelo.cli.base import Base


class SimpleContentAccess(Base):
    """
    Manipulates Katello engine's simple-content-access command.
    """

    command_base = 'simple-content-access'

    @classmethod
    def disable(cls, options=None, timeout=None):
        """Disable simple content access for a manifest"""
        cls.command_sub = 'disable'
        return cls.execute(cls._construct_command(options), ignore_stderr=True, timeout=timeout)

    @classmethod
    def enable(cls, options=None, timeout=None):
        """Enable simple content access for a manifest"""
        cls.command_sub = 'enable'
        return cls.execute(cls._construct_command(options), ignore_stderr=True, timeout=timeout)

    @classmethod
    def status(cls, options=None, timeout=None):
        """Check if the specified organization has Simple Content Access enabled"""
        cls.command_sub = 'status'
        return cls.execute(cls._construct_command(options), ignore_stderr=True, timeout=timeout)
