# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer domain [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    set_parameter                 Create or update parameter for a domain.
    create                        Create a domain.
    info                          Show a domain.
    list                          List of domains
    update                        Update a domain.
    delete                        Delete a domain.
    delete_parameter              Delete parameter for a domain.
"""

from robottelo.cli.base import Base


class Domain(Base):
    """
    Manipulates Foreman's domains.
    """

    command_base = "domain"
