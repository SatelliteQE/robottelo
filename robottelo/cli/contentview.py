# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer content-view [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    add-repository                Associate a resource
    add-version                   Associate a resource
    create                        Create a content view
    filter                        View and manage filters
    info                          Show a content view
    list                          List content views
    publish                       Publish a content view
    puppet-module                 View and manage puppet modules
    remove-from-environment       Remove a content view from an environment
    remove-repository             Disassociate a resource
    remove-version                Disassociate a resource
    update                        Update a content view
    version                       View and manage content view versions

Options:
    -h, --help                    print help
"""

from robottelo.cli.base import Base


class ContentView(Base):
    """
    Manipulates Foreman's content view.
    """

    command_base = "content-view"
