# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer report [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    info                          Show info for report.
    list                          List reports.
    delete                        Delete report.

"""

from robottelo.cli.base import Base


class Report(Base):
    """
    Manipulates Foreman's reports.
    """

    command_base = "report"
