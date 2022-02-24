"""
Usage::

    hammer environment [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create an environment
    delete                        Delete an environment
    info                          Show an environment
    list                          List all environments
    sc-params                     List all smart class parameters
    update                        Update an environment
"""
from robottelo.cli.base import Base


class Environment(Base):
    """Manipulates Foreman's environments."""

    command_base = 'puppet-environment'

    @classmethod
    def sc_params(cls, options=None):
        """List all smart class parameters."""
        cls.command_sub = 'sc-params'
        return cls.execute(cls._construct_command(options), output_format='json')
