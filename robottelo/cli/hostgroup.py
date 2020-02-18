# -*- encoding: utf-8 -*-
"""
Usage::

    hammer hostgroup [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create an hostgroup.
    delete                        Delete an hostgroup.
    delete_parameter              Delete parameter for a hostgroup.
    info                          Show a hostgroup.
    list                          List all hostgroups.
    puppet_classes                List all puppetclasses.
    sc_params                     List all smart class parameters
    set_parameter                 Create or update parameter for a hostgroup.
    smart-variables               List all smart variables
    update                        Update an hostgroup.
"""
from robottelo.cli.base import Base


class HostGroup(Base):
    """Manipulates Foreman's hostgroups."""

    command_base = 'hostgroup'

    @classmethod
    def sc_params(cls, options=None):
        """List all smart class parameters

        Usage::

            hammer hostgroup sc-params [OPTIONS]

        Options::

            --hostgroup HOSTGROUP_NAME        Hostgroup name
            --hostgroup-id HOSTGROUP_ID
            --hostgroup-title HOSTGROUP_TITLE Hostgroup title
            --order ORDER                     sort results
            --page PAGE                       paginate results
            --per-page PER_PAGE               number of entries per request
            --search SEARCH                   filter results
        """
        cls.command_sub = 'sc-params'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def smart_variables(cls, options=None):
        """List all smart variables

        Usage::

            hammer hostgroup smart-variables [OPTIONS]

        Options::

            --hostgroup HOSTGROUP_NAME        Hostgroup name
            --hostgroup-id HOSTGROUP_ID
            --hostgroup-title HOSTGROUP_TITLE Hostgroup title
            --order ORDER                     sort results
            --page PAGE                       paginate results
            --per-page PER_PAGE               number of entries per request
            --search SEARCH                   filter results
        """
        cls.command_sub = 'smart-variables'
        return cls.execute(cls._construct_command(options), output_format='csv')
