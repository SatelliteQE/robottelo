#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging
import sys

from robottelo.common import conf
from robottelo.common.helpers import csv_to_dictionary
from threading import Lock

try:
    import paramiko
except ImportError:
    print "Please install paramiko."
    sys.exit(-1)


class SSHCommandResult(object):
    """
    Structure that returns in all Base commands results.
    """

    def __init__(self, stdout=None, stderr=None,
                 return_code=0, transform_csv=False):
        self.__stdout = stdout
        self.__stderr = stderr
        self.__return_code = return_code
        self.__transform_csv = transform_csv
        #  Does not make sense to return suspicious CSV if ($? <> 0)
        if transform_csv and self.__return_code == 0:
            self.__stdout = csv_to_dictionary(stdout) if stdout else {}

    @property
    def stdout(self):
        return self.__stdout

    @property
    def stderr(self):
        return self.__stderr

    @property
    def return_code(self):
        return self.__return_code


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

    logger = logging.getLogger("robottelo")

    locale = conf.properties['main.locale']
    katello_user = conf.properties['foreman.admin.username']
    katello_passwd = conf.properties['foreman.admin.password']

    __connection = None

    def __init__(self):
        pass

    @classmethod
    def get_connection(cls):
        if not cls.__connection:
            # Hide base logger from paramiko
            logging.getLogger("paramiko").setLevel(logging.ERROR)

            conn = paramiko.SSHClient()
            conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            host = conf.properties['main.server.hostname']
            root = conf.properties['main.server.ssh.username']
            key_filename = conf.properties['main.server.ssh.key_private']
            conn.connect(host, username=root, key_filename=key_filename)
            cls.__connection = conn
            cls.logger.info(
                "Paramiko instance prepared (and would be reused): %s"
                % hex(id(cls.__connection))
            )
        return cls.__connection

    @classmethod
    def upload_file(cls, local_file, remote_file=None):
        """
        Uploads a remote file to a server.
        """

        if not remote_file:
            remote_file = local_file

        sftp = cls.get_connection().open_sftp()
        sftp.put(local_file, remote_file)
        sftp.close()

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

    def dump(self, options=None):
        """
        Displays the content for existing partition table.
        """

        self.command_sub = "dump"

        result = self.execute(self._construct_command(options))

        return result

    def execute(self, command, user=None, password=None, expect_csv=False):

        # Dictionary object to hold all artifacts from Paramiko.
        if user is None:
            user = self.katello_user
        if password is None:
            password = self.katello_passwd

        output_csv = ""
        if expect_csv:
            output_csv = " --output csv"
        shell_cmd = "LANG=%s hammer -u %s -p %s" + output_csv + " %s"

        lock = Lock()
        with lock:
            stdout, stderr = Base.get_connection().exec_command(
                shell_cmd % (self.locale, user, password, command))[-2:]
            errorcode = stdout.channel.recv_exit_status()
            output = stdout.readlines()
            errors = stderr.readlines()

        # helps for each command to be grouped with a new line.
        print ""

        self.logger.debug(shell_cmd % (self.locale, user, password, command))

        if output:
            self.logger.debug("".join(output))
        if errors:
            self.logger.error("".join(errors))

        return SSHCommandResult(output, errors, errorcode, expect_csv)

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

        # TODO: update SSHCommandResult so that attributes are not
        # "protected" :)
        if len(result.stdout) == 1:
            result._SSHCommandResult__stdout = result.stdout[0]
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

    def remove_operating_system(self, options=None):
        """
        Removes OS from record.
        """

        self.command_sub = "remove_operatingsystem"

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
        tail = ""

        options = options or {}

        for key, val in options.items():
            if val is not None:
                if isinstance(val, str):
                    tail += " --%s='%s'" % (key, val)
                else:
                    tail += " --%s=%s" % (key, val)
            else:
                tail += " --%s" % key
        cmd = self.command_base + " " + self.command_sub + " " + tail.strip()

        return cmd
