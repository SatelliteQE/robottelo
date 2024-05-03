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
        return super().info(options=options, output_format='json')

    @classmethod
    def add_matcher(cls, options=None):
        """Create a matcher for a specific smart class parameter

        Usage::

            hammer sc-param add-matcher [OPTIONS]

        Options::

            --location[-id|-title]        Name/Title/Id of associated location
            --match MATCH                 Override match
            --omit OMIT                   Satellite will not send this parameter in
                                          classificationoutput
                                          One of true/false, yes/no, 1/0.
            --organization[-id|-title]    Name/Title/Id of associated organization
            --puppet-class[-id]           Name/Id of associated puppetclass
            --smart-class-parameter[-id]  Name/Id of associated smart class parameter
            --value VALUE                 Override value, required if omit is false
        """
        cls.command_sub = 'add-matcher'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def remove_matcher(cls, options=None):
        """Delete a matcher for a specific smart class parameter

        Usage::

            hammer sc-param remove-matcher [OPTIONS]

        Options::

            --id ID
            --location[-id|-title]        Name/Title/Id of associated location
            --organization[-id|-title]    Name/Title/Id of associated organization
            --puppet-class[-id]           Name/Id of associated puppetclass
            --smart-class-parameter[-id]  Name/Id of associated smart class parameter
        """
        cls.command_sub = 'remove-matcher'
        return cls.execute(cls._construct_command(options), output_format='csv')
