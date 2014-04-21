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

    @classmethod
    def add_repository(cls, options):
        """
        Associate repository to a selected CV.
        """

        cls.command_sub = "add-repository"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def publish(cls, options):
        """
        Publishes a new version of content-view.
        """

        cls.command_sub = "publish"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def promote(cls, options):
        """
        Promotes a version of content-view to next env.
        """

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def version(cls, sub_task, options):
        """
        Provides version details related to content-view.
        """

        cls.command_sub = "version"
        cls.command_tertiary = sub_task

        if sub_task == "list":
            result = cls.list(options)
        if sub_task == "info":
            result = cls.info(options)
        if sub_task == "promote":
            result = cls.promote(options)

        return result
