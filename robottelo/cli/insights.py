"""
Usage:
    hammer insights [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    Subcommand
 [ARG] ...                     Subcommand arguments

Subcommands:
 cloud-connector               Manage cloud connector setup
 inventory                     Manage inventory related operations

Options:
 -h, --help                    Print help

"""

from robottelo.cli.base import Base


class Insights(Base):
    """
    Exports content from satellite
    """

    command_base = 'insights'
    command_requires_org = True

    @classmethod
    def inventory_sync(cls, options):
        """
        Start inventory status sync
        """
        cls.command_sub = 'inventory sync'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def inventory_generate_report(cls, options):
        """
        Start new report generation
        """
        cls.command_sub = 'inventory generate-report'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def inventory_download_report(cls, options):
        """
        Download the last generated report
        """
        cls.command_sub = 'inventory download-report'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def cloud_connector_enable(cls, options=None):
        """
        Enable cloud connector
        """
        cls.command_sub = 'cloud-connector enable'
        return cls.execute(cls._construct_command(options))
