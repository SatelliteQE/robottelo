# -*- encoding: utf-8 -*-
"""
Usage::

    hammer hostgroup [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    ansible-roles                 Manage Ansible roles on a hostgroup
    create                        Create a host group
    delete                        Delete a host group
    delete-parameter              Delete parameter for a hostgroup
    info                          Show a host group
    list                          List all host groups
    puppet-classes                List all Puppet classes
    rebuild-config                Rebuild orchestration config
    sc-params                     List all smart class parameters
    set-parameter                 Create or update parameter for a hostgroup
    update                        Update a host group
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
