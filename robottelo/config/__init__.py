import os

from dynaconf import LazySettings
from dynaconf.validator import ValidationError

from .validators import validators as dynaconf_validators
from robottelo.config.base import Settings as LegacySettings
from robottelo.config.facade import SettingsFacade
from robottelo.config.facade import SettingsNodeWrapper
from robottelo.errors import ImproperlyConfigured
from robottelo.logging import config_logger as logger
from robottelo.logging import robottelo_root_dir


if not os.getenv('ROBOTTELO_DIR'):
    # dynaconf robottelo file uses ROBOTELLO_DIR for screenshots
    os.environ['ROBOTTELO_DIR'] = str(robottelo_root_dir)

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


def setting_is_set(option):
    """Return either ``True`` or ``False`` if a Robottelo section setting is
    set or not respectively.
    """
    if not settings.configured:
        settings.configure()
    # Example: `settings.clients`
    # TODO: Use dynaconf 3.2 selective validation
    # Within the split world of Legacy settings and dynaconf, there is a limitation on validating
    # against the dynaconf settings within the scope of this method, and its use to skip tests.
    # With dynaconf 3.2, selective validation is available, and this is a perfect use for it.
    # Otherwise dynaconf validation is done above when the instance is created
    # Validation misses are allowed while the SettingsFacade still exists, because the opposite
    # configuration provider may have that field and will resolve.
    from dynaconf.utils.boxing import DynaBox

    opt_inst = getattr(settings, option, None)
    if opt_inst is None:
        raise ValueError(f'Setting {option} did not resolve in settings')
    return opt_inst.validate() == [] or isinstance(opt_inst, DynaBox)
