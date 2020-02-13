# -*- encoding: utf-8 -*-
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
    """Manipulates Katello engine's sync-plan command."""
    command_base = 'sync-plan'
