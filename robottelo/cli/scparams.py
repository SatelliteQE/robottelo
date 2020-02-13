# -*- encoding: utf-8 -*-
"""
Usage::

    hammer sc-param [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add-override-value            Create an override value for a specific smart
                                  variable
    info                          Show a smart class parameter
    list                          List all smart class parameters
    remove-override-value         Delete an override value for a specific smart
                                  variable
    update                        Update a smart class parameter
"""
from robottelo.cli.base import Base


class SmartClassParameter(Base):
    """Manipulates smart class parameters"""

    command_base = 'sc-param'

    @classmethod
    def info(cls, options=None):
        """Gets information for smart class parameter"""
        return super(SmartClassParameter, cls).info(
            options=options, output_format='json')

    @classmethod
    def add_override_value(cls, options=None):
        """Create an override value for a specific smart class parameter

        Usage::

            hammer sc-param add-override-value [OPTIONS]

        Options::

            --match MATCH                                       Override match
            --puppet-class PUPPET_CLASS_NAME                    Puppet class
                                                                name
            --puppet-class-id PUPPET_CLASS_ID                   ID of Puppet
                                                                class
            --smart-class-parameter SMART_CLASS_PARAMETER_NAME  Smart class
                                                                parameter name
            --smart-class-parameter-id SMART_CLASS_PARAMETER_ID
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
        """Delete an override value for a specific smart class parameter

        Usage::

            hammer sc-param remove-override-value [OPTIONS]

        Options::

            --id ID
            --puppet-class PUPPET_CLASS_NAME                    Puppet class
                                                                name
            --puppet-class-id PUPPET_CLASS_ID                   ID of Puppet
                                                                class
            --smart-class-parameter SMART_CLASS_PARAMETER_NAME  Smart class
                                                                parameter name
            --smart-class-parameter-id SMART_CLASS_PARAMETER_ID
        """
        cls.command_sub = 'remove-override-value'
        return cls.execute(
            cls._construct_command(options), output_format='csv')
