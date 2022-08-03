# Pytest Plugin to modify collection of test cases based on fixtures used by tests.
from robottelo.logging import collection_logger as logger


def pytest_addoption(parser):
    """Add options for pytest to collect tests based on fixtures its using"""
    help_text = '''
        Collects tests based on fixtures used by tests

        Usage: --uses-fixtures [options]

        Options: [ specific_fixture_name | list_of fixture names ]

        example: pytest tests/foreman --uses-fixtures target_sat module_target_sat
    '''
    parser.addoption("--uses-fixtures", nargs='+', help=help_text)


def pytest_collection_modifyitems(items, config):

    if not config.getoption('uses_fixtures', False):
        return

    filter_fixtures = config.getvalue('uses_fixtures')
    selected = []
    deselected = []

    for item in items:
        if set(item.fixturenames).intersection(set(filter_fixtures)):
            selected.append(item)
        else:
            deselected.append(item)
    logger.debug(
        f'Selected {len(selected)} and deselected {len(deselected)} '
        f'tests based on given fixtures {filter_fixtures} used by tests'
    )
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected
