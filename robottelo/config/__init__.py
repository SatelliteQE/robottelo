from dynaconf import LazySettings

from .validators import validators
from robottelo.config.base import Settings as LegacySettings


legacy_settings = LegacySettings()


settings = LazySettings(
    envvar_prefix="SATQE",
    core_loaders=["YAML"],
    settings_file="settings.yaml",
    preload=["conf/*.yaml", "settings_*.yaml"],
    includes=["settings.local.yaml", ".secrets.yaml", ".secrets_*.yaml"],
    envless_mode=True,
    lowercase_read=True,
)

settings.validators.register(**validators)
settings.validators.validate()
