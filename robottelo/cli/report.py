"""
Usage::

    hammer config-report [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    delete                        Delete report.
    info                          Show info for report.
    list                          List reports.

"""
from robottelo.cli.base import Base


class ConfigReport(Base):
    """
    Manipulates Foreman's config reports.
    """

    command_base = 'config-report'
