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
from robottelo.exceptions import CLIError


class SyncPlan(Base):
    """Manipulates Katello engine's sync-plan command."""

    command_base = 'sync-plan'

    @classmethod
    def create(cls, options=None, timeout=None):
        """Create a SyncPlan"""
        cls.command_sub = 'create'

        if options.get('interval') == 'custom cron' and options.get('cron-expression') is None:
            raise CLIError('Missing "cron-expression" option for "custom cron" interval.')

        return super().create(options, timeout)
