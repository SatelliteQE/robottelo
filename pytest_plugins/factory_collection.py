from inspect import getmembers
from inspect import isfunction


def pytest_configure(config):
    """Register markers related to testimony tokens"""
    marker = 'factory_instance: Test uses a fresh satellite or Capsule instance deployed by broker'
    config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(session, items, config):
    from pytest_fixtures.core import sat_cap_factory

    deselected = []
    selected = []
    factory_fixture_names = [m[0] for m in getmembers(sat_cap_factory, isfunction)]
    for item in items:
        has_factoryfixture = set(item.fixturenames).intersection(set(factory_fixture_names))
        if has_factoryfixture:
            item.add_marker('factory_instance')
        if 'upgrade' in config.option.markexpr and not config.getvalue('include_factory_upgrades'):
            if all(
                [item.get_closest_marker('upgrade'), has_factoryfixture]
            ) or item.get_closest_marker('destructive'):
                deselected.append(item)
                continue
        selected.append(item)
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected


def pytest_addoption(parser):
    """Add CLI options related to upgrade tests mark collection"""
    parser.addoption(
        '--include-factory-upgrades',
        action='store_true',
        default=False,
        help='Include all tier upgrade tests in collection needing upgraded instances,'
        'by default they are deselected',
    )
