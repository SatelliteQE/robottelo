# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Generic base class for cli hammer commands
"""

import logging

from robottelo.common import conf, ssh
from robottelo.common.helpers import info_dictionary


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
    command_requires_org = False  # True when command requires organization-id

    logger = logging.getLogger("robottelo")

    locale = conf.properties['main.locale']
    katello_user = conf.properties['foreman.admin.username']
    katello_passwd = conf.properties['foreman.admin.password']

    @classmethod
    def add_operating_system(cls, options=None):
        """
        Adds OS to record.
        """

        cls.command_sub = "add-operatingsystem"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def create(cls, options=None):
        """
        Creates a new record using the arguments passed via dictionary.
        """

        cls.command_sub = "create"

        if options is None:
            options = {}

        result = cls.execute(
            cls._construct_command(options),
            expect_csv=True)

        # Extract new object ID if it was successfully created
        if len(result.stdout) > 0 and 'id' in result.stdout[0]:
            obj_id = result.stdout[0]['id']

            # Fetch new object
            # Some Katello obj require the organization-id for subcommands
            info_options = {u'id': obj_id}
            if cls.command_requires_org:
                if 'organization-id' not in options:
                    raise Exception(
                        'organization-id option is required for %s.create' %
                        cls.__name__)
                info_options[u'organization-id'] = options[u'organization-id']

            new_obj = cls.info(info_options)
            # stdout should be a dictionary containing the object
            if len(new_obj.stdout) > 0:
                result.stdout = new_obj.stdout

        return result

    @classmethod
    def delete(cls, options=None):
        """
        Deletes existing record.
        """

        cls.command_sub = "delete"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def delete_parameter(cls, options=None):
        """
        Deletes parameter from record.
        """

        cls.command_sub = "delete-parameter"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def dump(cls, options=None):
        """
        Displays the content for existing partition table.
        """

        cls.command_sub = "dump"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def execute(cls, command, user=None, password=None,
                expect_csv=False, timeout=None):
        """
        Executes the command
        """
        if user is None:
            user = cls.katello_user
        if password is None:
            password = cls.katello_passwd

        output_csv = u""

        if expect_csv:
            output_csv = u" --output csv"
        shell_cmd = u"LANG=%s hammer -v -u %s -p %s %s %s"

        cmd = shell_cmd % (cls.locale, user, password, output_csv, command)

        return ssh.command(
            cmd.encode('utf-8'), expect_csv=expect_csv, timeout=timeout)

    @classmethod
    def exists(cls, options=None, tuple_search=None):
        """
        Search for record by given: ('name', '<search_value>')
        @return: CSV parsed structure[0] of the list.
        """

        if options is None:
            options = {}

        if tuple_search and 'search' not in options:
            options.update({"search": "%s=\"%s\"" %
                            (tuple_search[0], tuple_search[1])})

        result = cls.list(options)

        if result.stdout:
            result.stdout = result.stdout[0]

        return result

    @classmethod
    def info(cls, options=None):
        """
        Gets information by provided: options dictionary.
        @param options: ID (sometimes name or id).
        """

        cls.command_sub = "info"

        if options is None:
            options = {}

        if cls.command_requires_org and 'organization-id' not in options:
            raise Exception(
                'organization-id option is required for %s.info' %
                cls.__name__)

        result = cls.execute(cls._construct_command(options), expect_csv=False)

        # info_dictionary required to convert result.stdout to dic format
        updated_result = info_dictionary(result)

        return updated_result

    @classmethod
    def list(cls, options=None, per_page=True):
        """
        List information.
        @param options: ID (sometimes name works as well) to retrieve info.
        """

        cls.command_sub = "list"

        if options is None:
            options = {}

        if 'per-page' not in options and per_page:
            options[u'per-page'] = 10000

        if cls.command_requires_org and 'organization-id' not in options:
            raise Exception(
                'organization-id option is required for %s.list' %
                cls.__name__)

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def puppetclasses(cls, options=None):
        """
        Lists all puppet classes.
        """

        cls.command_sub = "puppet-classes"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def remove_operating_system(cls, options=None):
        """
        Removes OS from record.
        """

        cls.command_sub = "remove-operatingsystem"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def sc_params(cls, options=None):
        """
        Lists all smart class parameters.
        """

        cls.command_sub = "sc-params"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def set_parameter(cls, options=None):
        """
        Creates or updates parameter for a record.
        """

        cls.command_sub = "set-parameter"

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def update(cls, options=None):
        """
        Updates existing record.
        """

        cls.command_sub = "update"

        result = cls.execute(cls._construct_command(options), expect_csv=True)

        return result

    @classmethod
    def with_user(cls, username=None, password=None):
        if username is None:
            username = cls.katello_user
        if password is None:
            password = cls.katello_passwd

        class NUserBase(cls):
            katello_user = username
            katello_passwd = password
        return NUserBase

    @classmethod
    def _construct_command(cls, options=None):
        """
        Build a hammer cli command based on the options passed
        """

        tail = u""

        if options is None:
            options = {}

        for key, val in options.items():
            if val is not None:
                if val is True:
                    tail += u" --%s" % key
                elif val is not False:
                    tail += u" --%s='%s'" % (key, val)
        cmd = u"%s %s %s" % (cls.command_base, cls.command_sub,
                             tail.strip())

        return cmd
