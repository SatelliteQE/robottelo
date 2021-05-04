import logging
import os
from pathlib import Path

from dynaconf import LazySettings
from dynaconf.validator import ValidationError

from .validators import validators as dynaconf_validators
from robottelo.config.base import ImproperlyConfigured
from robottelo.config.base import Settings as LegacySettings
from robottelo.config.facade import SettingsFacade
from robottelo.config.facade import SettingsNodeWrapper

logger = logging.getLogger('robottelo.config')

if not os.getenv('ROBOTTELO_DIR'):
    # dynaconf robottelo file uses ROBOTELLO_DIR for screenshots
    os.environ['ROBOTTELO_DIR'] = str(Path(__file__).resolve().parent.parent)

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
        "Legacy Robottelo settings configure() failed, most likely required "
        "configuration option is not provided. Continuing for the sake of unit tests"
    )

try:
    dynaconf_settings.validators.validate()
except ValidationError:
    logger.warning("Dynaconf validation failed, continuing for the sake of unit tests")

settings_proxy = SettingsFacade()
settings_proxy.set_configs(dynaconf_settings, legacy_settings)

settings = SettingsNodeWrapper(settings_proxy)
settings.configure_nailgun()
settings.configure_airgun()
settings.configure_logging()
settings.configure_third_party_logging()


def setting_is_set(option):
    """Return either ``True`` or ``False`` if a Robottelo section setting is
    set or not respectively.
    """
    if not settings.configured:
        settings.configure()
    # Example: `settings.clients`
    if getattr(settings, option).validate():
        return False
    return True
