-*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""
# hammer report --help
Usage:
    hammer report [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    info                          Show a report.
    list                          List all reports.
    delete                        Delete a report.

Options:
    -h, --help                    print help
"""
from robottelo.cli.base import Base

class Report(Base):
      """
          Report puppet info
      """
      def __init__(self):
          """
                Sets the base command for class.
          """
          Base.__init__(self)

          self.command_base = "report"