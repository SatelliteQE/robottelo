"""
Usage::

    hammer puppet-class [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    info                          Show a puppetclass
    list                          List all puppetclasses.
    sc-params                     List all smart class parameters
"""

from robottelo.cli.base import Base


class Puppet(Base):
    """
    Search Foreman's puppet modules.
    """

    command_base = 'puppet-class'

    @classmethod
    def sc_params(cls, options=None):
        """
        Usage:
            hammer puppet-class sc-params [OPTIONS]

        Options:
             --order ORDER                      sort results
             --page PAGE                        paginate results
             --per-page PER_PAGE                number of entries per request
             --puppet-class PUPPET_CLASS_NAME   Puppet class name
             --puppet-class-id PUPPET_CLASS_ID  ID of Puppet class
             --search SEARCH                    filter results
        """
        cls.command_sub = 'sc-params'
        return cls.execute(cls._construct_command(options), output_format='csv')
