"""Usage: python scripts/validate_config.py"""
from distutils.log import error
from dynaconf.validator import ValidationError

try:
    from robottelo.config import settings
except Exception as err:
    print(f"Encountered the following exception, continuing for the sake of validation\n {err}")

    from dynaconf import LazySettings
    from robottelo.config.validators import VALIDATORS
    settings = LazySettings(
        envvar_prefix="ROBOTTELO",
        core_loaders=["YAML"],
        settings_file="settings.yaml",
        preload=["conf/*.yaml"],
        includes=["settings.local.yaml", ".secrets.yaml", ".secrets_*.yaml"],
        envless_mode=True,
        lowercase_read=True,
    )

    settings.validators.register(**VALIDATORS)

def binary_validation(validators):
    settings.validators.clear()
    settings.validators.extend(validators)
    try:
        settings.validators.validate()
    except (ValidationError, AttributeError) as err:
        if len(validators) == 1:
            if isinstance(err, AttributeError):
                print(f"validator={validators[0].names}:\n    {err}")
                #breakpoint();
            else:
                print(err)
        else:
            left, right = (
                validators[: len(validators) // 2],
                validators[len(validators) // 2 :],  # noqa: E203
            )
            binary_validation(left)
            binary_validation(right)


binary_validation(settings.validators[:])
