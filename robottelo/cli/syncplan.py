# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage::

    hammer sync-plan [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a sync plan
    delete                        Destroy a sync plan
    info                          Show a sync plan
    list                          List sync plans
    update
"""

from robottelo.cli.base import Base


class SyncPlan(Base):
    """
    Manipulates Katello engine's sync-plan command.
    """

    command_base = "sync-plan"
    command_requires_org = True

    @classmethod
    def create(cls, options=None):
        cls.command_requires_org = False

        try:
            result = super(SyncPlan, cls).create(options)
        finally:
            cls.command_requires_org = True

        return result

    @classmethod
    def info(cls, options=None):
        cls.command_requires_org = False

        try:
            result = super(SyncPlan, cls).info(options)
        finally:
            cls.command_requires_org = True

        return result
