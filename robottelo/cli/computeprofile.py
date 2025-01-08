"""
Usage:
    hammer compute-profile [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    Subcommand
 [ARG] ...                     Subcommand arguments

Subcommands:
 create                        Create a compute profile
 delete                        Delete a compute profile
 info                          Show a compute profile
 list                          List of compute profiles
 update                        Update a compute profile
 values                        Create update and delete Compute profile values

Options:
 -h, --help                    Print help
                      Update a compute resource.
"""

from robottelo.cli.base import Base


class ComputeProfile(Base):
    """
    Manipulates Foreman's compute-profile.
    """

    command_base = 'compute-profile'

    @classmethod
    def values_create(cls, options=None):
        """Create Compute profile values"""
        cls.command_sub = 'values create'
        return cls.execute(cls._construct_command(options), output_format='csv')
