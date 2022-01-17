"""Generic base class for cli hammer commands."""
import re

from wait_for import wait_for

from robottelo import ssh
from robottelo.cli import hammer
from robottelo.config import settings
from robottelo.logging import logger
from robottelo.ssh import get_client


class CLIError(Exception):
    """Indicates that a CLI command could not be run."""


class CLIBaseError(Exception):
    """Indicates that a CLI command has finished with return code different
    from zero.

    :param status: CLI command return code
    :param stderr: contents of the ``stderr``
    :param msg: explanation of the error

    """

    def __init__(self, status, stderr, msg):
        self.status = status
        self.stderr = stderr
        self.msg = msg
        super().__init__(msg)
        self.message = msg

    def __str__(self):
        """Include class name, status, stderr and msg to string repr so
        assertRaisesRegexp can be used to assert error present on any
        attribute
        """
        return repr(self)

    def __repr__(self):
        """Include class name status, stderr and msg to improve logging"""
        return '{}(status={!r}, stderr={!r}, msg={!r}'.format(
            type(self).__name__, self.status, self.stderr, self.msg
        )


class CLIReturnCodeError(CLIBaseError):
    """Error to be raised when an error occurs due to some validation error
    when execution hammer cli.
    See: https://github.com/SatelliteQE/robottelo/issues/3790 for more details
    """


class CLIDataBaseError(CLIBaseError):
    """Error to be raised when an error occurs due to some missing parameter
    which cause a data base error on hammer
    See: https://github.com/SatelliteQE/robottelo/issues/3790 for more details
    """


class Base:
    """Base class for hammer CLI interaction

    See Subcommands section in `hammer --help` output on your Satellite.
    """

    command_base = None  # each inherited instance should define this
    command_sub = None  # specific to instance, like: create, update, etc.
    command_end = None  # extending commands like for directory to pass
    command_requires_org = False  # True when command requires organization-id
    hostname = None  # Now used for Satellite class hammer execution
    logger = logger
    _db_error_regex = re.compile(r'.*INSERT INTO|.*SELECT .*FROM|.*violates foreign key')

    @classmethod
    def _handle_response(cls, response, ignore_stderr=None):
        """Verify ``status`` of the CLI command.

        Check for a non-zero return code or any stderr contents.

        :param response: a result object, returned by :mod:`robottelo.ssh.command`.
        :param ignore_stderr: indicates whether to throw a warning in logs if
            ``stderr`` is not empty.
        :returns: contents of ``stdout``.
        :raises robottelo.cli.base.CLIReturnCodeError: If return code is
            different from zero.
        """
        if isinstance(response.stderr, tuple):
            # the current contents of response.stderr is a tuple with the following properties
            # (<len(message)>,<message>).
            # This behavior could (and maybe should) change in the near future.
            # In the meantime, we don't need it here so we just use the message itself
            response.stderr = response.stderr[1]
        if isinstance(response.stderr, bytes):
            response.stderr = response.stderr.decode()
        if response.status != 0:
            full_msg = (
                f'Command "{cls.command_base} {cls.command_sub}" '
                f'finished with status {response.status}\n'
                f'stderr contains:\n{response.stderr}'
            )
            error_data = (response.status, response.stderr, full_msg)
            if cls._db_error_regex.search(full_msg):
                raise CLIDataBaseError(*error_data)
            raise CLIReturnCodeError(*error_data)
        if len(response.stderr) != 0 and not ignore_stderr:
            cls.logger.warning(f'stderr contains following message:\n{response.stderr}')
        return response.stdout

    @classmethod
    def add_operating_system(cls, options=None):
        """
        Adds OS to record.
        """

        cls.command_sub = 'add-operatingsystem'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def create(cls, options=None, timeout=None):
        """
        Creates a new record using the arguments passed via dictionary.
        """

        cls.command_sub = 'create'

        if options is None:
            options = {}

        result = cls.execute(cls._construct_command(options), output_format='csv', timeout=timeout)

        # Extract new object ID if it was successfully created
        if len(result) > 0 and 'id' in result[0]:
            obj_id = result[0]['id']

            # Fetch new object
            # Some Katello obj require the organization-id for subcommands
            info_options = {'id': obj_id}
            if cls.command_requires_org:
                if 'organization-id' not in options:
                    tmpl = 'organization-id option is required for {0}.create'
                    raise CLIError(tmpl.format(cls.__name__))
                info_options['organization-id'] = options['organization-id']

            # organization creation can take some time
            if cls.command_base == 'organization':
                new_obj, _ = wait_for(
                    lambda: cls.info(info_options),
                    timeout=300000,
                    delay=5,
                    silent_failure=True,
                    handle_exception=True,
                )
            else:
                new_obj = cls.info(info_options)

            # stdout should be a dictionary containing the object
            if len(new_obj) > 0:
                result = new_obj

        return result

    @classmethod
    def delete(cls, options=None, timeout=None):
        """Deletes existing record."""
        cls.command_sub = 'delete'
        return cls.execute(cls._construct_command(options), ignore_stderr=True, timeout=timeout)

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
                username = settings.server.admin_username
        if password is None:
            try:
                password = getattr(cls, 'foreman_admin_password')
            except AttributeError:
                password = settings.server.admin_password

        return (username, password)

    @classmethod
    def execute(
        cls,
        command,
        hostname=None,
        user=None,
        password=None,
        output_format=None,
        timeout=None,
        ignore_stderr=None,
        return_raw_response=None,
    ):
        """Executes the cli ``command`` on the server via ssh"""
        user, password = cls._get_username_password(user, password)
        time_hammer = settings.performance.time_hammer

        # add time to measure hammer performance
        cmd = 'LANG={} {} hammer -v {} {} {} {}'.format(
            settings.robottelo.locale,
            'time -p' if time_hammer else '',
            f'-u {user}' if user else "--interactive no",
            f'-p {password}' if password else "",
            f'--output={output_format}' if output_format else "",
            command,
        )
        response = ssh.command(
            cmd.encode('utf-8'),
            hostname=hostname or settings.server.hostname or cls.hostname,
            output_format=output_format,
            timeout=timeout,
        )
        if return_raw_response:
            return response
        else:
            return cls._handle_response(response, ignore_stderr=ignore_stderr)

    @classmethod
    def fm_execute(
        cls,
        command,
        hostname=None,
        timeout=None,
    ):
        """Executes the foreman-maintain cli commands on the server via ssh"""
        client = get_client(hostname=hostname or cls.hostname)
        result = client.execute(f'foreman-maintain {command}', timeout=timeout)
        return result

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

        if search is not None and 'search' not in options:
            options.update({'search': f'{search[0]}=\\"{search[1]}\\"'})

        result = cls.list(options)
        if result:
            result = result[0]

        return result

    @classmethod
    def info(cls, options=None, output_format=None, return_raw_response=None):
        """Reads the entity information."""
        cls.command_sub = 'info'

        if options is None:
            options = {}

        if cls.command_requires_org and 'organization-id' not in options:
            raise CLIError(f'organization-id option is required for {cls.__name__}.info')

        result = cls.execute(
            command=cls._construct_command(options),
            output_format=output_format,
            return_raw_response=return_raw_response,
        )
        if not return_raw_response and output_format != 'json':
            result = hammer.parse_info(result)
        return result

    @classmethod
    def list(cls, options=None, per_page=True, output_format='csv'):
        """
        List information.
        @param options: ID (sometimes name works as well) to retrieve info.
        """

        cls.command_sub = 'list'

        if options is None:
            options = {}

        if 'per-page' not in options and per_page:
            options['per-page'] = 10000

        # With the introduction of hammer defaults, a default organization can be set
        # this makes getting around this check awkward.
        # should we completely remove this or implement a workaround?
        # if cls.command_requires_org and 'organization-id' not in options:
        #     raise CLIError(f'organization-id option is required for {cls.__name__}.list')

        return cls.execute(cls._construct_command(options), output_format=output_format)

    @classmethod
    def puppetclasses(cls, options=None):
        """
        Lists all puppet classes.
        """

        cls.command_sub = 'puppet-classes'

        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def remove_operating_system(cls, options=None):
        """
        Removes OS from record.
        """

        cls.command_sub = 'remove-operatingsystem'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def sc_params(cls, options=None):
        """
        Lists all smart class parameters.
        """

        cls.command_sub = 'sc-params'

        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def set_parameter(cls, options=None):
        """
        Creates or updates parameter for a record.
        """

        cls.command_sub = 'set-parameter'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def update(cls, options=None, return_raw_response=None):
        """
        Updates existing record.
        """

        cls.command_sub = 'update'

        return cls.execute(
            cls._construct_command(options),
            output_format='csv',
            return_raw_response=return_raw_response,
        )

    @classmethod
    def with_user(cls, username=None, password=None):
        """Context Manager for credentials"""

        class Wrapper(cls):
            """Wrapper class which defines the foreman admin username and
            password to be used when executing any cli command.

            """

            foreman_admin_username = username
            foreman_admin_password = password

        return Wrapper

    @classmethod
    def _construct_command(cls, options=None):
        """Build a hammer cli command based on the options passed"""
        tail = ''

        if options is None:
            options = {}

        for key, val in options.items():
            if val is None:
                continue
            if val is True:
                tail += f' --{key}'
            elif val is not False:
                if isinstance(val, list):
                    val = ','.join(str(el) for el in val)
                tail += f' --{key}="{val}"'
        cmd = f"{cls.command_base} {cls.command_sub or ''} {tail.strip()} {cls.command_end or ''}"

        return cmd
