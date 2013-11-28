#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging.config
from lib.common import conf
from lib.common.helpers import csv_to_dictionary


class Base():
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

    try:
        logging.config.fileConfig("%s/logging.conf" % conf.get_root_path())
    except Exception:
        log_format = '%(levelname)s %(module)s:%(lineno)d: %(message)s'
        logging.basicConfig(format=log_format)

    logger = logging.getLogger("robottelo")
    logger.setLevel(int(conf.properties['nosetests.verbosity']))

    locale = conf.properties['main.locale']
    katello_user = conf.properties['foreman.admin.username']
    katello_passwd = conf.properties['foreman.admin.password']

    def execute(self, command, user=None, password=None):

        if user is None:
            user = self.katello_user
        if password is None:
            password = self.katello_passwd

        shell_cmd = "LANG=%s hammer -u %s -p %s --csv %s"

        stdout, stderr = self.conn.exec_command(
            shell_cmd % (self.locale, user, password, command))[-2:]

        output = stdout.readlines()
        errors = stderr.readlines()

        print ""  # helps for each command to be grouped with a new line.
        self.logger.debug(shell_cmd % (self.locale, user, password, command))
        if len(output) > 0:
            self.logger.debug("".join(output))
        if len(errors) > 0:
            self.logger.error("".join(errors))

        return output, errors

    def info(self, name):
        """
        Gets information by provided: name.
        @param name: ID (sometimes name works as well) to retrieve info.
        """
        self.command_sub = "info"

        cmd = "%s %s --id='%s'" % \
            (self.command_base, self.command_sub, name)

        stdout = self.execute(cmd)[0]
        return csv_to_dictionary(stdout) if stdout else {}

    def list(self, per_page=10000):
        """
        List information.
        @param cmdID: ID (sometimes name works as well) to retrieve info.
        """
        self.command_sub = "list"

        cmd = "%s %s --per-page=%d" % \
            (self.command_base, self.command_sub, per_page)

        stdout = self.execute(cmd)[0]
        return csv_to_dictionary(stdout) if stdout else {}

    def _construct_command(self, options={}):
        tail = ""
        for option in options.keys():
            if option:
                if options[option]:
                    tail = tail + " --%s='%s'" % (option, options[option])
                else:
                    tail = tail + " --%s" % option
        cmd = self.command_base + " " + self.command_sub + " " + tail.strip()
        return cmd
