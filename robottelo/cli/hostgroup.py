# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

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
    update                        Update an hostgroup.
"""

from robottelo.cli.base import Base


class HostGroup(Base):
    """
    Manipulates Foreman's hostgroups.
    """

    command_base = 'hostgroup'
