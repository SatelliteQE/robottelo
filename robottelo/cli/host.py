# -*- encoding: utf-8 -*-
"""
Usage::

    hammer host [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a host
    delete                        Delete a host
    delete-parameter              Delete parameter for a host.
    facts                         List all fact values
    info                          Show a host
    list                          List all hosts
    puppet-classes                List all Puppet classes
    puppetrun                     Force a Puppet agent run on the host
    reboot                        Reboot a host
    reports                       List all reports
    sc-params                     List all smart class parameters
    set-parameter                 Create or update parameter for a host.
    start                         Power a host on
    status                        Get status of host
    stop                          Power a host off
    update                        Update a host

"""

from robottelo.cli.base import Base


class Host(Base):
    """
    Manipulates Foreman's hosts.
    """

    command_base = 'host'

    @classmethod
    def facts(cls, options=None):
        """
        List all fact values.

        Usage:
            hammer host facts [OPTIONS]

        Options:
            --id ID                       resource id
            --name NAME                   resource name
            --order ORDER                 sort results
            --page PAGE                   paginate results
            --per-page PER_PAGE           number of entries per request
            --search SEARCH               filter results
            -h, --help                    print help
        """
        cls.command_sub = 'facts'

        result = cls.execute(
            cls._construct_command(options), output_format='csv')

        facts = []

        if result:
            facts = result

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

        cls.command_sub = 'puppetrun'

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

        cls.command_sub = 'reboot'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def reports(cls, options=None):
        """
        List all reports.

        Usage:
            hammer host reports [OPTIONS]

        Options:
            --id ID                       resource id
            --name NAME                   resource name
            --order ORDER                 sort results
            --page PAGE                   paginate results
            --per-page PER_PAGE           number of entries per request
            --search SEARCH               filter results
            -h, --help                    print help
        """

        cls.command_sub = 'reports'

        result = cls.execute(
            cls._construct_command(options), output_format='csv')

        reports = []

        if result:
            reports = result

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

        cls.command_sub = 'start'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def status(cls, options=None):
        """
        Get status of host

        Usage:
            hammer host status [OPTIONS]

        Options:
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        cls.command_sub = 'status'

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

        cls.command_sub = 'stop'

        result = cls.execute(cls._construct_command(options))

        return result
