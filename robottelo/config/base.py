"""Define and instantiate the configuration class for Robottelo."""
import importlib
import os
from configparser import ConfigParser
from configparser import NoOptionError
from configparser import NoSectionError

import yaml

from robottelo.config import casts
from robottelo.constants import AZURERM_VALID_REGIONS
from robottelo.constants import VALID_GCE_ZONES
from robottelo.errors import ImproperlyConfigured


SETTINGS_FILE_NAME = 'robottelo.properties'


class INIReader:
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
            self.config_parser.read_file(handler)

    def get(self, section, option, default=None, cast=None):
        """Read an option from a section of a INI file.

        First try to lookup for the value as an environment variable having the
        following format: ROBOTTELO_{SECTION}_{OPTION}.

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
        # First try to read from environment variable.
        # [bugzilla]
        # api_key=123456
        # can be expressed as:
        # $ export ROBOTTELO_BUGZILLA_API_KEY=123456
        value = os.environ.get(f'ROBOTTELO_{section.upper()}_{option.upper()}')

        try:
            # If envvar does not exist then try from .properties file.
            value = value or self.config_parser.get(section, option)
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


class FeatureSettings:
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
        """Subclasses must implement this method in order to validate the
        settings and raise ``ImproperlyConfigured`` if any issue is found.
        """
        raise NotImplementedError('Subclasses must implement validate method.')


class ServerSettings(FeatureSettings):
    """Satellite server settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin_password = None
        self.admin_username = None
        self.hostname = None
        self.port = None
        self.scheme = None
        self.ssh_key = None
        self.ssh_key_string = None
        self.ssh_password = None
        self.ssh_username = None
        self._version = None

    def read(self, reader):
        """Read and validate Satellite server settings."""
        self.admin_password = reader.get('server', 'admin_password', 'changeme')
        self.admin_username = reader.get('server', 'admin_username', 'admin')
        self.hostname = reader.get('server', 'hostname')
        self.port = reader.get('server', 'port', cast=int)
        self.scheme = reader.get('server', 'scheme', 'https')
        self.ssh_key = reader.get('server', 'ssh_key')
        self.ssh_key_string = reader.get('sever', 'ssh_key_string')
        self.ssh_password = reader.get('server', 'ssh_password')
        self.ssh_username = reader.get('server', 'ssh_username', 'root')
        self._version = reader.get('server', 'version', None)

    @property
    def version(self):
        # Version is lazily taken from config OR SATELLITE_VERSION env var or SSH.
        if self._version is None:
            # import here to avoid circular import error
            from robottelo.host_info import get_sat_version

            self._version = get_sat_version()
        return self._version

    def validate(self):
        validation_errors = []
        if self.hostname is None:
            validation_errors.append('[server] hostname must be provided.')
        if not any([self.ssh_key, self.ssh_password, self.ssh_key_string]):
            validation_errors.append(
                '[server] ssh_key or ssh_password or ssh_key_string must be provided.'
            )
        return validation_errors

    def get_hostname(self, key="hostname"):
        from robottelo.config import robottelo_root_dir

        reader = INIReader(robottelo_root_dir.joinpath(SETTINGS_FILE_NAME))
        return reader.get('server', key, self.hostname)


class BrokerSettings(FeatureSettings):
    """Broker settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.broker_directory = None

    def read(self, reader):
        """Read and validate broker settings."""
        self.broker_directory = reader.get('broker', 'broker_directory', '.')
        os.environ["BROKER_DIRECTORY"] = self.broker_directory

    def validate(self):
        """This section is lazily validated on .issue_handlers.bugzilla."""
        return []


class BugzillaSettings(FeatureSettings):
    """Bugzilla server settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = None
        self.api_key = None

    def read(self, reader):
        """Read and validate Bugzilla server settings."""
        self.url = reader.get('bugzilla', 'url', 'https://bugzilla.redhat.com')
        self.api_key = reader.get('bugzilla', 'api_key', None)

    def validate(self):
        """This section is lazily validated on .issue_handlers.bugzilla."""
        return []


class CapsuleSettings(FeatureSettings):
    """Clients settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            return f'{self.instance_name}.{self.domain}'

        return None

    def validate(self):
        """Validate capsule settings."""
        validation_errors = []
        if self.instance_name is None:
            validation_errors.append('[capsule] instance_name option must be provided.')
        return validation_errors


class CertsSettings(FeatureSettings):
    """Katello-certs settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            validation_errors.append('[certs] cert_file option must be provided.')
        if self.key_file is None:
            validation_errors.append('[certs] key_file option must be provided.')
        if self.req_file is None:
            validation_errors.append('[certs] req_file option must be provided.')
        if self.ca_bundle_file is None:
            validation_errors.append('[certs] ca_bundle_file option must be provided.')
        return validation_errors


class ClientsSettings(FeatureSettings):
    """Clients settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            validation_errors.append('[clients] provisioning_server option must be provided.')
        return validation_errors


class ContainerRepositorySettings(FeatureSettings):
    """Settings for syncing containers from container registries"""

    section = 'container_repo'

    repo_config_required = [
        'label',
        'registry_url',
        'registry_username',
        'registry_password',
        'repos_to_sync',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_file = None
        self.config = None
        self.multi_registry_test_configs = None
        self.yaml = None
        self.long_pass_registry = None

    def read(self, reader):
        """Read container repo settings and associated yaml file"""
        self.config_file = reader.get(self.section, 'config_file')
        if self.config_file:
            with open(self.config_file) as cf:
                self.yaml = yaml.safe_load(cf)
                self.config = self.yaml.get(self.section, None)
                if self.config:
                    self.long_pass_registry = self.config.get('long_pass_test_registry', None)
                    self.multi_registry_test_configs = self.config.get(
                        'multi_registry_test_configs', None
                    )

    def validate(self):
        validation_errors = []
        if not self.config_file:
            validation_errors.append(f'[{self.section}] config_file must be provided')
        elif not self.config:
            validation_errors.append(f"{self.config_file} contains no {self.section} entry")
        else:
            if not self.long_pass_registry:
                validation_errors.append(f'[{self.section}] contains no long_pass_registry')
            else:
                validation_errors.extend(
                    self._validate_registry_configs([self.long_pass_registry])
                )

            if not self.multi_registry_test_configs:
                validation_errors.append(
                    '[{}] {} contains no multi_registry_test_configs'.format(
                        self.section, self.config_file
                    )
                )
            else:
                validation_errors.extend(
                    self._validate_registry_configs(self.multi_registry_test_configs)
                )

        return validation_errors

    def _validate_registry_configs(self, configs):
        validation_errors = []
        for config in configs:
            for req in self.repo_config_required:
                if not config.get(req):
                    validation_errors.append(f'[{self.section}] {req} is required in {config}')
        return validation_errors


class DistroSettings(FeatureSettings):
    """Distro settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_el6 = None
        self.image_el7 = None
        self.image_el8 = None
        self.image_sles11 = None
        self.image_sles12 = None

    def read(self, reader):
        """Read distro settings."""
        self.image_el6 = reader.get('distro', 'image_el6')
        self.image_el7 = reader.get('distro', 'image_el7')
        self.image_el8 = reader.get('distro', 'image_el8')
        self.image_sles11 = reader.get('distro', 'image_sles11')
        self.image_sles12 = reader.get('distro', 'image_sles12')

    def validate(self):
        """Validate distro settings."""
        validation_errors = []
        if not all(self.__dict__.values()):
            validation_errors.append(
                'All [distro] %s options must be provided.' % list(self.__dict__.keys())
            )
        return validation_errors


class DockerSettings(FeatureSettings):
    """Docker settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.external_registry_1 = None
        self.private_registry_url = None
        self.private_registry_name = None
        self.private_registry_username = None
        self.private_registry_password = None

    def read(self, reader):
        """Read docker settings."""
        self.external_registry_1 = reader.get('docker', 'external_registry_1')
        self.private_registry_url = reader.get('docker', 'private_registry_url')
        self.private_registry_name = reader.get('docker', 'private_registry_name')
        self.private_registry_username = reader.get('docker', 'private_registry_username')
        self.private_registry_password = reader.get('docker', 'private_registry_password')

    def validate(self):
        """Validate docker settings."""
        validation_errors = []
        if not self.external_registry_1:
            validation_errors.append('[docker] external_registry_1 option must be provided.')
        return validation_errors


class AzureRMSettings(FeatureSettings):
    """Azure Resource Manager settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = None
        self.client_secret = None
        self.subscription_id = None
        self.tenant_id = None
        self.azure_region = None
        self.ssh_pub_key = None
        self.username = None
        self.password = None
        self.azure_subnet = None

    def read(self, reader):
        """Read AzureRM settings."""
        self.client_id = reader.get('azurerm', 'client_id')
        self.client_secret = reader.get('azurerm', 'client_secret')
        self.subscription_id = reader.get('azurerm', 'subscription_id')
        self.tenant_id = reader.get('azurerm', 'tenant_id')
        self.azure_region = reader.get('azurerm', 'azure_region')
        self.ssh_pub_key = reader.get('azurerm', 'ssh_pub_key')
        self.username = reader.get('azurerm', 'username')
        self.password = reader.get('azurerm', 'password')
        self.azure_subnet = reader.get('azurerm', 'azure_subnet')

    def validate(self):
        """Validate AzureRM settings."""
        validation_errors = []
        if not all(self.__dict__.values()):
            validation_errors.append(
                f'All [azurerm] {self.__dict__.keys()} options must be provided'
            )
        if self.azure_region not in AZURERM_VALID_REGIONS:
            validation_errors.append(
                'Invalid [azurerm] region - {}, The region should be one of {}'.format(
                    self.azure_region, AZURERM_VALID_REGIONS
                )
            )
        return validation_errors


class EC2Settings(FeatureSettings):
    """AWS EC2 settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.security_groups = reader.get('ec2', 'security_groups', ['default'], list)
        self.managed_ip = reader.get('ec2', 'managed_ip', 'Private')

    def validate(self):
        """Validate AWS EC2 settings."""
        validation_errors = []
        if not all((self.access_key, self.secret_key, self.region)):
            validation_errors.append(
                'All [ec2] access_key, secret_key, region options must be provided'
            )
        if self.managed_ip not in ('Private', 'Public'):
            validation_errors.append('[ec2] managed_ip option must be Public or Private')
        return validation_errors


class FakeManifestSettings(FeatureSettings):
    """Fake manifest settings defintitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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


class GCESettings(FeatureSettings):
    """Google Compute Engine settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = None
        self.client_email = None
        self.cert_path = None
        self.zone = None
        self.cert_url = None

    def read(self, reader):
        """Read GCE settings."""
        self.project_id = reader.get('gce', 'project_id')
        self.client_email = reader.get('gce', 'client_email')
        self.cert_path = reader.get('gce', 'cert_path')
        self.zone = reader.get('gce', 'zone')
        self.cert_url = reader.get('gce', 'cert_url')

    def validate(self):
        """Validate GCE settings."""
        valid_cert_path = '/usr/share/foreman/'
        validation_errors = []
        if not all(self.__dict__.values()):
            validation_errors.append(f'All [gce] {self.__dict__.keys()} options must be provided')
        if not str(self.cert_path).startswith(valid_cert_path):
            validation_errors.append(
                '[gce] cert_path - cert should be available '
                'from satellites {}'.format(valid_cert_path)
            )
        if self.zone not in VALID_GCE_ZONES:
            validation_errors.append(
                'Invalid [gce] zone - {}, The zone should be one of {}'.format(
                    self.zone, VALID_GCE_ZONES
                )
            )
        return validation_errors


class RHSSOSettings(FeatureSettings):
    """RHSSO settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host_name = None
        self.host_url = None
        self.rhsso_user = None
        self.password = None
        self.realm = None
        self.totp_secret = None

    def read(self, reader):
        """Read LDAP settings."""
        self.host_name = reader.get('rhsso', 'host_name')
        self.host_url = reader.get('rhsso', 'host_url')
        self.rhsso_user = reader.get('rhsso', 'rhsso_user')
        self.password = reader.get('rhsso', 'user_password')
        self.realm = reader.get('rhsso', 'realm')
        self.totp_secret = reader.get('rhsso', 'totp_secret')

    def validate(self):
        """Validate RHSSO settings."""
        validation_errors = []
        if not all(vars(self).values()):
            validation_errors.append(
                'All [rhsso] host_name, host_url, rhsso_user, password, '
                'realm, totp_secret options must be provided.'
            )
        return validation_errors


class LDAPSettings(FeatureSettings):
    """LDAP settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.basedn = None
        self.grpbasedn = None
        self.hostname = None
        self.nameserver = None
        self.password = None
        self.realm = None
        self.username = None

    def read(self, reader):
        """Read LDAP settings."""
        self.basedn = reader.get('ldap', 'basedn')
        self.grpbasedn = reader.get('ldap', 'grpbasedn')
        self.hostname = reader.get('ldap', 'hostname')
        self.nameserver = reader.get('ldap', 'nameserver')
        self.password = reader.get('ldap', 'password')
        self.realm = reader.get('ldap', 'realm')
        self.username = reader.get('ldap', 'username')

    def validate(self):
        """Validate LDAP settings."""
        validation_errors = []
        if not all(vars(self).values()):
            validation_errors.append(
                'All [ldap] basedn, grpbasedn, hostname, nameserver, password, realm'
                'username options must be provided.'
            )
        return validation_errors


class LDAPIPASettings(FeatureSettings):
    """LDAP freeIPA settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.basedn_ipa = None
        self.grpbasedn_ipa = None
        self.hostname_ipa = None
        self.password_ipa = None
        self.username_ipa = None
        self.user_ipa = None
        self.otp_user = None
        self.time_based_secret = None
        self.disabled_user_ipa = None
        self.group_users = None
        self.groups = None

    def read(self, reader):
        """Read LDAP freeIPA settings."""
        self.basedn_ipa = reader.get('ipa', 'basedn_ipa')
        self.grpbasedn_ipa = reader.get('ipa', 'grpbasedn_ipa')
        self.hostname_ipa = reader.get('ipa', 'hostname_ipa')
        self.password_ipa = reader.get('ipa', 'password_ipa')
        self.username_ipa = reader.get('ipa', 'username_ipa')
        self.user_ipa = reader.get('ipa', 'user_ipa')
        self.otp_user = reader.get('ipa', 'otp_user')
        self.time_based_secret = reader.get('ipa', 'time_based_secret')
        self.disabled_user_ipa = reader.get('ipa', 'disabled_user_ipa')
        self.group_users = reader.get('ipa', 'group_users', cast=list)
        self.groups = reader.get('ipa', 'groups', cast=list)

    def validate(self):
        """Validate LDAP freeIPA settings."""
        validation_errors = []
        if not all(vars(self).values()):
            validation_errors.append(
                'All [ipa] basedn_ipa, grpbasedn_ipa, hostname_ipa,'
                ' password_ipa, username_ipa, user_ipa,'
                ' otp_user, time_based_secret, disabled_user_ipa, '
                'group_users and groups options must be provided.'
            )
        return validation_errors


class OpenLDAPSettings(FeatureSettings):
    """Open LDAP settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_dn = None
        self.group_base_dn = None
        self.hostname = None
        self.password = None
        self.username = None
        self.open_ldap_user = None

    def read(self, reader):
        """Read Open LDAP settings."""
        self.base_dn = reader.get('open_ldap', 'base_dn')
        self.group_base_dn = reader.get('open_ldap', 'group_base_dn')
        self.hostname = reader.get('open_ldap', 'hostname')
        self.password = reader.get('open_ldap', 'password')
        self.username = reader.get('open_ldap', 'username')
        self.open_ldap_user = reader.get('open_ldap', 'open_ldap_user')

    def validate(self):
        """Validate Open LDAP settings."""
        validation_errors = []
        if not all(vars(self).values()):
            validation_errors.append(
                'All [open_ldap] base_dn, group_base_dn, hostname, password, '
                'username, open_ldap_user options must be provided.'
            )
        return validation_errors


class LibvirtHostSettings(FeatureSettings):
    """Libvirt host settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.libvirt_image_dir = None
        self.libvirt_hostname = None

    def read(self, reader):
        """Read libvirt host settings."""
        self.libvirt_image_dir = reader.get(
            'compute_resources', 'libvirt_image_dir', '/var/lib/libvirt/images'
        )
        self.libvirt_hostname = reader.get('compute_resources', 'libvirt_hostname')

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
        super().__init__(*args, **kwargs)
        self.port_range = None

    def read(self, reader):
        """Read fake capsule settings"""
        self.port_range = reader.get('fake_capsules', 'port_range', cast=tuple)

    def validate(self):
        """Validate fake capsule settings."""
        validation_errors = []
        if self.port_range is None:
            validation_errors.append('[fake_capsules] port_range option must be provided.')
        return validation_errors


class RHEVSettings(FeatureSettings):
    """RHEV settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.image_uuid = None
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
        self.image_uuid = reader.get('rhev', 'image_uuid', None)
        self.ca_cert = reader.get('rhev', 'ca_cert', None)

    def validate(self):
        """Validate rhev settings."""
        validation_errors = []
        values = [v for k, v in vars(self).items() if k not in ['ca_cert', 'image_uuid']]
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
        super().__init__(*args, **kwargs)
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
        super().__init__(*args, **kwargs)
        self.discovery_iso = None

    def read(self, reader):
        """Read discovery iso setting."""
        self.discovery_iso = reader.get('discovery', 'discovery_iso')

    def validate(self):
        """Validate discovery iso name setting."""
        validation_errors = []
        if self.discovery_iso is None:
            validation_errors.append('[discovery] discovery iso name must be provided.')
        return validation_errors


class OscapSettings(FeatureSettings):
    """Oscap settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            validation_errors.append('[oscap] content_path option must be provided.')
        if self.tailoring_path is None:
            validation_errors.append('[oscap] tailoring_path option must be provided.')
        return validation_errors


class OSPSettings(FeatureSettings):
    """OSP settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Compute Resource Information
        self.hostname = None
        self.username = None
        self.password = None
        self.tenant = None
        self.project_domain_id = None
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
        self.project_domain_id = reader.get('osp', 'project_domain_id')
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
                'security_group, project_domain_id options must be provided.'
            )
        return validation_errors


class PerformanceSettings(FeatureSettings):
    """Performance settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.time_hammer = reader.get('performance', 'time_hammer', False, bool)
        self.cdn_address = reader.get('performance', 'cdn_address')
        self.virtual_machines = reader.get('performance', 'virtual_machines', cast=list)
        self.fresh_install_savepoint = reader.get('performance', 'fresh_install_savepoint')
        self.enabled_repos_savepoint = reader.get('performance', 'enabled_repos_savepoint')
        self.csv_buckets_count = reader.get('performance', 'csv_buckets_count', 10, int)
        self.sync_count = reader.get('performance', 'sync_count', 3, int)
        self.sync_type = reader.get('performance', 'sync_type', 'sync')
        self.repos = reader.get('performance', 'repos', cast=list)

    def validate(self):
        """Validate performance settings."""
        validation_errors = []
        if self.cdn_address is None:
            validation_errors.append('[performance] cdn_address must be provided.')
        if self.virtual_machines is None:
            validation_errors.append('[performance] virtual_machines must be provided.')
        if self.fresh_install_savepoint is None:
            validation_errors.append('[performance] fresh_install_savepoint must be provided.')
        if self.enabled_repos_savepoint is None:
            validation_errors.append('[performance] enabled_repos_savepoint must be provided.')
        return validation_errors


class SSHClientSettings(FeatureSettings):
    """SSHClient settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._command_timeout = None
        self._connection_timeout = None

    @property
    def command_timeout(self):
        return self._command_timeout if (self._command_timeout is not None) else 300

    @property
    def connection_timeout(self):
        return self._connection_timeout if (self._connection_timeout is not None) else 10

    def read(self, reader):
        """Read SSHClient settings."""
        self._command_timeout = reader.get('ssh_client', 'command_timeout', default=300, cast=int)
        self._connection_timeout = reader.get(
            'ssh_client', 'connection_timeout', default=10, cast=int
        )

    def validate(self):
        """Validate SSHClient settings."""
        return []


class VlanNetworkSettings(FeatureSettings):
    """Vlan Network settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subnet = None
        self.netmask = None
        self.gateway = None
        self.bridge = None
        self.network = None
        self.dhcp_ipam = None
        self.dhcp_from = None
        self.dhcp_to = None
        self.dns_primary = None
        self.dns_zone = None

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
        self.dns_zone = reader.get('vlan_networking', 'dns_zone')

    def validate(self):
        """Validate Vlan Network settings."""
        validation_errors = []
        if bool(self.bridge) == bool(self.network):
            validation_errors.append(
                'exactly one of the "bridge" or "network" parameters must be specified'
            )
        if bool(self.dhcp_from) != bool(self.dhcp_to):
            validation_errors.append(
                'both or none of "dhcp_from", "dhcp_to" parameters must be specified'
            )
        if self.dhcp_ipam and self.dhcp_ipam not in ['Internal DB', 'DHCP']:
            validation_errors.append(
                '[vlan_networking] "dhcp_ipam" must be one of "Internal DB" or "DHCP"'
            )
        ignored = [
            'bridge',
            'network',
            'dhcp_ipam',
            'dhcp_from',
            'dhcp_to',
            'dns_primary',
            'dns_zone',
        ]
        if not all(value for (key, value) in vars(self).items() if key not in ignored):
            validation_errors.append(
                'All [vlan_networking] subnet, netmask, gateway, bridge|network '
                'options must be provided.'
            )
        return validation_errors


class UpgradeSettings(FeatureSettings):
    """Satellite upgrade settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rhev_cap_host = None
        self.capsule_hostname = None
        self.rhev_capsule_ak = None
        self.capsule_ak = None
        self.to_version = None
        self.from_version = None
        self.docker_vm = None
        self.vm_domain = None

    def read(self, reader):
        """Read and validate Satellite server settings."""
        self.rhev_cap_host = reader.get('upgrade', 'rhev_cap_host')
        self.capsule_hostname = reader.get('upgrade', 'capsule_hostname')
        self.rhev_capsule_ak = reader.get('upgrade', 'rhev_capsule_ak')
        self.capsule_ak = reader.get('upgrade', 'capsule_ak')
        self.to_version = reader.get('upgrade', 'to_version')
        self.from_version = reader.get('upgrade', 'from_version')
        self.docker_vm = reader.get('upgrade', 'docker_vm')
        self.vm_domain = reader.get('upgrade', 'vm_domain')

    def validate(self):
        validation_errors = []
        if self.rhev_cap_host and self.capsule_hostname:
            validation_errors.append('Provide either rhev_cap_host or capsule_hostname, not both')
        if self.rhev_capsule_ak and self.capsule_ak:
            validation_errors.append('Provide either rhev_capsule_ak or capsule_ak, not both')
        return validation_errors


class SharedFunctionSettings(FeatureSettings):
    """Shared function settings definitions."""

    MAX_SHARE_TIMEOUT = 86400

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.enabled = reader.get('shared_function', 'enabled', False, bool)
        self.lock_timeout = reader.get('shared_function', 'lock_timeout', 7200, int)
        self.share_timeout = reader.get(
            'shared_function', 'share_timeout', self.MAX_SHARE_TIMEOUT, int
        )
        self.redis_host = reader.get('shared_function', 'redis_host', 'localhost')
        self.redis_port = reader.get('shared_function', 'redis_port', 6379, int)
        self.redis_db = reader.get('shared_function', 'redis_db', 0, int)
        self.redis_password = reader.get('shared_function', 'redis_password', None)
        self.call_retries = reader.get('shared_function', 'call_retries', 2, int)

    def validate(self):
        """Validate the shared settings"""
        validation_errors = []
        supported_storage_handlers = ['file', 'redis']
        if self.storage not in supported_storage_handlers:
            validation_errors.append(
                f'[shared] storage must be one of {supported_storage_handlers}'
            )
        if self.storage == 'redis':
            try:
                importlib.import_module('redis')
            except ImportError:
                validation_errors.append('[shared] python redis package not installed')
        if self.share_timeout is None:
            self.share_timeout = self.MAX_SHARE_TIMEOUT
        if self.share_timeout > self.MAX_SHARE_TIMEOUT:
            validation_errors.append(
                '[shared] share time out cannot be more than 86400 seconds (24 hours)'
            )

        return validation_errors


class VirtWhoSettings(FeatureSettings):
    """VirtWho settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hypervisor Information
        self.hypervisor_type = None
        self.hypervisor_server = None
        self.hypervisor_username = None
        self.hypervisor_password = None
        self.hypervisor_config_file = None
        self.guest = None
        self.guest_port = None
        self.guest_username = None
        self.guest_password = None
        # SKU Information
        self.sku_vdc_physical = None
        self.sku_vdc_virtual = None

    def read(self, reader):
        """Read virtwho settings."""
        # Hypervisor Information
        self.hypervisor_type = reader.get('virtwho', 'hypervisor_type')
        self.hypervisor_server = reader.get('virtwho', 'hypervisor_server')
        self.hypervisor_username = reader.get('virtwho', 'hypervisor_username')
        self.hypervisor_password = reader.get('virtwho', 'hypervisor_password')
        self.hypervisor_config_file = reader.get('virtwho', 'hypervisor_config_file')
        self.guest = reader.get('virtwho', 'guest')
        self.guest_port = reader.get('virtwho', 'guest_port', 22, int)
        self.guest_username = reader.get('virtwho', 'guest_username')
        self.guest_password = reader.get('virtwho', 'guest_password')
        # SKU Information
        self.sku_vdc_physical = reader.get('virtwho', 'sku_vdc_physical')
        self.sku_vdc_virtual = reader.get('virtwho', 'sku_vdc_virtual')

    def validate(self):
        """Validate virtwho settings."""
        validation_errors = []
        mandatory = (
            self.hypervisor_type,
            self.hypervisor_server,
            self.guest,
            self.guest_username,
            self.guest_password,
            self.sku_vdc_physical,
            self.sku_vdc_virtual,
        )
        if not all(mandatory):
            validation_errors.append(
                '[virtwho] hypervisor_type, hypervisor_server, guest, '
                'guest_username, guest_password, sku_vdc_physical, '
                'sku_vdc_virtual options must be provided.'
            )
        supported_hypervisors = ('esx', 'xen', 'hyperv', 'rhevm', 'libvirt', 'kubevirt')
        if self.hypervisor_type not in supported_hypervisors:
            validation_errors.append(
                f'[virtwho] hypervisor_type must be one of {supported_hypervisors}'
            )
        if self.hypervisor_type == 'kubevirt' and self.hypervisor_config_file is None:
            validation_errors.append(
                '[virtwho] hypervisor_config_file must be provided for kubevirt type.'
            )
        if self.hypervisor_type == 'libvirt' and self.hypervisor_username is None:
            validation_errors.append(
                '[virtwho] hypervisor_username must be provided for libvirt type'
            )
        if self.hypervisor_type in ('esx', 'xen', 'hyperv', 'rhevm') and (
            self.hypervisor_username is None or self.hypervisor_password is None
        ):
            validation_errors.append(
                '[virtwho] hypervisor_username and hypervisor_password '
                'must be provided for esx, xen, hyperv, rhevm'
            )
        return validation_errors


class ReportPortalSettings(FeatureSettings):
    """Report portal settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rp_url = None
        self.rp_project = None
        self.rp_key = None
        self.fail_threshold = None

    def read(self, reader):
        """Read Report portal settings."""
        self.rp_url = reader.get('report_portal', 'portal_url')
        self.rp_project = reader.get('report_portal', 'project')
        self.rp_key = reader.get('report_portal', 'api_key')
        self.fail_threshold = reader.get('report_portal', 'fail_threshold', 20, int)

    def validate(self):
        """Validate Report portal settings."""
        validation_errors = []
        if not all([self.rp_key, self.rp_project, self.rp_url]):
            validation_errors.append(
                'All [report_portal] options must be provided, except fail_threshold'
            )
        return validation_errors


class Settings:
    """Robottelo's settings representation."""

    def __init__(self):
        self._all_features = None
        self._configured = False
        self._validation_errors = []
        self.browser = None
        self.cdn = None
        self.locale = None
        self.reader = None
        self.rhel6_repo = None
        self.rhel7_repo = None
        self.rhel8_repo = None
        self.rhel6_os = None
        self.rhel7_os = None
        self.rhel8_os = None
        self.rhel7_optional = None
        self.rhel7_extras = None
        self.capsule_repo = None
        self.rhscl_repo = None
        self.ansible_repo = None
        self.sattools_repo = None
        self.satmaintenance_repo = None
        self.swid_tools_repo = None
        self.screenshots_path = None
        self.tmp_dir = None
        self.artifacts_server = None
        self.saucelabs_key = None
        self.saucelabs_user = None
        self.server = ServerSettings()
        self.run_one_datapoint = None
        self.upstream = None
        self.verbosity = None
        self.webdriver = None
        self.webdriver_binary = None
        self.browseroptions = None
        self.webdriver_desired_capabilities = None
        self.command_executor = None
        self.repos_hosting_url = None

        self.broker = BrokerSettings()
        self.bugzilla = BugzillaSettings()
        # Features
        self.azurerm = AzureRMSettings()
        self.capsule = CapsuleSettings()
        self.certs = CertsSettings()
        self.clients = ClientsSettings()
        self.compute_resources = LibvirtHostSettings()
        self.container_repo = ContainerRepositorySettings()
        self.discovery = DiscoveryISOSettings()
        self.distro = DistroSettings()
        self.docker = DockerSettings()
        self.ec2 = EC2Settings()
        self.fake_capsules = FakeCapsuleSettings()
        self.fake_manifest = FakeManifestSettings()
        self.gce = GCESettings()
        self.ldap = LDAPSettings()
        self.ipa = LDAPIPASettings()
        self.open_ldap = OpenLDAPSettings()
        self.oscap = OscapSettings()
        self.osp = OSPSettings()
        self.performance = PerformanceSettings()
        self.rhev = RHEVSettings()
        self.rhsso = RHSSOSettings()
        self.ssh_client = SSHClientSettings()
        self.shared_function = SharedFunctionSettings()
        self.vlan_networking = VlanNetworkSettings()
        self.upgrade = UpgradeSettings()
        self.vmware = VmWareSettings()
        self.virtwho = VirtWhoSettings()
        self.report_portal = ReportPortalSettings()
        self.http_proxy = HttpProxySettings()

    def configure(self, settings_path=None):
        """Read the settings file and parse the configuration.

        :param str settings_path: path to settings file to read. If None, looks in the project
            root for a file named 'robottelo.properties'.

        :raises: ImproperlyConfigured if any issue is found during the parsing
            or validation of the configuration.
        """
        if self.configured:
            # TODO: what to do here, raise and exception, just skip or ...?
            return

        if not settings_path:
            from robottelo.config import robottelo_root_dir

            # Expect the settings file to be on the robottelo project root.
            settings_path = robottelo_root_dir.joinpath(SETTINGS_FILE_NAME)

        if not os.path.isfile(settings_path):
            raise ImproperlyConfigured(f'Not able to find settings file at {settings_path}')

        self.reader = INIReader(settings_path)
        self._read_robottelo_settings()
        self._validation_errors.extend(self._validate_robottelo_settings())

        attrs = map(lambda attr_name: (attr_name, getattr(self, attr_name)), dir(self))
        feature_settings = filter(lambda tpl: isinstance(tpl[1], FeatureSettings), attrs)
        for name, settings in feature_settings:
            if self.reader.has_section(name) or name == 'server':
                settings.read(self.reader)
                self._validation_errors.extend(settings.validate())

        if self._validation_errors:
            raise ImproperlyConfigured(
                'Failed to validate the configuration, check the message(s):\n'
                '{}'.format('\n'.join(self._validation_errors))
            )
        self._configured = True

    def _read_robottelo_settings(self):
        """Read Robottelo's general settings."""
        self.log_driver_commands = self.reader.get(
            'robottelo',
            'log_driver_commands',
            [
                'newSession',
                'windowMaximize',
                'get',
                'findElement',
                'sendKeysToElement',
                'clickElement',
                'mouseMoveTo',
            ],
            list,
        )
        self.browser = self.reader.get('robottelo', 'browser', 'selenium')
        self.cdn = self.reader.get('robottelo', 'cdn', True, bool)
        self.locale = self.reader.get('robottelo', 'locale', 'en_US.UTF-8')
        self.rhel6_repo = self.reader.get('robottelo', 'rhel6_repo', None)
        self.rhel7_repo = self.reader.get('robottelo', 'rhel7_repo', None)
        self.rhel8_repo = self.reader.get('robottelo', 'rhel8_repo', None)
        self.rhel6_os = self.reader.get('robottelo', 'rhel6_os', None)
        self.rhel7_os = self.reader.get('robottelo', 'rhel7_os', None)
        self.rhel8_os = self.reader.get('robottelo', 'rhel8_os', None, dict)
        self.rhel7_optional = self.reader.get('robottelo', 'rhel7_optional', None)
        self.rhel7_extras = self.reader.get('robottelo', 'rhel7_extras', None)
        self.capsule_repo = self.reader.get('robottelo', 'capsule_repo', None)
        self.rhscl_repo = self.reader.get('robottelo', 'rhscl_repo', None)
        self.ansible_repo = self.reader.get('robottelo', 'ansible_repo', None)
        self.sattools_repo = self.reader.get('robottelo', 'sattools_repo', None, dict)
        self.satmaintenance_repo = self.reader.get('robottelo', 'satmaintenance_repo', None)
        self.swid_tools_repo = self.reader.get('robottelo', 'swid_tools_repo', None)
        self.screenshots_path = self.reader.get(
            'robottelo', 'screenshots_path', '/tmp/robottelo/screenshots'
        )
        self.tmp_dir = self.reader.get('robottelo', 'tmp_dir', '/var/tmp')
        self.artifacts_server = self.reader.get('robottelo', 'artifacts_server', None)
        self.run_one_datapoint = self.reader.get('robottelo', 'run_one_datapoint', False, bool)
        self.upstream = self.reader.get('robottelo', 'upstream', True, bool)
        self.verbosity = self.reader.get(
            'robottelo',
            'verbosity',
            INIReader.cast_logging_level('debug'),
            INIReader.cast_logging_level,
        )
        self.webdriver = self.reader.get('robottelo', 'webdriver', 'chrome')
        self.saucelabs_user = self.reader.get('robottelo', 'saucelabs_user', None)
        self.saucelabs_key = self.reader.get('robottelo', 'saucelabs_key', None)
        self.webdriver_binary = self.reader.get('robottelo', 'webdriver_binary', None)
        self.browseroptions = self.reader.get('robottelo', 'browseroptions', None)
        self.webdriver_desired_capabilities = self.reader.get(
            'robottelo',
            'webdriver_desired_capabilities',
            None,
            cast=INIReader.cast_webdriver_desired_capabilities,
        )
        self.command_executor = self.reader.get(
            'robottelo', 'command_executor', 'http://127.0.0.1:4444/wd/hub'
        )
        self.window_manager_command = self.reader.get('robottelo', 'window_manager_command', None)
        self.repos_hosting_url = self.reader.get('robottelo', 'repos_hosting_url', None)

    def _validate_robottelo_settings(self):
        """Validate Robottelo's general settings."""
        validation_errors = []
        browsers = ('selenium', 'docker', 'saucelabs', 'remote')
        webdrivers = ('chrome', 'edge', 'firefox', 'ie', 'phantomjs')
        if self.browser not in browsers:
            validation_errors.append(
                '[robottelo] browser should be one of {}.'.format(', '.join(browsers))
            )
        if self.webdriver not in webdrivers:
            validation_errors.append(
                '[robottelo] webdriver should be one of {}.'.format(', '.join(webdrivers))
            )
        if self.browser == 'saucelabs':
            if self.saucelabs_user is None:
                validation_errors.append(
                    '[robottelo] saucelabs_user must be provided when browser is saucelabs.'
                )
            if self.saucelabs_key is None:
                validation_errors.append(
                    '[robottelo] saucelabs_key must be provided when browser is saucelabs.'
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
                name for name, value in vars(self).items() if isinstance(value, FeatureSettings)
            ]
        return self._all_features


class HttpProxySettings(FeatureSettings):
    """Http Proxy settings definitions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.un_auth_proxy_url = None
        self.auth_proxy_url = None
        self.username = None
        self.password = None

    def read(self, reader):
        """Read Http Proxy settings."""
        self.un_auth_proxy_url = reader.get('http_proxy', 'un_auth_proxy_url')
        self.auth_proxy_url = reader.get('http_proxy', 'auth_proxy_url')
        self.username = reader.get('http_proxy', 'username')
        self.password = reader.get('http_proxy', 'password')

    def validate(self):
        """Validate Http Proxy settings."""
        validation_errors = []
        if not all(self.__dict__.values()):
            validation_errors.append(
                f'All [http_proxy] {self.__dict__.keys()} options must be provided'
            )
        return validation_errors
