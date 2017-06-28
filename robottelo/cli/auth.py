# -*- encoding: utf-8 -*-
"""
Usage::
    hammer auth [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::
    login                         Set credentials
    logout                        Wipe your credentials
    status                        Information about current connections
"""

from robottelo.cli.base import Base


class Auth(Base):
    """ Authenticates Foreman users """

    command_base = 'auth'

    @classmethod
    def login(cls, options=None):
        """Set credentials"""
        cls.command_sub = 'login'
        return cls.execute(
            cls._construct_command(options), output_format='csv',
            pass_credentials=False)

    @classmethod
    def logout(cls, options=None):
        """Wipe credentials"""
        cls.command_sub = 'logout'
        return cls.execute(
            cls._construct_command(options), output_format='csv',
            pass_credentials=False)

    @classmethod
    def status(cls, options=None):
        """Show login status"""
        cls.command_sub = 'status'
        return cls.execute(
            cls._construct_command(options), output_format='csv',
            pass_credentials=False)
