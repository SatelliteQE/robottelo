"""Define and instantiate the configuration class for Robottelo."""
import logging
import os
import sys
import urlparse

from nailgun import entities, entity_mixins
from nailgun.config import ServerConfig

from robottelo import test_data

try:
    from ConfigParser import (
        NoOptionError,
        NoSectionError,
        SafeConfigParser as ConfigParser,
    )
except ImportError:
    from configparser import (
        ConfigParser,
        NoOptionError,
        NoSectionError,
    )

from logging import config
from robottelo.config import casts

LOGGER = logging.getLogger(__name__)
SETTINGS_FILE_NAME = 'robottelo.properties'


class ImproperlyConfigured(Exception):
    """Indicates that Robottelo somehow is improperly configured.

    For example, if settings file can not be found or some required
    configuration is not defined.
    """


def get_project_root():
    """Return the path to the Robottelo project root directory.

    :return: A directory path.
    :rtype: str
    """
    return os.path.realpath(os.path.join(
        os.path.dirname(__file__),
        os.pardir,
        os.pardir,
    ))


class INIReader(object):
    """ConfigParser wrapper able to cast value when reading INI options."""
    # Helper casters
    cast_boolean = casts.Boolean()
    cast_list = casts.List()
    cast_logging_level = casts.LoggingLevel()
    cast_tuple = casts.Tuple()

    def __init__(self, path):
        self.config_parser = ConfigParser()
        with open(path) as handler:
            self.config_parser.readfp(handler)
            if sys.version_info[0] < 3:
                # ConfigParser.readfp is deprecated on Python3, read_file
                # replaces it
                self.config_parser.readfp(handler)
            else:
                self.config_parser.read_file(handler)

    def get(self, section, option, default=None, cast=None):
        """Read an option from a section of a INI file.

        The default value will return if the look up option is not available.
        The value will be cast using a callable if specified otherwise a string
        will be returned.

        :param section: Section to look for.
        :param option: Option to look for.
        :param default: The value that should be used if the option is not
            defined.
        :param cast: If provided the value will be cast using the cast
            provided.

        """
        try:
            value = self.config_parser.get(section, option)
            if cast is not None:
                if cast is bool:
                    value = self.cast_boolean(value)
                elif cast is list:
                    value = self.cast_list(value)
                elif cast is tuple:
                    value = self.cast_tuple(value)
                else:
                    value = cast(value)
        except (NoSectionError, NoOptionError):
            value = default
        return value

    def has_section(self, section):
        """Check if section is available."""
        return self.config_parser.has_section(section)


class FeatureSettings(object):
    """Settings related to a feature.

    Create a instance of this class and assign attributes to map to the feature
    options.
    """
    def __init__(self, reader=None):
        self.reader = reader

    def read(self):
        """Subclasses must implement this method in order to populate itself
        with expected settings values.
        """
        raise NotImplementedError('Subclasses must implement read method.')

    def validate(self):
        """Subclasses must implement this method in order to validade the
        settings and raise ``ImproperlyConfigured`` if any issue is found.
        """
        raise NotImplementedError('Subclasses must implement validate method.')


class ServerSettings(FeatureSettings):
    """Satellite server settings definitions."""
    def __init__(self, *args, **kwargs):
        super(ServerSettings, self).__init__(*args, **kwargs)
        self.admin_password = None
        self.admin_username = None
        self.hostname = None
        self.port = None
        self.scheme = None
        self.ssh_key = None
        self.ssh_password = None
        self.ssh_username = None

    def read(self):
        """Read and validate Satellite server settings."""
        self.admin_password = self.reader.get(
            'server', 'admin_password', 'changeme')
        self.admin_username = self.reader.get(
            'server', 'admin_username', 'admin')
        self.hostname = self.reader.get('server', 'hostname')
        self.port = self.reader.get('server', 'port', cast=int)
        self.scheme = self.reader.get('server', 'scheme', 'https')
        self.ssh_key = self.reader.get('server', 'ssh_key')
        self.ssh_password = self.reader.get('server', 'ssh_password')
        self.ssh_username = self.reader.get('server', 'ssh_username', 'root')

    def validate(self):
        validation_errors = []
        if self.hostname is None:
            validation_errors.append('[server] hostname must be provided.')
        if (self.ssh_key is None and self.ssh_password is None):
            validation_errors.append(
                '[server] ssh_key or ssh_password must be provided.')
        return validation_errors

    def get_credentials(self):
        """Return credentials for interacting with a Foreman deployment API.

        :return: A username-password pair.
        :rtype: tuple

        """
        return (self.admin_username, self.admin_password)

    def get_url(self):
        """Return the base URL of the Foreman deployment being tested.

        The following values from the config file are used to build the URL:

        * ``[server] scheme`` (default: https)
        * ``[server] hostname`` (required)
        * ``[server] port`` (default: none)

        Setting ``port`` to 80 does *not* imply that ``scheme`` is 'https'. If
        ``port`` is 80 and ``scheme`` is unset, ``scheme`` will still default
        to 'https'.

        :return: A URL.
        :rtype: str

        """
        if not self.scheme:
            scheme = 'https'
        else:
            scheme = self.scheme
        # All anticipated error cases have been handled at this point.
        if not self.port:
            return urlparse.urlunsplit((scheme, self.hostname, '', '', ''))
        else:
            return urlparse.urlunsplit((
                scheme, '{0}:{1}'.format(self.hostname, self.port), '', '', ''
            ))

    def get_pub_url(self):
        """Return the pub URL of the server being tested.

        The following values from the config file are used to build the URL:

        * ``main.server.hostname`` (required)

        :return: The pub directory URL.
        :rtype: str

        """
        return urlparse.urlunsplit(('http', self.hostname, 'pub/', '', ''))

    def get_cert_rpm_url(self):
        """Return the Katello cert RPM URL of the server being tested.

        The following values from the config file are used to build the URL:

        * ``main.server.hostname`` (required)

        :return: The Katello cert RPM URL.
        :rtype: str

        """
        return urlparse.urljoin(
            self.get_pub_url(), 'katello-ca-consumer-latest.noarch.rpm')


class ClientsSettings(FeatureSettings):
    """Clients settings definitions."""
    def __init__(self, *args, **kwargs):
        super(ClientsSettings, self).__init__(*args, **kwargs)
        self.image_dir = None
        self.provisioning_server = None

    def read(self):
        """Read clients settings."""
        self.image_dir = self.reader.get(
            'clients', 'image_dir', '/opt/robottelo/images')
        self.provisioning_server = self.reader.get(
            'clients', 'provisioning_server')

    def validate(self):
        """Validate clients settings."""
        validation_errors = []
        if self.provisioning_server is None:
            validation_errors.append(
                '[clients] provisioning_server option must be provided.')
        return validation_errors


class DockerSettings(FeatureSettings):
    """Docker settings definitions."""
    def __init__(self, *args, **kwargs):
        super(DockerSettings, self).__init__(*args, **kwargs)
        self.unix_socket = None
        self.external_url = None

    def read(self):
        """Read docker settings."""
        self.unix_socket = self.reader.get(
            'docker', 'unix_socket', False, bool)
        self.external_url = self.reader.get('docker', 'external_url')

    def validate(self):
        """Validate docker settings."""
        validation_errors = []
        if not any(vars(self).values()):
            validation_errors.append(
                'Either [docker] unix_socket or external_url options must '
                'be provided or enabled.')
        return validation_errors

    def get_unix_socket_url(self):
        """Use the unix socket connection to the local docker daemon. Make sure
        that your Satellite server's docker is configured to allow foreman user
        accessing it. This can be done by::

            $ groupadd docker
            $ usermod -aG docker foreman
            # Add -G docker to the options for the docker daemon
            $ systemctl restart docker
            $ katello-service restart

        """
        return (
            'unix:///var/run/docker.sock'
            if self.unix_socket else None
        )


class FakeManifestSettings(FeatureSettings):
    """Fake manifest settings defintitions."""
    def __init__(self, *args, **kwargs):
        super(FakeManifestSettings, self).__init__(*args, **kwargs)
        self.cert_url = None
        self.key_url = None
        self.url = None

    def read(self):
        """Read fake manifest settings."""
        self.cert_url = self.reader.get(
            'fake_manifest', 'cert_url')
        self.key_url = self.reader.get(
            'fake_manifest', 'key_url')
        self.url = self.reader.get(
            'fake_manifest', 'url')

    def validate(self):
        """Validate fake manifest settings."""
        validation_errors = []
        if not all(vars(self).values()):
            validation_errors.append(
                'All [fake_manifest] cert_url, key_url, url options must '
                'be provided.'
            )
        return validation_errors


class LDAPSettings(FeatureSettings):
    """LDAP settings definitions."""
    def __init__(self, *args, **kwargs):
        super(LDAPSettings, self).__init__(*args, **kwargs)
        self.basedn = None
        self.grpbasedn = None
        self.hostname = None
        self.password = None
        self.username = None

    def read(self):
        """Read LDAP settings."""
        self.basedn = self.reader.get('ldap', 'basedn')
        self.grpbasedn = self.reader.get('ldap', 'grpbasedn')
        self.hostname = self.reader.get('ldap', 'hostname')
        self.password = self.reader.get('ldap', 'password')
        self.username = self.reader.get('ldap', 'username')

    def validate(self):
        """Validate LDAP settings."""
        validation_errors = []
        if not all(vars(self).values()):
            validation_errors.append(
                'All [ldap] basedn, grpbasedn, hostname, password, '
                'username options must be provided.'
            )
        return validation_errors


class PerformanceSettings(FeatureSettings):
    """Performance settings definitions."""
    def __init__(self, *args, **kwargs):
        super(PerformanceSettings, self).__init__(*args, **kwargs)
        self.time_hammer = None
        self.cdn_address = None
        self.virtual_machines = None
        self.fresh_install_savepoint = None
        self.enabled_repos_savepoint = None
        self.csv_buckets_count = None
        self.sync_count = None
        self.sync_type = None
        self.repos = None

    def read(self):
        """Read performance settings."""
        self.time_hammer = self.reader.get(
            'performance', 'time_hammer', False, bool)
        self.cdn_address = self.reader.get(
            'performance', 'cdn_address')
        self.virtual_machines = self.reader.get(
            'performance', 'virtual_machines', cast=list)
        self.fresh_install_savepoint = self.reader.get(
            'performance', 'fresh_install_savepoint')
        self.enabled_repos_savepoint = self.reader.get(
            'performance', 'enabled_repos_savepoint')
        self.csv_buckets_count = self.reader.get(
            'performance', 'csv_buckets_count', 10, int)
        self.sync_count = self.reader.get(
            'performance', 'sync_count', 3, int)
        self.sync_type = self.reader.get(
            'performance', 'sync_type', 'sync')
        self.repos = self.reader.get(
            'performance', 'repos', cast=list)

    def validate(self):
        """Validate performance settings."""
        validation_errors = []
        if self.cdn_address is None:
            validation_errors.append(
                '[performance] cdn_address must be provided.')
        if self.virtual_machines is None:
            validation_errors.append(
                '[performance] virtual_machines must be provided.')
        if self.fresh_install_savepoint is None:
            validation_errors.append(
                '[performance] fresh_install_savepoint must be provided.')
        if self.enabled_repos_savepoint is None:
            validation_errors.append(
                '[performance] enabled_repos_savepoint must be provided.')
        return validation_errors


class RHAISettings(FeatureSettings):
    """RHAI settings definitions."""
    def __init__(self, *args, **kwargs):
        super(RHAISettings, self).__init__(*args, **kwargs)
        self.insights_client_el6repo = None
        self.insights_client_el7repo = None

    def read(self):
        """Read RHAI settings."""
        self.insights_client_el6repo = self.reader.get(
            'rhai', 'insights_client_el6repo')
        self.insights_client_el7repo = self.reader.get(
            'rhai', 'insights_client_el7repo')

    def validate(self):
        """Validate RHAI settings."""
        return []


class TransitionSettings(FeatureSettings):
    """Transition settings definitions."""
    def __init__(self, *args, **kwargs):
        super(TransitionSettings, self).__init__(*args, **kwargs)
        self.exported_data = None

    def read(self):
        """Read transition settings."""
        self.exported_data = self.reader.get('transition', 'exported_data')

    def validate(self):
        """Validate transition settings."""
        validation_errors = []
        if self.exported_data is None:
            validation_errors.append(
                '[transition] exported_data must be provided.')
        return validation_errors


class Settings(object):
    """Robottelo's settings representation."""

    def __init__(self):
        self._configured = False
        self._validation_errors = []
        self.locale = None
        self.project = None
        self.reader = None
        self.rhel6_repo = None
        self.rhel7_repo = None
        self.screenshots_path = None
        self.server = None
        self.upstream = None
        self.verbosity = None
        self.virtual_display = None
        self.webdriver = None
        self.window_manager = None

        # Features
        self.clients = None
        self.docker = None
        self.fake_manifest = None
        self.ldap = None
        self.performance = None
        self.rhai = None
        self.transition = None

    def configure(self):
        """Read the settings file and parse the configturation.

        :raises: ImproperlyConfigured if any issue is found during the parsing
            or validation of the configruation.
        """
        if self.configured:
            # TODO: what to do here, raise and exception, just skip or ...?
            return

        # Expect the settings file to be on the robottelo project root.
        settings_path = os.path.join(get_project_root(), SETTINGS_FILE_NAME)
        if not os.path.isfile(settings_path):
            raise ImproperlyConfigured(
                'Not able to find settings file at {}'.format(settings_path))

        self.reader = INIReader(settings_path)
        self._read_robottelo_settings()
        self.server = ServerSettings(self.reader)
        self.server.read()
        self._validation_errors.extend(self.server.validate())
        if self.reader.has_section('clients'):
            self.clients = ClientsSettings(self.reader)
            self.clients.read()
            self._validation_errors.extend(self.clients.validate())
        if self.reader.has_section('docker'):
            self.docker = DockerSettings(self.reader)
            self.docker.read()
            self._validation_errors.extend(self.docker.validate())
        if self.reader.has_section('fake_manifest'):
            self.fake_manifest = FakeManifestSettings(self.reader)
            self.fake_manifest.read()
            self._validation_errors.extend(self.fake_manifest.validate())
        if self.reader.has_section('ldap'):
            self.ldap = LDAPSettings(self.reader)
            self.ldap.read()
            self._validation_errors.extend(self.ldap.validate())
        if self.reader.has_section('performance'):
            self.performance = PerformanceSettings(self.reader)
            self.performance.read()
            self._validation_errors.extend(self.performance.validate())
        if self.reader.has_section('rhai'):
            self.rhai = RHAISettings(self.reader)
            self.rhai.read()
            self._validation_errors.extend(self.rhai.validate())
        if self.reader.has_section('transition'):
            self.transition = TransitionSettings(self.reader)
            self.transition.read()
            self._validation_errors.extend(self.transition.validate())

        if self._validation_errors:
            raise ImproperlyConfigured(
                'Failed to validate the configuration, check the message(s):\n'
                '{}'.format('\n'.join(self._validation_errors))
            )

        self._configure_logging()
        self._configure_third_party_logging()
        self._configure_entities()
        self._configured = True

    def _read_robottelo_settings(self):
        """Read Robottelo's general settings."""
        self.locale = self.reader.get('robottelo', 'locale', 'en_US.UTF-8')
        self.project = self.reader.get('robottelo', 'project', 'sat')
        self.rhel6_repo = self.reader.get('robottelo', 'rhel6_repo', None)
        self.rhel7_repo = self.reader.get('robottelo', 'rhel7_repo', None)
        self.screenshots_path = self.reader.get(
            'robottelo', 'screenshots_path', None)
        self.upstream = self.reader.get('robottelo', 'upstream', True)
        self.verbosity = self.reader.get(
            'robottelo',
            'verbosity',
            'debug',
            INIReader.cast_logging_level
        )
        self.virtual_display = self.reader.get(
            'robottelo', 'virtual_display', False)
        self.webdriver = self.reader.get(
            'robottelo', 'webdriver', 'firefox')
        self.window_manager = self.reader.get(
            'robottelo', 'window_manager', None)

    @property
    def configured(self):
        """Returns True if the settings have already been configured."""
        return self._configured

    def _configure_entities(self):
        """Configure NailGun's entity classes.

        Do the following:

        * Set ``entity_mixins.CREATE_MISSING`` to ``True``. This causes method
        ``EntityCreateMixin.create_raw`` to generate values for empty and
        required fields.
        * Set ``nailgun.entity_mixins.DEFAULT_SERVER_CONFIG`` to whatever is
        returned by :meth:`robottelo.helpers.get_nailgun_config`. See
        ``robottelo.entity_mixins.Entity`` for more information on the effects
        of this.
        * Set a default value for ``nailgun.entities.GPGKey.content``.
        * Set the default value for
          ``nailgun.entities.DockerComputeResource.url``
        if either ``docker.internal_url`` or ``docker.external_url`` is set in
        the configuration file.
        """
        entity_mixins.CREATE_MISSING = True
        entity_mixins.DEFAULT_SERVER_CONFIG = ServerConfig(
            self.server.get_url(),
            self.server.get_credentials(),
            verify=False,
        )

        gpgkey_init = entities.GPGKey.__init__

        def patched_gpgkey_init(self, server_config=None, **kwargs):
            """Set a default value on the ``content`` field."""
            gpgkey_init(self, server_config, **kwargs)
            self._fields['content'].default = test_data.read(
                test_data.VALID_GPG_KEY)
        entities.GPGKey.__init__ = patched_gpgkey_init

        # NailGun provides a default value for ComputeResource.url. We override
        # that value if `docker.internal_url` or `docker.external_url` is set.
        docker_url = None
        # Try getting internal url
        docker_url = self.docker.get_unix_socket_url()
        # Try getting external url
        if docker_url is None:
            docker_url = self.docker.external_url
        if docker_url is not None:
            dockercr_init = entities.DockerComputeResource.__init__

            def patched_dockercr_init(self, server_config=None, **kwargs):
                """Set a default value on the ``docker_url`` field."""
                dockercr_init(self, server_config, **kwargs)
                self._fields['url'].default = docker_url
            entities.DockerComputeResource.__init__ = patched_dockercr_init

    def _configure_logging(self):
        """Configure logging for the entire framework.

        If a config named ``logging.conf`` exists in Robottelo's root
        directory, the logger is configured using the options in that file.
        Otherwise, a custom logging output format is set, and default values
        are used for all other logging options.
        """
        # All output should be made by the logging module, including warnings
        logging.captureWarnings(True)

        # Set the logging level based on the Robottelo's verbosity
        for name in ('nailgun', 'robottelo'):
            logging.getLogger(name).setLevel(self.verbosity)

        # Allow overriding logging config based on the presence of logging.conf
        # file on Robottelo's project root
        logging_conf_path = os.path.join(get_project_root(), 'logging.conf')
        if os.path.isfile(logging_conf_path):
            config.fileConfig(logging_conf_path)
        else:
            logging.basicConfig(
                format='%(levelname)s %(module)s:%(lineno)d: %(message)s'
            )

    def _configure_third_party_logging(self):
        """Increase the level of third party packages logging."""
        loggers = (
            'bugzilla',
            'easyprocess',
            'paramiko',
            'pyvirtualdisplay',
            'requests.packages.urllib3.connectionpool',
            'selenium.webdriver.remote.remote_connection',
        )
        for logger in loggers:
            logging.getLogger(logger).setLevel(logging.WARNING)
