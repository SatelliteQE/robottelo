import logging

from dynaconf import LazySettings
from dynaconf.validator import ValidationError

from .validators import validators as dynaconf_validators
from robottelo.config.base import ImproperlyConfigured
from robottelo.config.base import Settings as LegacySettings
from robottelo.config.facade import SettingsFacade
from robottelo.config.facade import SettingsNodeWrapper

logger = logging.getLogger('robottelo.config')

legacy_settings = LegacySettings()

dynaconf_settings = LazySettings(
    envvar_prefix="ROBOTTELO",
    core_loaders=["YAML"],
    settings_file="settings.yaml",
    preload=["conf/*.yaml"],
    includes=["settings.local.yaml", ".secrets.yaml", ".secrets_*.yaml"],
    envless_mode=True,
    lowercase_read=True,
)
dynaconf_settings.validators.register(**dynaconf_validators)

try:
    legacy_settings.configure()
except ImproperlyConfigured:
    logger.warning(
        (
            "Legacy Robottelo settings configure() failed, most likely required "
            "configuration option is not provided. Continuing for the sake of unit tests"
        ),
        exc_info=True,
    )

try:
    dynaconf_settings.validators.validate()
except ValidationError:
    logger.warning(
        "Dynaconf validation failed, continuing for the sake of unit tests", exc_info=True
    )

settings_proxy = SettingsFacade()
settings_proxy.set_configs(dynaconf_settings, legacy_settings)

settings = SettingsNodeWrapper(settings_proxy)
settings.configure_nailgun()
settings.configure_airgun()
settings.configure_logging()
settings.configure_third_party_logging()
