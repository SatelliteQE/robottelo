# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer template [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
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

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)
        self.command_base = "template"

    def kinds(self, options=None):
        """
        Returns list of types of templates.
        """

        self.command_sub = "kinds"

        result = self.execute(self._construct_command(options),
                              expect_csv=True)

        kinds = []

        if result.stdout:
            kinds = result.stdout

        return kinds
