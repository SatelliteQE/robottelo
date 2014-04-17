# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer lifecycle-environment [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    list                          List environments in an organization
    update                        Update an environment
    create                        Create an environment
    delete                        Destroy an environment
    info                          Show an environment
"""

from robottelo.cli.base import Base


class LifecycleEnvironment(Base):
    """
    Manipulates Katello engine's lifecycle-environment command.
    """

    command_base = "lifecycle-environment"
    command_requires_org = True

    @classmethod
    def list(cls, options=None, per_page=False):
        result = super(LifecycleEnvironment, cls).list(
            options, per_page=per_page)

        return result
