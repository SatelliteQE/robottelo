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
        is_destructive = item.get_closest_marker('destructive')
        # Deselect Destructive tests and tests without capsule_factory fixture
        if 'capsule_factory' not in item.fixturenames or is_destructive:
            deselected.append(item)
            continue
        # Ignoring all puppet tests as they are destructive in nature
        # and needs its own satellite for verification
        if 'session_puppet_enabled_sat' in item.fixturenames:
            deselected.append(item)
            continue
        # Ignoring all satellite maintain tests as they are destructive in nature
        # Also dont need them in nminus testing as its not integration testing
        if 'sat_maintain' in item.fixturenames and 'satellite' in item.callspec.params.values():
            deselected.append(item)
            continue
        selected.append(item)

    config.hook.pytest_deselected(items=deselected)
    items[:] = selected


def pytest_sessionfinish(session, exitstatus):
    # Unregister the capsule from CDN after all tests
    if session.config.option.n_minus and not session.config.option.collectonly:
        caps = Capsule.get_host_by_hostname(hostname=settings.capsule.hostname)
        caps.unregister()
