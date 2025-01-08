"""
Usage::

    hammer discovery [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    auto-provision                Auto provision a host
    delete                        Delete a discovered host
    facts                         Show a discovered host
    info                          Show a discovered host
    list                          List all discovered hosts
    provision                     Provision a discovered host
    reboot                        Reboot a host
    refresh-facts                 Refresh the facts of a host
"""

from robottelo.cli.base import Base


class DiscoveredHost(Base):
    """Manipulates Discovery Hosts"""

    command_base = 'discovery'

    @classmethod
    def provision(cls, options=None):
        """Manually provision discovered host"""
        cls.command_sub = 'provision'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def facts(cls, options=None):
        """Get all the facts associated with discovered host"""
        cls.command_sub = 'facts'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def auto_provision(cls, options=None):
        """Auto provision discovered host"""
        cls.command_sub = 'auto-provision'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def reboot(cls, options=None):
        """Reboot discovered host"""
        cls.command_sub = 'reboot'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def refresh_facts(cls, options=None):
        """Refresh facts associated with discovered host"""
        cls.command_sub = 'refresh-facts'
        return cls.execute(cls._construct_command(options), output_format='csv')
