# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage::

    hammer template [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    remove_operatingsystem        Disassociate a resource
    kinds                         List available config template kinds.
    dump                          View config template content.
    create                        Create a template
    add_operatingsystem           Associate a resource
    info                          Show template details
    list                          List templates
    update                        Update a template
    delete                        Delete a template
"""

from robottelo.cli.base import Base


class Template(Base):
    """
    Manipulates Foreman's configuration templates.
    """

    command_base = "template"

    @classmethod
    def kinds(cls, options=None):
        """
        Returns list of types of templates.
        """

        cls.command_sub = "kinds"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        kinds = []

        if result.stdout:
            kinds = result.stdout

        return kinds

    @classmethod
    def add_operatingsystem(cls, options=None):
        """
        Adds operating system, requires "id" and "operatingsystem-id".
        """

        cls.command_sub = "add-operatingsystem"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def remove_operatingsystem(cls, options=None):
        """
        Remove operating system, requires "id" and "operatingsystem-id".
        """

        cls.command_sub = "remove-operatingsystem"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result
