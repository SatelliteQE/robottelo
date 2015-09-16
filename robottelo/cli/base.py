# -*- encoding: utf-8 -*-
"""Generic base class for cli hammer commands."""
import logging
import re

from robottelo import ssh
from robottelo.cli import hammer
from robottelo.config import conf


# Task status message have two formats:
#   * "Task b18d3363-f4b8-44eb-871c-760e51444d22 success: 1.0/1, 100%,
#     elapsed: 00:00:02\n"
#   * "Task 6ba9d82a-ea55-4934-8aab-0e057102ee11 running: 0.005/1, 0%, 0.0/s,
#     elapsed: 00:00:02, ETA: 00:06:55\n"
TASK_STATUS_REGEX = re.compile(
    r'Task [\w-]+ \w+: [\d./]+, \d+%,( [\d./s]+,)? elapsed: [\d:]+'
    '(, ETA: [\d:]+)?\n\n?'
)


class CLIError(Exception):
    """Indicates that a CLI command could not be run."""


class Base(object):
    """
    @param command_base: base command of hammer.
    Output of recent `hammer --help`::

        activation-key                Manipulate activation keys.
        architecture                  Manipulate architectures.
        auth                          Foreman connection login/logout.
        auth-source                   Manipulate auth sources.
        capsule                       Manipulate capsule
        compute-resource              Manipulate compute resources.
        content-host                  Manipulate content hosts on the server
        content-view                  Manipulate content views.
        docker-image                  Manipulate docker images
        domain                        Manipulate domains.
        environment                   Manipulate environments.
        erratum                       Manipulate errata
        fact                          Search facts.
        filter                        Manage permission filters.
        global-parameter              Manipulate global parameters.
        gpg                           Manipulate GPG Key actions on the server
        host                          Manipulate hosts.
        host-collection               Manipulate host collections
        hostgroup                     Manipulate hostgroups.
        import                        Import data exported from a Red Hat Sat..
        lifecycle-environment         Manipulate lifecycle_environments
        location                      Manipulate locations.
        medium                        Manipulate installation media.
        model                         Manipulate hardware models.
        organization                  Manipulate organizations
        os                            Manipulate operating system.
        package                       Manipulate packages.
        package-group                 Manipulate package groups
        partition-table               Manipulate partition tables.
        ping                          Get the status of the server
        product                       Manipulate products.
        proxy                         Manipulate smart proxies.
        puppet-class                  Search puppet modules.
        puppet-module                 View Puppet Module details.
        report                        Browse and read reports.
        repository                    Manipulate repositories
        repository-set                Manipulate repository sets on the server
        role                          Manage user roles.
        sc-param                      Manipulate smart class parameters.
        shell                         Interactive shell
        subnet                        Manipulate subnets.
        subscription                  Manipulate subscriptions.
        sync-plan                     Manipulate sync plans
        task                          Tasks related actions.
        template                      Manipulate config templates.
        user                          Manipulate users.
        user-group                    Manage user groups.


    @since: 27.Nov.2013
    """
    command_base = None  # each inherited instance should define this
    command_sub = None  # specific to instance, like: create, update, etc
    command_requires_org = False  # True when command requires organization-id

    logger = logging.getLogger('robottelo')

    @classmethod
    def add_operating_system(cls, options=None):
        """
        Adds OS to record.
        """

        cls.command_sub = 'add-operatingsystem'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def create(cls, options=None):
        """
        Creates a new record using the arguments passed via dictionary.
        """

        cls.command_sub = 'create'

        if options is None:
            options = {}

        result = cls.execute(
            cls._construct_command(options), output_format='csv')

        # Extract new object ID if it was successfully created
        if len(result.stdout) > 0 and 'id' in result.stdout[0]:
            obj_id = result.stdout[0]['id']

            # Fetch new object
            # Some Katello obj require the organization-id for subcommands
            info_options = {u'id': obj_id}
            if cls.command_requires_org:
                if 'organization-id' not in options:
                    raise CLIError(
                        'organization-id option is required for {0}.create'
                        .format(cls.__name__)
                    )
                info_options[u'organization-id'] = options[u'organization-id']

            new_obj = cls.info(info_options)
            # stdout should be a dictionary containing the object
            if len(new_obj.stdout) > 0:
                result.stdout = new_obj.stdout

        return result

    @classmethod
    def delete(cls, options=None):
        """Deletes existing record."""
        cls.command_sub = 'delete'
        return cls._remove_task_status(
            cls.execute(cls._construct_command(options)))

    @classmethod
    def delete_parameter(cls, options=None):
        """
        Deletes parameter from record.
        """

        cls.command_sub = 'delete-parameter'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def dump(cls, options=None):
        """
        Displays the content for existing partition table.
        """

        cls.command_sub = 'dump'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def _get_username_password(cls, username=None, password=None):
        """Lookup for the username and password for cli command in following
        order:

        1. ``user`` or ``password`` parameters
        2. ``foreman_admin_username`` or ``foreman_admin_password`` attributes
        3. foreman.admin.username or foreman.admin.password configuration

        :return: A tuple with the username and password found
        :rtype: tuple

        """
        if username is None:
            try:
                username = getattr(cls, 'foreman_admin_username')
            except AttributeError:
                username = conf.properties['foreman.admin.username']
        if password is None:
            try:
                password = getattr(cls, 'foreman_admin_password')
            except AttributeError:
                password = conf.properties['foreman.admin.password']

        return (username, password)

    @classmethod
    def execute(cls, command, user=None, password=None, output_format=None,
                timeout=None):
        """Executes the cli ``command`` on the server via ssh"""
        user, password = cls._get_username_password(user, password)

        # add time to measure hammer performance
        perf_test = conf.properties.get('performance.test.foreman.perf', '0')
        cmd = u'LANG={0} {1} hammer -v -u {2} -p {3} {4} {5}'.format(
            conf.properties['main.locale'],
            u'time -p' if perf_test == '1' else '',
            user,
            password,
            u'--output={0}'.format(output_format) if output_format else u'',
            command,
        )

        return ssh.command(
            cmd.encode('utf-8'), output_format=output_format, timeout=timeout)

    @classmethod
    def exists(cls, options=None, search=None):
        """Search for an entity using the query ``search[0]="search[1]"``

        Will be used the ``list`` command with the ``--search`` option to do
        the search.

        If ``options`` argument already have a search key, then the ``search``
        argument will not be evaluated. Which allows different search query.

        """

        if options is None:
            options = {}

        if search is not None and u'search' not in options:
            options.update({u'search': u'{0}=\\"{1}\\"'.format(
                search[0], search[1])})

        result = cls.list(options)

        if result.stdout:
            result.stdout = result.stdout[0]

        return result

    @classmethod
    def info(cls, options=None, output_format=None):
        """Reads the entity information."""
        cls.command_sub = 'info'

        if options is None:
            options = {}

        if cls.command_requires_org and 'organization-id' not in options:
            raise CLIError(
                'organization-id option is required for {0}.info'
                .format(cls.__name__)
            )

        result = cls.execute(
            command=cls._construct_command(options),
            output_format=output_format
        )
        if output_format != 'json':
            result.stdout = hammer.parse_info(result.stdout)
        return result

    @classmethod
    def list(cls, options=None, per_page=True):
        """
        List information.
        @param options: ID (sometimes name works as well) to retrieve info.
        """

        cls.command_sub = 'list'

        if options is None:
            options = {}

        if 'per-page' not in options and per_page:
            options[u'per-page'] = 10000

        if cls.command_requires_org and 'organization-id' not in options:
            raise CLIError(
                'organization-id option is required for {0}.list'
                .format(cls.__name__)
            )

        result = cls.execute(
            cls._construct_command(options), output_format='csv')

        return result

    @classmethod
    def puppetclasses(cls, options=None):
        """
        Lists all puppet classes.
        """

        cls.command_sub = 'puppet-classes'

        result = cls.execute(
            cls._construct_command(options), output_format='csv')

        return result

    @classmethod
    def remove_operating_system(cls, options=None):
        """
        Removes OS from record.
        """

        cls.command_sub = 'remove-operatingsystem'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def sc_params(cls, options=None):
        """
        Lists all smart class parameters.
        """

        cls.command_sub = 'sc-params'

        result = cls.execute(
            cls._construct_command(options), output_format='csv')

        return result

    @classmethod
    def set_parameter(cls, options=None):
        """
        Creates or updates parameter for a record.
        """

        cls.command_sub = 'set-parameter'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def update(cls, options=None):
        """
        Updates existing record.
        """

        cls.command_sub = 'update'

        result = cls.execute(
            cls._construct_command(options), output_format='csv')

        return result

    @classmethod
    def with_user(cls, username=None, password=None):
        """Context Manager for credentials"""
        if username is None:
            username = conf.properties['foreman.admin.username']
        if password is None:
            password = conf.properties['foreman.admin.password']

        class Wrapper(cls):
            """Wrapper class which defines the foreman admin username and
            password to be used when executing any cli command.

            """
            foreman_admin_username = username
            foreman_admin_password = password

        return Wrapper

    @classmethod
    def _construct_command(cls, options=None):
        """
        Build a hammer cli command based on the options passed
        """

        tail = u''

        if options is None:
            options = {}

        for key, val in options.items():
            if val is None:
                continue
            if val is True:
                tail += u' --{0}'.format(key)
            elif val is not False:
                if isinstance(val, list):
                    val = ','.join(str(el) for el in val)
                tail += u' --{0}="{1}"'.format(key, val)
        cmd = u'{0} {1} {2}'.format(
            cls.command_base,
            cls.command_sub,
            tail.strip()
        )

        return cmd

    @classmethod
    def _remove_task_status(cls, result):
        """Remove all task status entries from the stderr if command return
        code is 0.

        """
        if result.return_code == 0:
            result.stderr = TASK_STATUS_REGEX.sub('', result.stderr)
        return result
