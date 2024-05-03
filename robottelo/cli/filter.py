"""
Usage::
     hammer filter [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

 SUBCOMMAND                    subcommand
 [ARG] ...                     subcommand arguments

Subcommands::

 available-permissions         List all permissions
 available-resources           List available resource types.
 create                        Create a filter
 delete                        Delete a filter
 info                          Show a filter
 list                          List all filters
 update                        Update a filter
"""

from robottelo.cli.base import Base


class Filter(Base):
    """Manipulates Katello's filter command."""

    command_base = 'filter'

    @classmethod
    def available_permissions(cls, options=None):
        cls.command_sub = 'available-permissions'
        return cls.execute(cls._construct_command(options), output_format='csv')
