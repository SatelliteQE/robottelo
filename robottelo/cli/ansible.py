"""
Usage::
     ansible [OPTIONS] SUBCOMMAND [ARG] ...
Parameters::
     SUBCOMMAND                    Subcommand
     [ARG] ...                     Subcommand arguments
Subcommands::
     roles                         Manage ansible roles
     variables                     Manage ansible variables
"""
from robottelo.cli.base import Base


class Ansible(Base):
    """Manipulates Ansible Variables and roles."""

    command_base = 'ansible'

    @classmethod
    def roles_import(cls, options=None):
        """DEPRECATED - Import ansible roles"""
        cls.command_sub = 'roles import'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def roles_sync(cls, options=None):
        """Sync Ansible roles"""
        cls.command_sub = 'roles sync'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def roles_delete(cls, options=None):
        """Delete Ansible roles"""
        cls.command_sub = 'roles delete'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def variables_import(cls, options=None):
        """Import ansible variables"""
        cls.command_sub = 'variables import'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def roles_list(cls, options=None):
        """List ansible roles"""
        cls.command_sub = 'roles list'
        return cls.execute(cls._construct_command(options), output_format='csv')
