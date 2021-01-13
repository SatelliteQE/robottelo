import logging
import os
from functools import reduce
from urllib.parse import urljoin
from urllib.parse import urlunsplit

from wrapt import CallableObjectProxy

from robottelo.config.base import get_project_root
from robottelo.config.base import INIReader
from robottelo.config.base import SETTINGS_FILE_NAME

logger = logging.getLogger('robottelo.config.facade')

WRAPPER_EXCEPTIONS = (
    'server.hostname',
    'server.ssh_key',
    'server.ssh_password',
    'server.port',
    'server.scheme',
    'server.admin_username',
    'server.admin_password',
    'azurerm.azure_region',
    'azurerm.client_id',
    'azurerm.client_secret',
    'azurerm.password',
    'azurerm.ssh_pub_key',
    'azurerm.subscription_id',
    'azurerm.tenant_id',
    'azurerm.username',
    'clients.provisioning_server',
    'compute_resources.libvirt_hostname',
    'container_repo.long_pass_registry',
    'container_repo.multi_registry_test_configs',
    'docker.private_registry_name',
    'docker.private_registry_password',
    'docker.private_registry_url',
    'docker.private_registry_username',
    'fake_capsules.port_range',
    'gce.cert_path',
    'gce.cert_path',
    'gce.cert_url',
    'gce.client_email',
    'gce.client_email',
    'gce.project_id',
    'gce.project_id',
    'gce.zone',
    'gce.zone',
    'http_proxy.auth_proxy_url',
    'http_proxy.password',
    'http_proxy.username',
    'ipa.basedn_ipa',
    'ipa.grpbasedn_ipa',
    'ipa.hostname_ipa',
    'ipa.password_ipa',
    'ipa.user_ipa',
    'ipa.username_ipa',
    'ipa.group_users',
    'ipa.groups',
    'ldap.basedn',
    'ldap.grpbasedn',
    'ldap.hostname',
    'ldap.password',
    'ldap.username',
    'open_ldap.username',
    'open_ldap.password',
    'open_ldap.base_dn',
    'open_ldap.hostname',
    'open_ldap.group_base_dn',
    'open_ldap.open_ldap_user',
    'rhel7_os',
    'rhel8_os',
    'rhsso.rhsso_user',
    'rhsso.password',
    'sattools_repo',
    'swid_tools_repo',
    'vlan_networking.netmask',
    'vlan_networking.subnet',
    'vmware.vcenter',
)


class SettingsNodeWrapper(CallableObjectProxy):
    def __init__(self, wrapped, config_provider=None, full_path=None):
        super().__init__(wrapped)
        if config_provider is None:
            config_provider = wrapped
        self._self_config_provider = config_provider
        self._self_full_path = full_path

    def __getattr__(self, name):
        new_path = name
        if self._self_full_path:
            new_path = f"{self._self_full_path}.{name}"
        config_value = self._self_config_provider.get(new_path)
        if new_path in WRAPPER_EXCEPTIONS:
            logger.debug(
                f"Found '{new_path}' in exceptions list - will not wrap in SettingsNodeWrapper"
            )
            return config_value
        return SettingsNodeWrapper(config_value, self._self_config_provider, new_path)

    def __dir__(self):
        if self._self_full_path is None:
            return dir(self._self_config_provider)
        else:
            return dir(self.__wrapped__)

    def __fspath__(self):
        return str(self.__wrapped__)

    def __repr__(self):
        return '<{} for "{}" wrapping value of type {}: {}>'.format(
            type(self).__name__,
            self._self_full_path,
            type(self.__wrapped__).__name__,
            self.__wrapped__,
        )


class SettingsFacade:
    _cache = {}
    _configs = []

    @classmethod
    def set_configs(cls, *configs):
        cls._configs = configs

    @classmethod
    def _from_cache(cls, key):
        value = cls._cache[key]
        logger.debug(f"returning '{key}' from cache")
        return value

    @classmethod
    def _add_to_cache(cls, key, value):
        cls._cache[key] = value

    @staticmethod
    def _cached_function(fn):
        computed_value = fn()

        def inner(*args, **kwargs):
            return computed_value

        return inner

    def __all_features(self):
        return [name for name in dir(self) if not name.startswith("_")]

    def __server_get_credentials(self):
        """Return credentials for interacting with a Foreman deployment API.

        :return: A username-password pair.
        :rtype: tuple

        """
        username = self.get('server.admin_username')
        password = self.get('server.admin_password')
        return (username, password)

    def __server_get_url(self):
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
        scheme = self.get('server.scheme')
        hostname = self.get('server.hostname')
        port = self.get('server.port')
        if port is not None:
            hostname = f"{hostname}:{port}"

        return urlunsplit((scheme, hostname, '', '', ''))

    def __server_get_pub_url(self):
        """Return the pub URL of the server being tested.

        The following values from the config file are used to build the URL:

        * ``main.server.hostname`` (required)

        :return: The pub directory URL.
        :rtype: str

        """
        hostname = self.get('server.hostname')
        return urlunsplit(('http', hostname, 'pub/', '', ''))

    def __server_get_cert_rpm_url(self):
        """Return the Katello cert RPM URL of the server being tested.

        The following values from the config file are used to build the URL:

        * ``main.server.hostname`` (required)

        :return: The Katello cert RPM URL.
        :rtype: str

        """
        get_pub_url = self.get('server.get_pub_url')
        return urljoin(get_pub_url(), 'katello-ca-consumer-latest.noarch.rpm')

    def __server_version(self):
        try:
            version = self._get_from_configs('server.version')
        except AttributeError:
            from robottelo.host_info import get_sat_version

            version = get_sat_version()

        return version

    def __server_get_hostname(self, key="hostname"):
        try:
            return self._get_from_configs(f"server.{key}")
        except AttributeError:
            default = self._get_from_configs("server.hostname")
            reader = INIReader(os.path.join(get_project_root(), SETTINGS_FILE_NAME))
            return reader.get('server', key, default)

    def __capsule_hostname(self):
        try:
            instance_name = self.get('capsule.instance_name')
            domain = self.get('capsule.domain')
            return f"{instance_name}.{domain}"
        except KeyError:
            return None

    def __ssh_client_command_timeout(self):
        try:
            timeout = self._get_from_configs('ssh_client.command_timeout')
        except AttributeError:
            timeout = 300
        return timeout

    def __ssh_client_connection_timeout(self):
        try:
            timeout = self._get_from_configs('ssh_client.connection_timeout')
        except AttributeError:
            timeout = 10
        return timeout

    def _dispatch_computed_value(self, key):
        if key == "configure":
            value = self._cached_function(lambda: None)
        elif key == "server.get_credentials":
            value = self._cached_function(self.__server_get_credentials)
        elif key == "server.get_url":
            value = self._cached_function(self.__server_get_url)
        elif key == "server.get_pub_url":
            value = self._cached_function(self.__server_get_pub_url)
        elif key == "server.get_cert_rpm_url":
            value = self._cached_function(self.__server_get_cert_rpm_url)
        elif key == 'server.get_hostname':
            value = self.__server_get_hostname
        elif key == "server.version":
            value = self.__server_version()
        elif key == "capsule.hostname":
            value = self.__capsule_hostname()
        elif key == "ssh_client.command_timeout":
            value = self.__ssh_client_command_timeout()
        elif key == "ssh_client.connection_timeout":
            value = self.__ssh_client_connection_timeout()
        elif key == "configured":
            value = True
        elif key == "all_features":
            value = self.__all_features()
        else:
            raise KeyError()
        self._add_to_cache(key, value)
        return value

    def _get_from_configs(self, key):
        for config_provider in self._configs:
            try:
                real_value = reduce(getattr, key.split('.'), config_provider)
                logger.debug(
                    f"obtained '{key}' from '{type(config_provider).__name__}' = {real_value}"
                )
                break
            except AttributeError:
                pass
        else:
            logger.debug(f"failed to find '{key}' in configuration")
            msg = f"None of configuration providers has attribute '{key}'"
            raise AttributeError(msg)
        self._add_to_cache(key, real_value)
        return real_value

    def get(self, full_path):
        try:
            return self._from_cache(full_path)
        except KeyError:
            pass

        try:
            return self._dispatch_computed_value(full_path)
        except KeyError:
            pass

        value = self._get_from_configs(full_path)
        return value

    def __dir__(self):
        all_keys = []
        for config in self._configs:
            try:
                keys = config.keys()
            except AttributeError:
                keys = config.__dict__.keys()
            all_keys.extend(keys)
        return tuple(all_keys)
