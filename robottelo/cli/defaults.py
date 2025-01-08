"""
Usage::

    hammer defaults [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add                           Add a default parameter to config
    delete                        Delete a default param
    list                          List all the default parameters
    providers                     List all the providers
"""

from robottelo.cli.base import Base


class Defaults(Base):
    """Manipulates Defaults entity"""

    command_base = 'defaults'

    @classmethod
    def add(cls, options=None):
        """Add parameter to config
        Usage::

            hammer defaults add [OPTIONS]

        Options::

            --param-name OPTION_NAME      The name of the default option
                                          (e.g. organization_id).
            --param-value OPTION_VALUE    The value for the default option
            --provider OPTION_PROVIDER    The name of the provider providing
                                          the value. For list available
                                          providers see `hammer defaults
                                          providers`.
        """
        cls.command_sub = 'add'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def delete(cls, options=None):
        """Delete parameter from config
        Usage::

            hammer defaults delete [OPTIONS]

        Options::

            --param-name OPTION_NAME      The name of the default option
        """
        cls.command_sub = 'delete'
        return cls.execute(cls._construct_command(options))
