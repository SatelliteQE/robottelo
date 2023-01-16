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
    """Authenticates Foreman users"""

    command_base = 'auth'

    @classmethod
    def login(cls, options=None):
        """Set credentials"""
        cls.command_sub = 'login'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def logout(cls, options=None):
        """Wipe credentials"""
        cls.command_sub = 'logout'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def status(cls, options=None):
        """Show login status"""
        cls.command_sub = 'status'
        return cls.execute(cls._construct_command(options), output_format='csv')


class AuthLogin(Base):
    """Auth Login for Foreman CLI"""

    command_base = 'auth login'

    @classmethod
    def basic(cls, options=None):
        """Provide username and password"""
        cls.command_sub = 'basic'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def oauth(cls, options=None):
        """Supports for both with/without 2fa"""
        cls.command_sub = 'oauth'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def negotiate(cls, options=None):
        """Kerberos ticket based auth"""
        cls.command_sub = 'negotiate'
        return cls.execute(cls._construct_command(options), output_format='csv')
