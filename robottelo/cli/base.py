#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Generic base class for cli hammer commands
"""

import logging

from robottelo.common import conf, ssh


class Base(object):
    """
    @param command_base: base command of hammer.
    Output of recent: `hammer --help`
        shell                         Interactive Shell
        architecture                  Manipulate Foreman's architectures.
        global_parameter              Manipulate Foreman's global parameters.
        compute_resource              Manipulate Foreman's compute resources.
        domain                        Manipulate Foreman's domains.
        environment                   Manipulate Foreman's environments.
        fact                          Search Foreman's facts.
        report                        Browse and read reports.
        puppet_class                  Browse and read reports.
        host                          Manipulate Foreman's hosts.
        hostgroup                     Manipulate Foreman's hostgroups.
        location                      Manipulate Foreman's locations.
        medium                        Manipulate Foreman's installation media.
        model                         Manipulate Foreman's hardware models.
        os                            Manipulate Foreman's operating system.
        organization                  Manipulate Foreman's organizations.
        partition_table               Manipulate Foreman's partition tables.
        proxy                         Manipulate Foreman's smart proxies.
        subnet                        Manipulate Foreman's subnets.
        template                      Manipulate Foreman's config templates.
        user                          Manipulate Foreman's users.
    @since: 27.Nov.2013
    """
    command_base = None  # each inherited instance should define this
    command_sub = None  # specific to instance, like: create, update, etc

    logger = logging.getLogger("robottelo")

    locale = conf.properties['main.locale']
    katello_user = conf.properties['foreman.admin.username']
    katello_passwd = conf.properties['foreman.admin.password']

    def __init__(self):
        pass

    def add_operating_system(self, options=None):
        """
        Adds OS to record.
        """

        self.command_sub = "add_operatingsystem"

        result = self.execute(self._construct_command(options))

        return result

    def create(self, options=None):
        """
        Creates a new record using the arguments passed via dictionary.
        """

        self.command_sub = "create"

        result = self.execute(self._construct_command(options))

        return result

    def delete(self, options=None):
        """
        Deletes existing record.
        """

        self.command_sub = "delete"

        result = self.execute(self._construct_command(options))

        return result

    def delete_parameter(self, options=None):
        """
        Deletes parameter from record.
        """

        self.command_sub = "delete_parameter"

        result = self.execute(self._construct_command(options))

        return result

    def dump(self, options=None):
        """
        Displays the content for existing partition table.
        """

        self.command_sub = "dump"

        result = self.execute(self._construct_command(options))

        return result

    def execute(self, command, user=None, password=None, expect_csv=False):
        """
        Executes the command
        """
        if user is None:
            user = self.katello_user
        if password is None:
            password = self.katello_passwd

        output_csv = ""
        if expect_csv:
            output_csv = " --output csv"
        shell_cmd = "LANG=%s hammer -v -u %s -p %s" + output_csv + " %s"
        cmd = shell_cmd % (self.locale, user, password, command)

        return ssh.command(cmd, expect_csv=expect_csv)

    def exists(self, tuple_search=None):
        """
        Search for record by given: ('name', '<search_value>')
        @return: CSV parsed structure[0] of the list.
        """
        if tuple_search:
            options = {"search": "%s=\"%s\"" %
                       (tuple_search[0], tuple_search[1])}

        result_list = self.list(options)

        if result_list.stdout:
            result = result_list.stdout[0]
        else:
            result = []

        return result

    def info(self, options=None):
        """
        Gets information by provided: options dictionary.
        @param options: ID (sometimes name or id).
        """
        self.command_sub = "info"

        result = self.execute(self._construct_command(options),
                              expect_csv=True)

        if len(result.stdout) == 1:
            result.stdout = result.stdout[0]
        # This should never happen but we're trying to be safe
        elif len(result.stdout) > 1:
            raise Exception("Info subcommand returned more than 1 result.")

        return result

    def list(self, options=None):
        """
        List information.
        @param options: ID (sometimes name works as well) to retrieve info.
        """
        self.command_sub = "list"
        if options is None:
            options = {}
            options['per-page'] = 10000

        result = self.execute(self._construct_command(options),
                              expect_csv=True)

        return result

    def puppetclasses(self, options=None):
        """
        Lists all puppet classes.
        """

        self.command_sub = "puppet_classes"

        result = self.execute(self._construct_command(options),
                              expect_csv=True)

        return result

    def remove_operating_system(self, options=None):
        """
        Removes OS from record.
        """

        self.command_sub = "remove_operatingsystem"

        result = self.execute(self._construct_command(options))

        return result

    def sc_params(self, options=None):
        """
        Lists all smart class parameters.
        """

        self.command_sub = "sc_params"

        result = self.execute(self._construct_command(options),
                              expect_csv=True)

        return result

    def set_parameter(self, options=None):
        """
        Creates or updates parameter for a record.
        """

        self.command_sub = "set_parameter"

        result = self.execute(self._construct_command(options))

        return result

    def update(self, options=None):
        """
        Updates existing record.
        """

        self.command_sub = "update"

        result = self.execute(self._construct_command(options))

        return result

    def _construct_command(self, options=None):
        """
        Build a hammer cli command based on the options passed
        """
        tail = ""

        options = options or {}

        for key, val in options.items():
            if val is not None:
                if isinstance(val, str):
                    tail += " --%s='%s'" % (key, val)
                else:
                    tail += " --%s=%s" % (key, val)
        cmd = self.command_base + " " + self.command_sub + " " + tail.strip()

        return cmd
