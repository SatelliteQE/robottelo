import pytest

from robottelo.config import setting_is_set
from robottelo.config import settings


def pytest_configure(config):
    """Register markers related to testimony tokens"""
    config.addinivalue_line(
        "markers",
        'skip_if_not_set: List settings sections that must be set for the test to run. '
        'If settings are missing, the test is skipped in setup.',
    )


def pytest_runtest_setup(item):
    """Skip in setup if settings mark isn't met

    settings validate method is used, so required fields are checked

    This will be getting updated before too long when dynaconf consolidation happens
    """
    skip_marker = item.get_closest_marker('skip_if_not_set', None)
    if skip_marker and skip_marker.args:
        options_set = set(skip_marker.args)
        if not options_set.issubset(settings.all_features):
            invalid = options_set.difference(settings.all_features)
            raise ValueError(
                f'Feature(s): {invalid} not found. Available ones are: {settings.all_features}.'
            )

        missing = []
        for option in options_set:
            # Example: `settings.clients`
            if not setting_is_set(option):
                # List of all sections that are not fully configured
                missing.append(option)
        if missing:
            pytest.skip(f'Missing configuration for: {missing}.')
