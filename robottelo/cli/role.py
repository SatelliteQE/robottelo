"""Usage::

    hammer role [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    clone                         Clone a role
    create                        Create an role.
    delete                        Delete an role.
    filters                       List all filters.
    info                          Show a role
    list                          List all roles.
    update                        Update an role.
"""

from robottelo.cli.base import Base


class Role(Base):
    """Manipulates Katello engine's role command."""

    command_base = 'role'

    @classmethod
    def filters(cls, options=None):
        """List all filters"""
        cls.command_sub = 'filters'
        return cls.execute(cls._construct_command(options), output_format='json')

    @classmethod
    def clone(cls, options):
        """Clone a role"""
        cls.command_sub = 'clone'
        result = cls.execute(cls._construct_command(options), output_format='csv')
        # Fetch new role
        if len(result) > 0 and 'id' in result[0]:
            new_role = cls.info({'id': result[0]['id']})
            if len(new_role) > 0:
                result = new_role
        return result
