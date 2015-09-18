"""Define and instantiate the configuration class for Robottelo."""
import logging
import os
import sys

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
# from robottelo.helpers import configure_entities

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
        self.ldap = None
        self.fake_manifest = None
        self.clients = None
        self.docker = None
        self.rhai = None
        self.transition = None
        self.performance = None

    def configure(self):
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
        self.server = self._read_server_settings()
        if self.reader.has_section('ldap'):
            self.ldap = self._read_ldap_settings()
        if self.reader.has_section('fake_manifest'):
            self.fake_manifest = self._read_fake_manifest_settings()
        if self.reader.has_section('clients'):
            self.clients = self._read_clients_settings()
        if self.reader.has_section('docker'):
            self.docker = self._read_docker_settings()
        if self.reader.has_section('rhai'):
            self.rhai = self._read_rhai_settings()
        if self.reader.has_section('transition'):
            self.transition = self._read_trasition_settings()
        if self.reader.has_section('performance'):
            self.performance = self._read_performance_settings()

        if self._validation_errors:
            raise ImproperlyConfigured(
                'Failed to validate the configuration, check the message(s):\n'
                '{}'.format('\n'.join(self._validation_errors))
            )

        self._configure_logging()
        self._configure_third_party_logging()
        # configure_entities()
        self._configured = True

    def _read_robottelo_settings(self):
        # Read Robottelo's general settings
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

    def _read_server_settings(self):
        self.server = FeatureSettings()
        self.server.admin_password = self.reader.get(
            'server', 'admin_password', 'changeme')
        self.server.admin_username = self.reader.get(
            'server', 'admin_username', 'admin')
        self.server.hostname = self.reader.get('server', 'hostname')
        self.server.port = self.reader.get('server', 'port', cast=int)
        self.server.scheme = self.reader.get('server', 'scheme', 'https')
        self.server.ssh_key = self.reader.get('server', 'ssh_key')
        self.server.ssh_password = self.reader.get(
            'server', 'ssh_password')
        self.server.ssh_username = self.reader.get(
            'server', 'ssh_username', 'root')

        if self.server.hostname is None:
            self._validation_errors.append(
                '[server] hostname must be provided.')
        if (self.server.ssh_key is None and
                self.server.ssh_password is None):
            self._validation_errors.append(
                '[server] ssh_key or ssh_password must be provided.')

    def _read_ldap_settings(self):
        self.ldap = FeatureSettings()
        self.ldap.basedn = self.reader.get('ldap', 'basedn')
        self.ldap.grpbasedn = self.reader.get('ldap', 'grpbasedn')
        self.ldap.hostname = self.reader.get('ldap', 'hostname')
        self.ldap.password = self.reader.get('ldap', 'password')
        self.ldap.username = self.reader.get('ldap', 'username')

        if not all(vars(self.ldap).values()):
            self._validation_errors.append(
                'All [ldap] basedn, grpbasedn, hostname, password, '
                'username options must be provided.'
            )

    def _read_fake_manifest_settings(self):
        self.fake_manifest = FeatureSettings()
        self.fake_manifest.cert_url = self.reader.get(
            'fake_manifest', 'cert_url')
        self.fake_manifest.key_url = self.reader.get(
            'fake_manifest', 'key_url')
        self.fake_manifest.url = self.reader.get(
            'fake_manifest', 'url')

        if not all(vars(self.fake_manifest).values()):
            self._validation_errors.append(
                'All [fake_manifest] cert_url, key_url, url options must '
                'be provided.'
            )

    def _read_clients_settings(self):
        self.clients = FeatureSettings()
        self.clients.image_dir = self.reader.get(
            'clients', 'image_dir', '/opt/robottelo/images')
        self.clients.provisioning_server = self.reader.get(
            'clients', 'provisioning_server')

        if self.clients.provisioning_server is None:
            self._validation_errors.append(
                '[clients] provisioning_server option must be provided.')

    def _read_docker_settings(self):
        self.docker = FeatureSettings()
        self.docker.unix_socket = self.reader.get(
            'docker', 'unix_socket', False, bool)
        self.docker.external_url = self.reader.get(
            'docker', 'external_url')

        if not any(vars(self.docker).values()):
            self._validation_errors.append(
                'Either [docker] unix_socket or external_url options must '
                'be provided or enabled.')

    def _read_rhai_settings(self):
        self.rhai = FeatureSettings()
        self.rhai.insights_client_el6repo = self.reader.get(
            'rhai', 'insights_client_el6repo')
        self.rhai.insights_client_el7repo = self.reader.get(
            'rhai', 'insights_client_el7repo')

    def _read_trasition_settings(self):
        self.transition = FeatureSettings()
        self.transition.exported_data = self.reader.get(
            'transition', 'exported_data')

        if self.transition.exported_data is None:
            self._validation_errors.append(
                '[transition] exported_data must be provided.')

    def _read_performance_settings(self):
        self.performance = FeatureSettings()
        self.performance.time_hammer = self.reader.get(
            'performance', 'time_hammer', False, bool)
        self.performance.cdn_address = self.reader.get(
            'performance', 'cdn_address')
        self.performance.virtual_machines = self.reader.get(
            'performance', 'virtual_machines')
        self.performance.fresh_install_savepoint = self.reader.get(
            'performance', 'fresh_install_savepoint')
        self.performance.enabled_repos_savepoint = self.reader.get(
            'performance', 'enabled_repos_savepoint')
        self.performance.csv_buckets_count = self.reader.get(
            'performance', 'csv_buckets_count', 10, int)
        self.performance.sync_count = self.reader.get(
            'performance', 'sync_count', 3, int)
        self.performance.sync_type = self.reader.get(
            'performance', 'sync_type', 'sync')

        if self.performance.cdn_address is None:
            self._validation_errors.append(
                '[performance] cdn_address must be provided.')
        if self.performance.virtual_machines is None:
            self._validation_errors.append(
                '[performance] virtual_machines must be provided.')
        if self.performance.fresh_install_savepoint is None:
            self._validation_errors.append(
                '[performance] fresh_install_savepoint must be provided.')
        if self.performance.enabled_repos_savepoint is None:
            self._validation_errors.append(
                '[performance] enabled_repos_savepoint must be provided.')

    @property
    def configured(self):
        """Returns True if the settings have already been configured."""
        return self._configured

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
