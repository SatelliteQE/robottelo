import os
from functools import reduce

import airgun.settings
from nailgun import entities
from nailgun import entity_mixins
from nailgun.config import ServerConfig
from wrapt import CallableObjectProxy

from robottelo.config import casts
from robottelo.config.base import INIReader
from robottelo.config.base import SETTINGS_FILE_NAME
from robottelo.logging import config_logger as logger

WRAPPER_EXCEPTIONS = (
    'server.hostname',
    # 'server.hostnames',
    'server.ssh_key',
    'server.ssh_key_string',
    'server.ssh_password',
    'server.port',
    'server.scheme',
    'server.admin_username',
    'server.admin_password',
    'server.inventory_filter',
    'server.deploy_workflow',
    'capsule.deploy_workflow',
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
    'container_repo.registries.redhat.url',
    'container_repo.registries.redhat.username',
    'container_repo.registries.redhat.password',
    'container_repo.registries.redhat.repos_to_sync',
    'container_repo.registries.quay.url',
    'container_repo.registries.quay.username',
    'container_repo.registries.quay.password',
    'container_repo.registries.quay.repos_to_sync',
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
    'http_proxy.un_auth_proxy_url',
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
    'azurerm.client_id',
    'azurerm.client_secret',
    'azurerm.subscription_id',
    'azurerm.tenant_id',
    'azurerm.azure_region',
    'azurerm.ssh_pub_key',
    'azurerm.username',
    'azurerm.password',
    'azurerm.azure_subnet',
    'bugzilla.url',
    'bugzilla.api_key',
    'distro.image_el6',
    'distro.image_el7',
    'distro.image_el8',
    'distro.image_sles11',
    'distro.image_sles12',
    'fake_capsules.port_range',
    'shared_function.storage',
    'shared_function.scope',
    'shared_function.enabled',
    'shared_function.lock_timeout',
    'shared_function.share_timeout',
    'shared_function.redis_host',
    'shared_function.redis_port',
    'shared_function.redis_db',
    'shared_function.redis_password',
    'shared_function.call_retries',
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

    def configure_nailgun(self):
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
        """
        # Calling here instead at top, to fix the circular dependency issue
        # This function should be moved to helpers once we get rid of facade
        from robottelo.helpers import settingsUtils

        entity_mixins.CREATE_MISSING = True
        entity_mixins.DEFAULT_SERVER_CONFIG = ServerConfig(
            settingsUtils.server_url(), settingsUtils.credentials(), verify=False
        )

        gpgkey_init = entities.GPGKey.__init__

        def patched_gpgkey_init(self, server_config=None, **kwargs):
            """Set a default value on the ``content`` field."""
            gpgkey_init(self, server_config, **kwargs)
            from robottelo.config import robottelo_root_dir

            self._fields['content'].default = os.path.join(
                robottelo_root_dir, 'tests', 'foreman', 'data', 'valid_gpg_key.txt'
            )

        entities.GPGKey.__init__ = patched_gpgkey_init

    def configure_airgun(self):
        """Pass required settings to AirGun"""
        import logging

        airgun.settings.configure(
            {
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
                    'screenshots_path': self.screenshots_path,
                    'webdriver': self.webdriver,
                    'webdriver_binary': self.webdriver_binary,
                    'command_executor': self.command_executor,
                },
                'webdriver_desired_capabilities': (self.webdriver_desired_capabilities or {}),
            }
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

    def __server_get_hostname(self, key="hostname"):
        try:
            return self._get_from_configs(f"server.{key}")
        except AttributeError:
            default = self._get_from_configs("server.hostname")
            from robottelo.config import robottelo_root_dir

            reader = INIReader(os.path.join(robottelo_root_dir, SETTINGS_FILE_NAME))
            return reader.get('server', key, default)

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

    def _robottelo_verbosity(self):
        """Casts logging level for robottelo framework,
        for more info refer robottelo.config.casts module
        """
        cast_logging_level = casts.LoggingLevel()
        try:
            verbosity = self._get_from_configs('robottelo.verbosity')
            verbosity = cast_logging_level(verbosity)
        except AttributeError:
            verbosity = cast_logging_level('debug')
        return verbosity

    def _fake_capsules_port_range(self):
        """Casts port ranges for fake capsules of type string into tuple"""
        cast_port_range = casts.Tuple()
        port_range = self._get_from_configs('fake_capsules.port_range')
        port_range = cast_port_range(port_range)
        return port_range

    def _dispatch_computed_value(self, key):
        if key == "configure":
            value = self._cached_function(lambda: None)
        elif key == "verbosity":
            value = self._robottelo_verbosity()
        elif key == 'server.get_hostname':
            value = self.__server_get_hostname
        elif key == "ssh_client.command_timeout":
            value = self.__ssh_client_command_timeout()
        elif key == "ssh_client.connection_timeout":
            value = self.__ssh_client_connection_timeout()
        elif key == "fake_capsules.port_range":
            value = self._fake_capsules_port_range()
        elif key == "configured":
            value = True
        elif key == "all_features":
            value = self.__all_features()
        else:
            raise KeyError()
        self._add_to_cache(key, value)
        return value

    # TO DO: Should be removed when LegacySettings are removed
    def _dispatch_robottelo_value(self, key):
        """Returns robottelo setting with dynaconf object in stead of dynaconf.robottelo object

        e.g `self.verbosity` instead of `self.robottelo.verbosity`
        """
        if hasattr(self._configs[0], 'robottelo'):
            robottelo_keys = [setting.lower() for setting in self._configs[0].robottelo.keys()]
            top_key = key.split('.')[0]
            if top_key in robottelo_keys:
                try:
                    # From DynaConf
                    value = self.get(f'robottelo.{key}')
                except KeyError:
                    # From Legacy Setting
                    value = self.get(key)
            else:
                raise KeyError()
            self._add_to_cache(key, value)
            return value
        else:
            raise KeyError()

    # TO DO: Should be removed when LegacySettings are removed
    def _dispatch_repos_value(self, key):
        """Returns repos setting with dynaconf object in stead of dynaconf.repos object

        e.g `self.capsule_repo` instead of `self.repos.capsule_repo`
        """
        if hasattr(self._configs[0], 'repos'):
            repos_keys = [setting.lower() for setting in self._configs[0].repos.keys()]
            top_key = key.split('.')[0]
            if top_key in repos_keys:
                try:
                    # From DynaConf
                    value = self.get(f'repos.{key}')
                except KeyError:
                    # From Legacy Setting
                    value = self.get(key)
            else:
                raise KeyError()
            self._add_to_cache(key, value)
            return value
        else:
            raise KeyError()

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
            if not key.startswith('_'):
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

        try:
            return self._dispatch_robottelo_value(full_path)
        except KeyError:
            pass

        try:
            return self._dispatch_repos_value(full_path)
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
