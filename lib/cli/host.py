#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.cli.base import Base
from lib.common.helpers import csv_to_dictionary


class Host(Base):

    def __init__(self):
        self.command_base = "host"

    def delete_parameter(self, options=None):
        """
        Delete parameter for a host.

        Usage:
        hammer host delete_parameter [OPTIONS]

        Options:
            --hostgroup-id HOSTGROUP_ID   id of the hostgroup the
            parameter is being deleted for
            -h, --help                    print help
            --name NAME                   parameter name

        """

        self.command_sub = "delete_parameter"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def facts(self, options=None):
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
        self.command_sub = "facts"

        result = self.execute(
            self._construct_command(options), expect_csv=True)

        facts = []

        if result.stdout:
            facts = csv_to_dictionary(result.stdout)

        return facts

    def puppet_classes(self, options=None):
        """
        List all puppetclasses.

        Usage:
            hammer host puppet_classes [OPTIONS]

        Options:
            --host-id HOST_ID             id of nested host
            --hostgroup-id HOSTGROUP_ID   id of nested hostgroup
            --environment-id ENVIRONMENT_ID id of nested environment
            --search SEARCH               Filter results
            --order ORDER                 Sort results
            --page PAGE                   paginate results
            --per-page PER_PAGE           number of entries per request
            --id ID                       resource id
            -h, --help                    print help
        """

        self.command_sub = "puppet_classes"

        result = self.execute(self._construct_command(options))

        puppet_classes = []

        if result.stdout:
            puppet_classes = csv_to_dictionary(result.stdout)

        return puppet_classes

    def puppetrun(self, options=None):
        """
        Force a puppet run on the agent.

        Usage:
            hammer host puppetrun [OPTIONS]

        Options:
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        self.command_sub = "puppetrun"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def reboot(self, options=None):
        """
        Reboot a host

        Usage:
            hammer host reboot [OPTIONS]

        Options:
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        self.command_sub = "reboot"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def reports(self, options=None):
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

        self.command_sub = "reports"

        result = self.execute(
            self._construct_command(options), expect_csv=True)

        reports = []

        if result.stdout:
            reports = csv_to_dictionary(result.stdout)

        return reports

    def sc_params(self, options=None):
        """
        List all smart class parameters

        Usage:
            hammer host sc_params [OPTIONS]

        Options:
            --search SEARCH               Filter results
            --order ORDER                 sort results
            --page PAGE                   paginate results
            --per-page PER_PAGE           number of entries per request
            --id, --name HOSTGROUP_ID     hostgroup id/name
            -h, --help                    print help
        """

        self.command_sub = "sc_params"

        result = self.execute(self._construct_command(options))

        parameters = []

        if result.stdout:
            parameters = csv_to_dictionary(result.stdout)

        return parameters

    def set_parameter(self, options=None):
        """
        Create or update parameter for a hostgroup.

        Usage:
            hammer hostgroup set_parameter [OPTIONS]

        Options:
            --hostgroup-id HOSTGROUP_ID   id of the hostgroup
                the parameter is being set for
            -h, --help                    print help
            --name NAME                   parameter name
            --value VALUE                 parameter value
        """

        self.command_sub = "set_parameter"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def start(self, options=None):
        """
        Power a host on

        Usage:
            hammer host start [OPTIONS]

        Options:
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        self.command_sub = "stop"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def status(self, options=None):
        """
        Get status of host

        Usage:
            hammer host start [OPTIONS]

        Options:
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        self.command_sub = "status"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True

    def stop(self, options=None):
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

        self.command_sub = "stop"

        result = self.execute(self._construct_command(options))

        return False if result.stderr else True
