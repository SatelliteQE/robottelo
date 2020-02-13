# -*- encoding: utf-8 -*-
"""
Usage::

    hammer smart-variable [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add-override-value            Create an override value for a specific smart
                                  variable
    create                        Create a smart variable
    delete                        Delete a smart variable
    info                          Show a smart variable
    list                          List all smart variables
    remove-override-value         Delete an override value for a specific smart
                                  variable
    update                        Update a smart variable
"""
from robottelo.cli.base import Base


class SmartVariable(Base):
    """Manipulates smart variables"""

    command_base = 'smart-variable'

    @classmethod
    def info(cls, options=None):
        """Gets information for smart variables"""
        return super(SmartVariable, cls).info(
            options=options, output_format='json')

    @classmethod
    def add_override_value(cls, options=None):
        """Create an override value for a specific smart variable

        Usage::

            hammer smart-variable add-override-value [OPTIONS]

        Options::

            --match MATCH                                       Override match
            --smart-variable SMART_VARIABLE_NAME                Smart variable
                                                                name
            --smart-variable-id SMART_VARIABLE_ID               ID of smart
                                                                variable
            --use-puppet-default USE_PUPPET_DEFAULT             One of
                                                                true/false,
                                                                yes/no, 1/0.
            --value VALUE                                       Override value
        """
        cls.command_sub = 'add-override-value'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def remove_override_value(cls, options=None):
        """Delete an override value for a specific smart variable

        Usage::

            hammer smart-variable remove-override-value [OPTIONS]

        Options::

            --id ID
            --smart-variable SMART_VARIABLE_NAME                Smart variable
                                                                name
            --smart-variable-id SMART_VARIABLE_ID
        """
        cls.command_sub = 'remove-override-value'
        return cls.execute(
            cls._construct_command(options), output_format='csv')
