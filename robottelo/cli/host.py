# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Usage:
    hammer host [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    set_parameter                 Create or update parameter for a host.
    puppet_classes                List all puppetclasses.
    create                        Create a host.
    info                          Show a host.
    stop                          Power a host off
    reports                       List all reports.
    facts                         List all fact values.
    list                          List all hosts.
    status
    update                        Update a host.
    puppetrun                     Force a puppet run on the agent.
    reboot                        Reboot a host
    sc_params                     List all smart class parameters
    start                         Power a host on
    delete                        Delete an host.
    delete_parameter              Delete parameter for a host.
"""

from robottelo.cli.base import Base


class Host(Base):
    """
    Manipulates Foreman's hosts.
    """

    command_base = "host"

    @classmethod
    def facts(cls, options=None):
        """
        List all fact values.

        Usage:
            hammer host facts [OPTIONS]

        Options:
            --search SEARCH               filter results
            --order ORDER                 sort results
            --page PAGE                   paginate results
            --per-page PER_PAGE           number of entries per request
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """
        cls.command_sub = "facts"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        facts = []

        if result.stdout:
            facts = result.stdout

        return facts

    @classmethod
    def puppetrun(cls, options=None):
        """
        Force a puppet run on the agent.

        Usage:
            hammer host puppetrun [OPTIONS]

        Options:
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        cls.command_sub = "puppetrun"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def reboot(cls, options=None):
        """
        Reboot a host

        Usage:
            hammer host reboot [OPTIONS]

        Options:
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        cls.command_sub = "reboot"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def reports(cls, options=None):
        """
        List all reports.

        Usage:
            hammer host reports [OPTIONS]

        Options:
            --order ORDER                 sort results
            --page PAGE                   paginate results
            --per-page PER_PAGE           number of entries per request
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        cls.command_sub = "reports"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        reports = []

        if result.stdout:
            reports = result.stdout

        return reports

    @classmethod
    def start(cls, options=None):
        """
        Power a host on

        Usage:
            hammer host start [OPTIONS]

        Options:
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        cls.command_sub = "stop"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def status(cls, options=None):
        """
        Get status of host

        Usage:
            hammer host start [OPTIONS]

        Options:
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        cls.command_sub = "status"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def stop(cls, options=None):
        """
        Power a host off

        Usage:
            hammer host stop [OPTIONS]

        Options:
            --force                       Force turning off a host
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        cls.command_sub = "stop"

        result = cls.execute(cls._construct_command(options))

        return result
