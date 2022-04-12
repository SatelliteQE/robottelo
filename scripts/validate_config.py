"""Usage: python scripts/validate_config.py"""
from dynaconf.validator import ValidationError

from robottelo.config import get_settings

try:
    from robottelo.config import settings
except Exception as err:
    print(f"Encountered the following exception, continuing for the sake of validation\n {err}")

    settings = get_settings()


def binary_validation(validators):
    settings.validators.clear()
    settings.validators.extend(validators)
    try:
        settings.validators.validate()
    except (ValidationError, AttributeError) as err:
        if len(validators) == 1:
            if isinstance(err, AttributeError):
                print(f"validator={validators[0].names}:\n    {err}")
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
