"""A sanity testing plugin to assist in executing robottelo tests as sanity tests smartly

1. Make installer test to run first which should set the hostname and all other tests then
should run after that
"""


class ConfigurationException(Exception):
    """Raised when pytest configuration is missed"""

    pass


def pytest_configure(config):
    """Register markers related to testimony tokens"""
    config.addinivalue_line(
        "markers", "first_sanity: An installer test to run first in sanity testing"
    )


def pytest_collection_modifyitems(session, items, config):
    if 'sanity' not in config.option.markexpr:
        return

    selected = []
    deselected = []
    installer_test = None

    for item in items:
        if item.get_closest_marker('build_sanity'):
            # Identify the installer sanity test to run first
            if not installer_test and item.get_closest_marker('first_sanity'):
                installer_test = item
                deselected.append(item)
                continue
            # Test parameterization disablement for sanity
            # Remove Puppet based tests
            if 'session_puppet_enabled_sat' in item.fixturenames and 'puppet' in item.name:
                deselected.append(item)
                continue
            # Remove capsule tests
            if 'sat_maintain' in item.fixturenames and 'capsule' in item.name:
                deselected.append(item)
                continue
            # Remove parametrization from organization test
            if (
                'test_positive_create_with_name_and_description' in item.name
                and 'alphanumeric' not in item.name
            ):
                deselected.append(item)
                continue
        # Else select
        selected.append(item)

    # Append the installer test first to run
    if not installer_test:
        raise ConfigurationException(
            'The installer test is not configured to base the sanity testing on!'
        )
    selected.insert(0, installer_test)
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected
