"""Define and instantiate the configuration class for Robottelo."""
import importlib
import logging
import logging.config

import os
import six

from functools import partial

from six.moves.urllib.parse import urlunsplit, urljoin
from six.moves.configparser import (
    NoOptionError,
    NoSectionError,
    ConfigParser
)

import airgun.settings

from nailgun import entities, entity_mixins
from nailgun.config import ServerConfig
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
    cast_dict = casts.Dict()
    cast_list = casts.List()
    cast_logging_level = casts.LoggingLevel()
    cast_tuple = casts.Tuple()
    cast_webdriver_desired_capabilities = casts.WebdriverDesiredCapabilities()

    def __init__(self, path):
        self.config_parser = ConfigParser()
        with open(path) as handler:
            if six.PY2:
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
                elif cast is dict:
                    value = self.cast_dict(value)
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
    def read(self, reader):
        """Subclasses must implement this method in order to populate itself
        with expected settings values.

        :param reader: An INIReader instance to read the settings.
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

    def read(self, reader):
        """Read and validate Satellite server settings."""
        self.admin_password = reader.get(
            'server', 'admin_password', 'changeme')
        self.admin_username = reader.get(
            'server', 'admin_username', 'admin')
        self.hostname = reader.get('server', 'hostname')
        self.port = reader.get('server', 'port', cast=int)
        self.scheme = reader.get('server', 'scheme', 'https')
        self.ssh_key = reader.get('server', 'ssh_key')
        self.ssh_password = reader.get('server', 'ssh_password')
        self.ssh_username = reader.get('server', 'ssh_username', 'root')

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
            return urlunsplit((scheme, self.hostname, '', '', ''))
        else:
            return urlunsplit((
                scheme, '{0}:{1}'.format(self.hostname, self.port), '', '', ''
            ))

    def get_pub_url(self):
        """Return the pub URL of the server being tested.

        The following values from the config file are used to build the URL:

        * ``main.server.hostname`` (required)

        :return: The pub directory URL.
        :rtype: str

        """
        return urlunsplit(('http', self.hostname, 'pub/', '', ''))

    def get_cert_rpm_url(self):
        """Return the Katello cert RPM URL of the server being tested.

        The following values from the config file are used to build the URL:

        * ``main.server.hostname`` (required)

        :return: The Katello cert RPM URL.
        :rtype: str

        """
        return urljoin(
            self.get_pub_url(), 'katello-ca-consumer-latest.noarch.rpm')


class BugzillaSettings(FeatureSettings):
    """Bugzilla server settings definitions."""
    def __init__(self, *args, **kwargs):
        super(BugzillaSettings, self).__init__(*args, **kwargs)
        self.password = None
        self.username = None
        self.wontfix_lookup = None

    def read(self, reader):
        """Read and validate Bugzilla server settings."""
        get_bz = partial(reader.get, 'bugzilla')
        self.password = get_bz('bz_password', None)
        self.username = get_bz('bz_username', None)
        self.wontfix_lookup = reader.get(
            'bugzilla', 'wontfix_lookup', True, bool)

    def get_credentials(self):
        """Return credentials for interacting with a Bugzilla API.

        :return: A username-password dict.
        :rtype: dict

        """
        return {'user': self.username, 'password': self.password}

    def validate(self):
        validation_errors = []
        if self.username is None:
            validation_errors.append(
                '[bugzilla] bz_username must be provided.')
        if self.password is None:
            validation_errors.append(
                '[bugzilla] bz_password must be provided.')
        return validation_errors


class CapsuleSettings(FeatureSettings):
    """Clients settings definitions."""

    def __init__(self, *args, **kwargs):
        super(CapsuleSettings, self).__init__(*args, **kwargs)
        self.domain = None
        self.instance_name = None
        self.hash = None
        self.ddns_package_url = None

    def read(self, reader):
        """Read clients settings."""
        self.instance_name = reader.get('capsule', 'instance_name')

    @property
    def hostname(self):
        if self.instance_name and self.domain:
            return '{0}.{1}'.format(self.instance_name, self.domain)

        return None

    def validate(self):
        """Validate capsule settings."""
        validation_errors = []
        if self.instance_name is None:
            validation_errors.append(
                '[capsule] instance_name option must be provided.')
        return validation_errors


class CertsSettings(FeatureSettings):
    """Katello-certs settings definitions."""
    def __init__(self, *args, **kwargs):
        super(CertsSettings, self).__init__(*args, **kwargs)
        self.cert_file = None
        self.key_file = None
        self.req_file = None
        self.ca_bundle_file = None

    def read(self, reader):
        """Read certs settings."""
        self.cert_file = reader.get('certs', 'CERT_FILE')
        self.key_file = reader.get('certs', 'KEY_FILE')
        self.req_file = reader.get('certs', 'REQ_FILE')
        self.ca_bundle_file = reader.get('certs', 'CA_BUNDLE_FILE')

    def validate(self):
        """Validate certs settings."""
        validation_errors = []
        if self.cert_file is None:
            validation_errors.append(
                '[certs] cert_file option must be provided.'
            )
        if self.key_file is None:
            validation_errors.append(
                '[certs] key_file option must be provided.'
            )
        if self.req_file is None:
            validation_errors.append(
                '[certs] req_file option must be provided.'
            )
        if self.ca_bundle_file is None:
            validation_errors.append(
                '[certs] ca_bundle_file option must be provided.'
            )
        return validation_errors


class ClientsSettings(FeatureSettings):
    """Clients settings definitions."""
    def __init__(self, *args, **kwargs):
        super(ClientsSettings, self).__init__(*args, **kwargs)
        self.image_dir = None
        self.provisioning_server = None
        self.distros = None

    def read(self, reader):
        """Read clients settings."""
        self.image_dir = reader.get('clients', 'image_dir')
        self.provisioning_server = reader.get('clients', 'provisioning_server')
        self.distros = [x.strip() for x in reader.get('clients', 'distros', "rhel7").split(",")]

    def validate(self):
        """Validate clients settings."""
        validation_errors = []
        if self.provisioning_server is None:
            validation_errors.append(
                '[clients] provisioning_server option must be provided.')
        return validation_errors


class DistroSettings(FeatureSettings):
    """Distro settings definitions."""
    def __init__(self, *args, **kwargs):
        super(DistroSettings, self).__init__(*args, **kwargs)
        self.image_el6 = None
        self.image_el7 = None
        self.image_sles11 = None
        self.image_sles12 = None

    def read(self, reader):
        """Read distro settings."""
        self.image_el6 = reader.get('distro', 'image_el6')
        self.image_el7 = reader.get('distro', 'image_el7')
        self.image_sles11 = reader.get('distro', 'image_sles11')
        self.image_sles12 = reader.get('distro', 'image_sles12')

    def validate(self):
        """Validate distro settings."""
        validation_errors = []
        if not all(self.__dict__.values()):
            validation_errors.append('All [distro] %s options must be provided.'
                                     % list(self.__dict__.keys()))
        return validation_errors


class DockerSettings(FeatureSettings):
    """Docker settings definitions."""
    def __init__(self, *args, **kwargs):
        super(DockerSettings, self).__init__(*args, **kwargs)
        self.docker_image = None
        self.external_url = None
        self.external_registry_1 = None
        self.external_registry_2 = None
        self.unix_socket = None
        self.private_registry_url = None
        self.private_registry_name = None
        self.private_registry_username = None
        self.private_registry_password = None

    def read(self, reader):
        """Read docker settings."""
        self.docker_image = reader.get('docker', 'docker_image')
        self.unix_socket = reader.get(
            'docker', 'unix_socket', False, bool)
        self.external_url = reader.get('docker', 'external_url')
        self.external_registry_1 = reader.get('docker', 'external_registry_1')
        self.external_registry_2 = reader.get('docker', 'external_registry_2')
        self.private_registry_url = reader.get(
            'docker', 'private_registry_url')
        self.private_registry_name = reader.get(
            'docker', 'private_registry_name')
        self.private_registry_username = reader.get(
            'docker', 'private_registry_username')
        self.private_registry_password = reader.get(
            'docker', 'private_registry_password')

    def validate(self):
        """Validate docker settings."""
        validation_errors = []
        if not self.docker_image:
            validation_errors.append(
                '[docker] docker_image option must be provided or enabled.')
        if not all((self.external_registry_1, self.external_registry_2)):
            validation_errors.append(
                'Both [docker] external_registry_1 and external_registry_2 '
                'options must be provided.')
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


class EC2Settings(FeatureSettings):
    """AWS EC2 settings definitions."""

    def __init__(self, *args, **kwargs):
        super(EC2Settings, self).__init__(*args, **kwargs)
        self.access_key = None
        self.secret_key = None
        self.region = None
        self.image = None
        self.availability_zone = None
        self.subnet = None
        self.security_groups = None
        self.managed_ip = None

    def read(self, reader):
        """Read AWS EC2 settings."""
        self.access_key = reader.get('ec2', 'access_key')
        self.secret_key = reader.get('ec2', 'secret_key')
        self.region = reader.get('ec2', 'region', 'us-west-2')
        self.image = reader.get('ec2', 'image')
        self.availability_zone = reader.get('ec2', 'availability_zone')
        self.subnet = reader.get('ec2', 'subnet')
        self.security_groups = reader.get(
            'ec2', 'security_groups', ['default'], list)
        self.managed_ip = reader.get('ec2', 'managed_ip', 'Private')

    def validate(self):
        """Validate AWS EC2 settings."""
        validation_errors = []
        if not all((self.access_key, self.secret_key, self.region)):
            validation_errors.append(
                'All [ec2] access_key, secret_key, region options '
                'must be provided'
            )
        if self. managed_ip not in ('Private', 'Public'):
            validation_errors.append(
                '[ec2] managed_ip option must be Public or Private'
            )
        return validation_errors


class FakeManifestSettings(FeatureSettings):
    """Fake manifest settings defintitions."""
    def __init__(self, *args, **kwargs):
        super(FakeManifestSettings, self).__init__(*args, **kwargs)
        self.cert_url = None
        self.key_url = None
        self.url = None

    def read(self, reader):
        """Read fake manifest settings."""
        self.cert_url = reader.get('fake_manifest', 'cert_url')
        self.key_url = reader.get('fake_manifest', 'key_url')
        url = {}
        try:
            url = reader.get('fake_manifest', 'url', cast=dict)
        except ValueError:
            url['default'] = reader.get('fake_manifest', 'url')
        self.url = url

    def validate(self):
        """Validate fake manifest settings."""
        validation_errors = []
        if not all(vars(self).values()):
            validation_errors.append(
                'All [fake_manifest] cert_url, key_url, url options must be provided.'
            )
        if isinstance(self.url, dict) and self.url.get('default') is None:
            validation_errors.append(
                'URL with key "default" is required if multiple URLs are provided'
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

    def read(self, reader):
        """Read LDAP settings."""
        self.basedn = reader.get('ldap', 'basedn')
        self.grpbasedn = reader.get('ldap', 'grpbasedn')
        self.hostname = reader.get('ldap', 'hostname')
        self.password = reader.get('ldap', 'password')
        self.username = reader.get('ldap', 'username')

    def validate(self):
        """Validate LDAP settings."""
        validation_errors = []
        if not all(vars(self).values()):
            validation_errors.append(
                'All [ldap] basedn, grpbasedn, hostname, password, '
                'username options must be provided.'
            )
        return validation_errors


class LDAPIPASettings(FeatureSettings):
    """LDAP freeIPA settings definitions."""
    def __init__(self, *args, **kwargs):
        super(LDAPIPASettings, self).__init__(*args, **kwargs)
        self.basedn_ipa = None
        self.grpbasedn_ipa = None
        self.hostname_ipa = None
        self.password_ipa = None
        self.username_ipa = None
        self.user_ipa = None

    def read(self, reader):
        """Read LDAP freeIPA settings."""
        self.basedn_ipa = reader.get('ipa', 'basedn_ipa')
        self.grpbasedn_ipa = reader.get('ipa', 'grpbasedn_ipa')
        self.hostname_ipa = reader.get('ipa', 'hostname_ipa')
        self.password_ipa = reader.get('ipa', 'password_ipa')
        self.username_ipa = reader.get('ipa', 'username_ipa')
        self.user_ipa = reader.get('ipa', 'user_ipa')

    def validate(self):
        """Validate LDAP freeIPA settings."""
        validation_errors = []
        if not all(vars(self).values()):
            validation_errors.append(
                'All [ipa] basedn_ipa, grpbasedn_ipa, hostname_ipa,'
                ' password_ipa, username_ipa, user_ipa options must be provided.'
            )
        return validation_errors


class LibvirtHostSettings(FeatureSettings):
    """Libvirt host settings definitions."""
    def __init__(self, *args, **kwargs):
        super(LibvirtHostSettings, self).__init__(*args, **kwargs)
        self.libvirt_image_dir = None
        self.libvirt_hostname = None

    def read(self, reader):
        """Read libvirt host settings."""
        self.libvirt_image_dir = reader.get(
            'compute_resources', 'libvirt_image_dir', '/var/lib/libvirt/images'
        )
        self.libvirt_hostname = reader.get(
            'compute_resources', 'libvirt_hostname')

    def validate(self):
        """Validate libvirt host settings."""
        validation_errors = []
        if self.libvirt_hostname is None:
            validation_errors.append(
                '[compute_resources] libvirt_hostname option must be provided.'
            )
        return validation_errors


class FakeCapsuleSettings(FeatureSettings):
    """Fake Capsule settings definitions."""
    def __init__(self, *args, **kwargs):
        super(FakeCapsuleSettings, self).__init__(*args, **kwargs)
        self.port_range = None

    def read(self, reader):
        """Read fake capsule settings"""
        self.port_range = reader.get(
            'fake_capsules', 'port_range', cast=tuple
        )

    def validate(self):
        """Validate fake capsule settings."""
        validation_errors = []
        if self.port_range is None:
            validation_errors.append(
                '[fake_capsules] port_range option must be provided.'
            )
        return validation_errors


class RHEVSettings(FeatureSettings):
    """RHEV settings definitions."""
    def __init__(self, *args, **kwargs):
        super(RHEVSettings, self).__init__(*args, **kwargs)
        # Compute Resource Information
        self.hostname = None
        self.username = None
        self.password = None
        self.datacenter = None
        self.vm_name = None
        self.storage_domain = None
        # Image Information
        self.image_os = None
        self.image_arch = None
        self.image_username = None
        self.image_password = None
        self.image_name = None
        self.ca_cert = None

    def read(self, reader):
        """Read rhev settings."""
        # Compute Resource Information
        self.hostname = reader.get('rhev', 'hostname')
        self.username = reader.get('rhev', 'username')
        self.password = reader.get('rhev', 'password')
        self.datacenter = reader.get('rhev', 'datacenter')
        self.vm_name = reader.get('rhev', 'vm_name')
        self.storage_domain = reader.get('rhev', 'storage_domain')
        # Image Information
        self.image_os = reader.get('rhev', 'image_os')
        self.image_arch = reader.get('rhev', 'image_arch')
        self.image_username = reader.get('rhev', 'image_username')
        self.image_password = reader.get('rhev', 'image_password')
        self.image_name = reader.get('rhev', 'image_name')
        self.ca_cert = reader.get('rhev', 'ca_cert', None)

    def validate(self):
        """Validate rhev settings."""
        validation_errors = []
        values = [v for k, v in vars(self).items() if k != 'ca_cert']
        if not all(values):
            validation_errors.append(
                'All [rhev] hostname, username, password, datacenter, '
                'vm_name, image_name, image_os, image_arch, image_username, '
                'image_name options must be provided.'
            )
        return validation_errors


class VmWareSettings(FeatureSettings):
    """VmWare settings definitions."""
    def __init__(self, *args, **kwargs):
        super(VmWareSettings, self).__init__(*args, **kwargs)
        # Compute Resource Information
        self.vcenter = None
        self.username = None
        self.password = None
        self.datacenter = None
        self.vm_name = None
        # Image Information
        self.image_os = None
        self.image_arch = None
        self.image_username = None
        self.image_password = None
        self.image_name = None

    def read(self, reader):
        """Read vmware settings."""
        # Compute Resource Information
        self.vcenter = reader.get('vmware', 'vcenter')
        self.username = reader.get('vmware', 'username')
        self.password = reader.get('vmware', 'password')
        self.datacenter = reader.get('vmware', 'datacenter')
        self.vm_name = reader.get('vmware', 'vm_name')
        # Image Information
        self.image_os = reader.get('vmware', 'image_os')
        self.image_arch = reader.get('vmware', 'image_arch')
        self.image_username = reader.get('vmware', 'image_username')
        self.image_password = reader.get('vmware', 'image_password')
        self.image_name = reader.get('vmware', 'image_name')

    def validate(self):
        """Validate vmware settings."""
        validation_errors = []
        if not all(vars(self).values()):
            validation_errors.append(
                'All [vmware] vcenter, username, password, datacenter, '
                'vm_name, image_name, image_os, image_arch, image_usernam, '
                'image_name options must be provided.'
            )
        return validation_errors


class DiscoveryISOSettings(FeatureSettings):
    """Discovery ISO name settings definition."""
    def __init__(self, *args, **kwargs):
        super(DiscoveryISOSettings, self).__init__(*args, **kwargs)
        self.discovery_iso = None

    def read(self, reader):
        """Read discovery iso setting."""
        self.discovery_iso = reader.get('discovery', 'discovery_iso')

    def validate(self):
        """Validate discovery iso name setting."""
        validation_errors = []
        if self.discovery_iso is None:
            validation_errors.append(
                '[discovery] discovery iso name must be provided.'
            )
        return validation_errors


class OscapSettings(FeatureSettings):
    """Oscap settings definitions."""
    def __init__(self, *args, **kwargs):
        super(OscapSettings, self).__init__(*args, **kwargs)
        self.content_path = None
        self.tailoring_path = None

    def read(self, reader):
        """Read Oscap settings."""
        self.content_path = reader.get('oscap', 'content_path')
        self.tailoring_path = reader.get('oscap', 'tailoring_path')

    def validate(self):
        """Validate Oscap settings."""
        validation_errors = []
        if self.content_path is None:
            validation_errors.append(
                '[oscap] content_path option must be provided.'
            )
        if self.tailoring_path is None:
            validation_errors.append(
                '[oscap] tailoring_path option must be provided.'
            )
        return validation_errors


class OSPSettings(FeatureSettings):
    """OSP settings definitions."""
    def __init__(self, *args, **kwargs):
        super(OSPSettings, self).__init__(*args, **kwargs)
        # Compute Resource Information
        self.hostname = None
        self.username = None
        self.password = None
        self.tenant = None
        self.vm_name = None
        self.security_group = None
        # Image Information
        self.image_os = None
        self.image_arch = None
        self.image_username = None
        self.image_name = None

    def read(self, reader):
        """Read osp settings."""
        # Compute Resource Information
        self.hostname = reader.get('osp', 'hostname')
        self.username = reader.get('osp', 'username')
        self.password = reader.get('osp', 'password')
        self.tenant = reader.get('osp', 'tenant')
        self.security_group = reader.get('osp', 'security_group')
        self.vm_name = reader.get('osp', 'vm_name')
        # Image Information
        self.image_os = reader.get('osp', 'image_os')
        self.image_arch = reader.get('osp', 'image_arch')
        self.image_username = reader.get('osp', 'image_username')
        self.image_name = reader.get('osp', 'image_name')

    def validate(self):
        """Validate osp settings."""
        validation_errors = []
        if not all(vars(self).values()):
            validation_errors.append(
                'All [osp] hostname, username, password, tenant, '
                'vm_name, image_name, image_os, image_arch, image_username, '
                'image_name options must be provided.'
            )
        return validation_errors


class OstreeSettings(FeatureSettings):
    """Ostree settings definitions."""
    def __init__(self, *args, **kwargs):
        super(OstreeSettings, self).__init__(*args, **kwargs)
        self.ostree_installer = None

    def read(self, reader):
        """Read Ostree settings."""
        self.ostree_installer = reader.get('ostree', 'ostree_installer')

    def validate(self):
        """Validate Ostree settings."""
        validation_errors = []
        if self.ostree_installer is None:
            validation_errors.append(
                '[ostree] ostree_installer option must be provided.'
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

    def read(self, reader):
        """Read performance settings."""
        self.time_hammer = reader.get(
            'performance', 'time_hammer', False, bool)
        self.cdn_address = reader.get(
            'performance', 'cdn_address')
        self.virtual_machines = reader.get(
            'performance', 'virtual_machines', cast=list)
        self.fresh_install_savepoint = reader.get(
            'performance', 'fresh_install_savepoint')
        self.enabled_repos_savepoint = reader.get(
            'performance', 'enabled_repos_savepoint')
        self.csv_buckets_count = reader.get(
            'performance', 'csv_buckets_count', 10, int)
        self.sync_count = reader.get(
            'performance', 'sync_count', 3, int)
        self.sync_type = reader.get(
            'performance', 'sync_type', 'sync')
        self.repos = reader.get(
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

    def read(self, reader):
        """Read RHAI settings."""
        self.insights_client_el6repo = reader.get(
            'rhai', 'insights_client_el6repo')
        self.insights_client_el7repo = reader.get(
            'rhai', 'insights_client_el7repo')

    def validate(self):
        """Validate RHAI settings."""
        return []


class SSHClientSettings(FeatureSettings):
    """SSHClient settings definitions."""
    def __init__(self, *args, **kwargs):
        super(SSHClientSettings, self).__init__(*args, **kwargs)
        self._command_timeout = None
        self._connection_timeout = None

    @property
    def command_timeout(self):
        return self._command_timeout if (
            self._command_timeout is not None) else 300

    @property
    def connection_timeout(self):
        return self._connection_timeout if (
            self._connection_timeout is not None) else 10

    def read(self, reader):
        """Read SSHClient settings."""
        self._command_timeout = reader.get(
            'ssh_client', 'command_timeout', default=300, cast=int)
        self._connection_timeout = reader.get(
            'ssh_client', 'connection_timeout', default=10, cast=int)

    def validate(self):
        """Validate SSHClient settings."""
        return []


class VlanNetworkSettings(FeatureSettings):
    """Vlan Network settings definitions."""
    def __init__(self, *args, **kwargs):
        super(VlanNetworkSettings, self).__init__(*args, **kwargs)
        self.subnet = None
        self.netmask = None
        self.gateway = None
        self.bridge = None
        self.network = None
        self.dhcp_ipam = None
        self.dhcp_from = None
        self.dhcp_to = None
        self.dns_primary = None

    def read(self, reader):
        """Read Vlan Network settings."""
        self.subnet = reader.get('vlan_networking', 'subnet')
        self.netmask = reader.get('vlan_networking', 'netmask')
        self.gateway = reader.get('vlan_networking', 'gateway')
        self.bridge = reader.get('vlan_networking', 'bridge')
        self.network = reader.get('vlan_networking', 'network')
        self.dhcp_ipam = reader.get('vlan_networking', 'dhcp_ipam')
        self.dhcp_from = reader.get('vlan_networking', 'dhcp_from')
        self.dhcp_to = reader.get('vlan_networking', 'dhcp_to')
        self.dns_primary = reader.get('vlan_networking', 'dns_primary')

    def validate(self):
        """Validate Vlan Network settings."""
        validation_errors = []
        if bool(self.bridge) == bool(self.network):
            validation_errors.append(
                'exactly one of the "bridge" or "network" parameters '
                'must be specified')
        if bool(self.dhcp_from) != bool(self.dhcp_to):
            validation_errors.append(
                'both or none of "dhcp_from", "dhcp_to" parameters '
                'must be specified')
        if self.dhcp_ipam and self.dhcp_ipam not in ['Internal DB', 'DHCP']:
            validation_errors.append(
                '[vlan_networking] "dhcp_ipam" must be one of "Internal DB" or "DHCP"')
        ignored = ['bridge', 'network', 'dhcp_ipam', 'dhcp_from', 'dhcp_to', 'dns_primary']
        if not all(value for (key, value) in vars(self).items() if key not in ignored):
            validation_errors.append(
                'All [vlan_networking] subnet, netmask, gateway, bridge|network '
                'options must be provided.')
        return validation_errors


class UpgradeSettings(FeatureSettings):
    """Satellite upgrade settings definitions."""
    def __init__(self, *args, **kwargs):
        super(UpgradeSettings, self).__init__(*args, **kwargs)
        self.upgrade_data = None

    def read(self, reader):
        """Read and validate Satellite server settings."""
        self.upgrade_data = reader.get('upgrade', 'upgrade_data')

    def validate(self):
        validation_errors = []
        if self.upgrade_data is None:
            validation_errors.append('[upgrade] data must be provided.')
        return validation_errors


class SharedFunctionSettings(FeatureSettings):
    """Shared function settings definitions."""

    MAX_SHARE_TIMEOUT = 86400

    def __init__(self, *args, **kwargs):
        super(SharedFunctionSettings, self).__init__(*args, **kwargs)
        self.storage = None
        self.scope = None
        self.enabled = None
        self.lock_timeout = None
        self.share_timeout = None
        self.redis_host = None
        self.redis_port = None
        self.redis_db = None
        self.redis_password = None
        self.call_retries = None

    def read(self, reader):
        """Read shared settings."""
        self.storage = reader.get('shared_function', 'storage', 'file')
        self.scope = reader.get('shared_function', 'scope', None)
        self.enabled = reader.get(
            'shared_function', 'enabled', False, bool)
        self.lock_timeout = reader.get(
            'shared_function', 'lock_timeout', 7200, int)
        self.share_timeout = reader.get(
            'shared_function', 'share_timeout', self.MAX_SHARE_TIMEOUT, int)
        self.redis_host = reader.get(
            'shared_function', 'redis_host', 'localhost')
        self.redis_port = reader.get(
            'shared_function', 'redis_port', 6379, int)
        self.redis_db = reader.get(
            'shared_function', 'redis_db', 0, int)
        self.redis_password = reader.get(
            'shared_function', 'redis_password', None)
        self.call_retries = reader.get(
            'shared_function', 'call_retries', 2, int)

    def validate(self):
        """Validate the shared settings"""
        validation_errors = []
        supported_storage_handlers = ['file', 'redis']
        if self.storage not in supported_storage_handlers:
            validation_errors.append(
                '[shared] storage must be one of {}'
                .format(supported_storage_handlers)
            )
        if self.storage == 'redis':
            try:
                importlib.import_module('redis')
            except ImportError:
                validation_errors.append(
                    '[shared] python redis package not installed')
        if self.share_timeout is None:
            self.share_timeout = self.MAX_SHARE_TIMEOUT
        if self.share_timeout > self.MAX_SHARE_TIMEOUT:
            validation_errors.append(
                '[shared] share time out cannot be more than 86400'
                ' seconds (24 hours)'
            )

        return validation_errors


class Settings(object):
    """Robottelo's settings representation."""

    def __init__(self):
        self._all_features = None
        self._configured = False
        self._validation_errors = []
        self.browser = None
        self.cdn = None
        self.locale = None
        self.project = None
        self.reader = None
        self.rhel6_repo = None
        self.rhel7_repo = None
        self.rhel6_os = None
        self.rhel7_os = None
        self.capsule_repo = None
        self.rhscl_repo = None
        self.ansible_repo = None
        self.sattools_repo = None
        self.satmaintenance_repo = None
        self.screenshots_path = None
        self.tmp_dir = None
        self.saucelabs_key = None
        self.saucelabs_user = None
        self.server = ServerSettings()
        self.run_one_datapoint = None
        self.upstream = None
        self.verbosity = None
        self.webdriver = None
        self.webdriver_binary = None
        self.webdriver_desired_capabilities = None
        self.command_executor = None

        self.bugzilla = BugzillaSettings()
        # Features
        self.capsule = CapsuleSettings()
        self.certs = CertsSettings()
        self.clients = ClientsSettings()
        self.compute_resources = LibvirtHostSettings()
        self.discovery = DiscoveryISOSettings()
        self.distro = DistroSettings()
        self.docker = DockerSettings()
        self.ec2 = EC2Settings()
        self.fake_capsules = FakeCapsuleSettings()
        self.fake_manifest = FakeManifestSettings()
        self.ldap = LDAPSettings()
        self.ipa = LDAPIPASettings()
        self.oscap = OscapSettings()
        self.ostree = OstreeSettings()
        self.osp = OSPSettings()
        self.performance = PerformanceSettings()
        self.rhai = RHAISettings()
        self.rhev = RHEVSettings()
        self.ssh_client = SSHClientSettings()
        self.shared_function = SharedFunctionSettings()
        self.vlan_networking = VlanNetworkSettings()
        self.upgrade = UpgradeSettings()
        self.vmware = VmWareSettings()

    def configure(self):
        """Read the settings file and parse the configuration.

        :raises: ImproperlyConfigured if any issue is found during the parsing
            or validation of the configuration.
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
        self._validation_errors.extend(
            self._validate_robottelo_settings())

        attrs = map(
            lambda attr_name: (attr_name, getattr(self, attr_name)),
            dir(self)
        )
        feature_settings = filter(
            lambda tpl: isinstance(tpl[1], FeatureSettings),
            attrs
        )
        for name, settings in feature_settings:
            if self.reader.has_section(name) or name == 'server':
                settings.read(self.reader)
                self._validation_errors.extend(settings.validate())

        if self._validation_errors:
            raise ImproperlyConfigured(
                'Failed to validate the configuration, check the message(s):\n'
                '{}'.format('\n'.join(self._validation_errors))
            )

        self._configure_logging()
        self._configure_third_party_logging()
        self._configure_entities()
        self._configure_airgun()
        self._configured = True

    def _read_robottelo_settings(self):
        """Read Robottelo's general settings."""
        self.log_driver_commands = self.reader.get(
            'robottelo',
            'log_driver_commands',
            ['newSession',
             'windowMaximize',
             'get',
             'findElement',
             'sendKeysToElement',
             'clickElement',
             'mouseMoveTo'],
            list
        )
        self.browser = self.reader.get(
            'robottelo', 'browser', 'selenium')
        self.cdn = self.reader.get('robottelo', 'cdn', True, bool)
        self.locale = self.reader.get('robottelo', 'locale', 'en_US.UTF-8')
        self.project = self.reader.get('robottelo', 'project', 'sat')
        self.rhel6_repo = self.reader.get('robottelo', 'rhel6_repo', None)
        self.rhel7_repo = self.reader.get('robottelo', 'rhel7_repo', None)
        self.rhel6_os = self.reader.get('robottelo', 'rhel6_os', None)
        self.rhel7_os = self.reader.get('robottelo', 'rhel7_os', None)
        self.capsule_repo = self.reader.get('robottelo', 'capsule_repo', None)
        self.rhscl_repo = self.reader.get('robottelo', 'rhscl_repo', None)
        self.ansible_repo = self.reader.get('robottelo', 'ansible_repo', None)
        self.sattools_repo = self.reader.get(
            'robottelo', 'sattools_repo', None, dict)
        self.satmaintenance_repo = self.reader.get(
            'robottelo', 'satmaintenance_repo', None)
        self.screenshots_path = self.reader.get(
            'robottelo', 'screenshots_path', '/tmp/robottelo/screenshots')
        self.tmp_dir = self.reader.get('robottelo', 'tmp_dir', '/var/tmp')
        self.run_one_datapoint = self.reader.get(
            'robottelo', 'run_one_datapoint', False, bool)
        self.cleanup = self.reader.get('robottelo', 'cleanup', False, bool)
        self.upstream = self.reader.get('robottelo', 'upstream', True, bool)
        self.verbosity = self.reader.get(
            'robottelo',
            'verbosity',
            INIReader.cast_logging_level('debug'),
            INIReader.cast_logging_level
        )
        self.webdriver = self.reader.get(
            'robottelo', 'webdriver', 'chrome')
        self.saucelabs_user = self.reader.get(
            'robottelo', 'saucelabs_user', None)
        self.saucelabs_key = self.reader.get(
            'robottelo', 'saucelabs_key', None)
        self.webdriver_binary = self.reader.get(
            'robottelo', 'webdriver_binary', None)
        self.webdriver_desired_capabilities = self.reader.get(
            'robottelo',
            'webdriver_desired_capabilities',
            None,
            cast=INIReader.cast_webdriver_desired_capabilities
        )
        self.command_executor = self.reader.get(
            'robottelo', 'command_executor', 'http://127.0.0.1:4444/wd/hub')
        self.window_manager_command = self.reader.get(
            'robottelo', 'window_manager_command', None)

    def _validate_robottelo_settings(self):
        """Validate Robottelo's general settings."""
        validation_errors = []
        browsers = ('selenium', 'docker', 'saucelabs')
        webdrivers = ('chrome', 'edge', 'firefox', 'ie', 'phantomjs', 'remote')
        if self.browser not in browsers:
            validation_errors.append(
                '[robottelo] browser should be one of {0}.'
                .format(', '.join(browsers))
            )
        if self.webdriver not in webdrivers:
            validation_errors.append(
                '[robottelo] webdriver should be one of {0}.'
                .format(', '.join(webdrivers))
            )
        if self.browser == 'saucelabs':
            if self.saucelabs_user is None:
                validation_errors.append(
                    '[robottelo] saucelabs_user must be provided when '
                    'browser is saucelabs.'
                )
            if self.saucelabs_key is None:
                validation_errors.append(
                    '[robottelo] saucelabs_key must be provided when '
                    'browser is saucelabs.'
                )
        return validation_errors

    @property
    def configured(self):
        """Returns True if the settings have already been configured."""
        return self._configured

    @property
    def all_features(self):
        """List all expected feature settings sections."""
        if self._all_features is None:
            self._all_features = [
                name for name, value in vars(self).items()
                if isinstance(value, FeatureSettings)
            ]
        return self._all_features

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
            self._fields['content'].default = os.path.join(
                get_project_root(),
                'tests', 'foreman', 'data', 'valid_gpg_key.txt'
            )
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

    def _configure_airgun(self):
        """Pass required settings to AirGun"""
        airgun.settings.configure({
            'airgun': {
                'verbosity': logging.getLevelName(self.verbosity),
                'tmp_dir': self.tmp_dir,
            },
            'satellite': {
                'hostname': self.server.hostname,
                'password': self.server.admin_password,
                'username': self.server.admin_username,
            },
            'selenium': {
                'browser': self.browser,
                'saucelabs_key': self.saucelabs_key,
                'saucelabs_user': self.saucelabs_user,
                'screenshots_path': self.screenshots_path,
                'webdriver': self.webdriver,
                'webdriver_binary': self.webdriver_binary,
            },
            'webdriver_desired_capabilities': (
                self.webdriver_desired_capabilities or {}),
        })

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
            logging.config.fileConfig(logging_conf_path)
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
            'requests.packages.urllib3.connectionpool',
            'selenium.webdriver.remote.remote_connection',
        )
        for logger in loggers:
            logging.getLogger(logger).setLevel(logging.WARNING)
