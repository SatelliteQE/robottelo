# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer sync-plan [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
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

    def __init__(self):
        """
        Sets the base command for class.
        """
        Base.__init__(self)

    @classmethod
    def info(cls, organization_id, options=None):
        """
        Displays information for sync plan
        """

        cls.command_sub = "info"

        if options is None:
            options = {}

        # Katello subcommands require the organization-id
        options['organization-id'] = organization_id

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def list(cls, organization_id, options=None):
        """
        Lists available sync plans.
        """

        cls.command_sub = "list"

        if options is None:
            options = {}
            options['per-page'] = 10000

        # Katello subcommands require the organization-id
        options['organization-id'] = organization_id

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result
