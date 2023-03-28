import datetime
import inspect
import re

import pytest

from robottelo.config import settings
from robottelo.hosts import get_sat_rhel_version
from robottelo.hosts import get_sat_version
from robottelo.logging import collection_logger as logger

FMT_XUNIT_TIME = '%Y-%m-%dT%H:%M:%S'
IMPORTANCE_LEVELS = []


def pytest_addoption(parser):
    """Add CLI options related to Testimony token based mark collection"""
    parser.addoption(
        '--importance',
        help='Comma separated list of importance levels to include in test collection',
    )
    parser.addoption(
        '--component',
        help='Comma separated list of component names to include in test collection',
    )
    parser.addoption(
        '--team',
        help='Comma separated list of teams to include in test collection',
    )


def pytest_configure(config):
    """Register markers related to testimony tokens"""
    for marker in [
        'importance: CaseImportance testimony token, use --importance to filter',
        'component: Component testimony token, use --component to filter',
        'team: Team testimony token, use --team to filter',
    ]:
        config.addinivalue_line("markers", marker)


component_regex = re.compile(
    # To match :CaseComponent: FooBar
    r'\s*:CaseComponent:\s*(?P<component>\S*)',
    re.IGNORECASE,
)

importance_regex = re.compile(
    # To match :CaseImportance: Critical
    r'\s*:CaseImportance:\s*(?P<importance>\S*)',
    re.IGNORECASE,
)

team_regex = re.compile(
    # To match :Team: Rocket
    r'\s*:Team:\s*(?P<team>\S*)',
    re.IGNORECASE,
)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, items, config):
    """Add markers and user_properties for testimony token metadata

    user_properties is used by the junit plugin, and thus by many test report systems
    Handle test function/class/module/session scope metadata coming from test docblocks
    Apply user_properties, ibutsu metadata, and pytest markers

    Markers for metadata use the testimony token name as the mark name
    The value of the token for the mark is the first mark arg

    Control test collection for custom options related to testimony metadata

    """
    # get RHEL version of the satellite
    rhel_version = get_sat_rhel_version().base_version
    sat_version = get_sat_version().base_version
    snap_version = settings.server.version.get('snap', '')

    # split the option string and handle no option, single option, multiple
    # config.getoption(default) doesn't work like you think it does, hence or ''
    importance = [i for i in (config.getoption('importance') or '').split(',') if i != '']
    component = [c for c in (config.getoption('component') or '').split(',') if c != '']
    team = [a.lower() for a in (config.getoption('team') or '').split(',') if a != '']

    selected = []
    deselected = []
    logger.info('Processing test items to add testimony token markers')
    for item in items:
        item.user_properties.append(
            ("start_time", datetime.datetime.utcnow().strftime(FMT_XUNIT_TIME))
        )
        if item.nodeid.startswith('tests/robottelo/') and 'test_junit' not in item.nodeid:
            # Unit test, no testimony markers
            continue

        # apply the marks for importance, component, and team
        # Find matches from docstrings starting at smallest scope
        item_docstrings = [
            d
            for d in map(inspect.getdoc, (item.function, getattr(item, 'cls', None), item.module))
            if d is not None
        ]
        for docstring in item_docstrings:
            item_mark_names = [m.name for m in item.iter_markers()]
            # Add marker starting at smallest docstring scope
            # only add the mark if it hasn't already been applied at a lower scope
            doc_component = component_regex.findall(docstring)
            if doc_component and 'component' not in item_mark_names:
                item.add_marker(pytest.mark.component(doc_component[0]))
            doc_importance = importance_regex.findall(docstring)
            if doc_importance and 'importance' not in item_mark_names:
                item.add_marker(pytest.mark.importance(doc_importance[0]))
            doc_team = team_regex.findall(docstring)
            if doc_team and 'team' not in item_mark_names:
                item.add_marker(pytest.mark.team(doc_team[0].lower()))

        # add markers as user_properties so they are recorded in XML properties of the report
        # pytest-ibutsu will include user_properties dict in testresult metadata
        for marker in item.iter_markers():
            item.user_properties.append((marker.name, next(iter(marker.args), None)))
        item.user_properties.append(("BaseOS", rhel_version))
        item.user_properties.append(("SatelliteVersion", sat_version))
        item.user_properties.append(("SnapVersion", snap_version))

        # exit early if no filters were passed
        if importance or component or team:
            # Filter test collection based on CLI options for filtering
            # filters should be applied together
            # such that --component Repository --importance Critical --team rocket
            # only collects tests which have all three of these marks

            # https://github.com/pytest-dev/pytest/issues/1373  Will make this way easier
            # testimony requires both importance and component, this will blow up if its forgotten
            importance_marker = item.get_closest_marker('importance').args[0]
            if importance and importance_marker not in importance:
                logger.debug(
                    f'Deselected test {item.nodeid} due to "--importance {importance}",'
                    f'test has importance mark: {importance_marker}'
                )
                deselected.append(item)
                continue
            component_marker = item.get_closest_marker('component').args[0]
            if component and component_marker not in component:
                logger.debug(
                    f'Deselected test {item.nodeid} due to "--component {component}",'
                    f'test has component mark: {component_marker}'
                )
                deselected.append(item)
                continue
            team_marker = item.get_closest_marker('team').args[0]
            if team and team_marker not in team:
                logger.debug(
                    f'Deselected test {item.nodeid} due to "--team {team}",'
                    f'test has team mark: {team_marker}'
                )
                deselected.append(item)
                continue

            selected.append(item)

    # selected will be empty if no filter option was passed, defaulting to full items list
    items[:] = selected if deselected else items
    config.hook.pytest_deselected(items=deselected)
