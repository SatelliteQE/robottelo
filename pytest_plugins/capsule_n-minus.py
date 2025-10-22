# Collection of Capsule Factory fixture tests
# No destructive tests
# Adjust capsule host and capsule_configured host behavior for n_minus testing
# Calculate capsule hostname from inventory just as we do in xDist.py
from robottelo.config import settings
from robottelo.hosts import Capsule


def pytest_addoption(parser):
    """Add options for pytest to collect tests based on fixtures its using"""
    help_text = '''
        Collects tests based on capsule fixtures used by tests and uncollect destructive tests

        Usage: --n-minus

        example: pytest --n-minus tests/foreman
    '''
    parser.addoption("--n-minus", action='store_true', default=False, help=help_text)


def pytest_collection_modifyitems(items, config):
    if not config.getoption('n_minus', False):
        return

    selected = []
    deselected = []

    for item in items:
        # Select only non-destructive tests with capsule_factory fixture or sat_maintain fxture with capsule parameter
        if not (
            item.get_closest_marker('destructive')
            or 'session_puppet_enabled_sat' in item.fixturenames
        ) and (
            'capsule_factory' in item.fixturenames
            or 'sat_maintain' in item.fixturenames
            and 'capsule' in item.callspec.params.values()
        ):
            selected.append(item)
            continue
        deselected.append(item)

    config.hook.pytest_deselected(items=deselected)
    items[:] = selected


def pytest_sessionfinish(session, exitstatus):
    # Unregister the capsule from CDN after all tests
    if session.config.option.n_minus and not session.config.option.collectonly:
        caps = Capsule.get_host_by_hostname(hostname=settings.capsule.hostname)
        caps.unregister()
