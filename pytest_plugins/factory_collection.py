from inspect import getmembers
from inspect import isfunction


def pytest_configure(config):
    """Register markers related to testimony tokens"""
    marker = 'factory_instance: Test uses a fresh satellite or Capsule instance deployed by broker'
    config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(session, items, config):
    from pytest_fixtures.core import sat_cap_factory

    factory_fixture_names = [m[0] for m in getmembers(sat_cap_factory, isfunction)]
    for item in items:
        has_factoryfixture = set(item.fixturenames).intersection(set(factory_fixture_names))
        if has_factoryfixture:
            item.add_marker('factory_instance')
