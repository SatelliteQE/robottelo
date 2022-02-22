"""Usage: python scripts/validate_config.py"""
from dynaconf.validator import ValidationError

from robottelo.config import settings


def binary_validation(validators):
    settings.validators.clear()
    settings.validators.extend(validators)
    try:
        settings.validators.validate()
    except ValidationError as err:
        if len(validators) == 1:
            print(err)
        else:
            left, right = (
                validators[: len(validators) // 2],
                validators[len(validators) // 2 :],  # noqa: E203
            )
            binary_validation(left)
            binary_validation(right)


binary_validation(settings.validators[:])
