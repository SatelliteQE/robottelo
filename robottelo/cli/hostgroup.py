# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer hostgroup [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    set_parameter                 Create or update parameter for a hostgroup.
    create                        Create an hostgroup.
    puppet_classes                List all puppetclasses.
    info                          Show a hostgroup.
    list                          List all hostgroups.
    update                        Update an hostgroup.
    sc_params                     List all smart class parameters
    delete                        Delete an hostgroup.
    delete_parameter              Delete parameter for a hostgroup.
"""

from robottelo.cli.base import Base


class HostGroup(Base):
    """
    Manipulates Foreman's hostgroups.
    """

    command_base = "hostgroup"
