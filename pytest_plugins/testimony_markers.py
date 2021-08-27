import datetime
import inspect
import re

import pytest

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
        '--assignee',
        help='Comma separated list of assignees to include in test collection',
    )


def pytest_configure(config):
    """Register markers related to testimony tokens"""
    for marker in [
        'importance: CaseImportance testimony token, use --importance to filter',
        'component: Component testimony token, use --component to filter',
        'assignee: Assignee testimony token, use --assignee to filter',
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

assignee_regex = re.compile(
    # To match :Assignee: jsmith
    r'\s*:Assignee:\s*(?P<assignee>\S*)',
    re.IGNORECASE,
)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, items, config):
    """Add markers for testimony tokens"""
    # split the option string and handle no option, single option, multiple
    # config.getoption(default) doesn't work like you think it does, hence or ''
    importance = [i for i in (config.getoption('importance') or '').split(',') if i != '']
    component = [c for c in (config.getoption('component') or '').split(',') if c != '']
    assignee = [a for a in (config.getoption('assignee') or '').split(',') if a != '']

    selected = []
    deselected = []
    logger.info('Processing test items to add testimony token markers')
    for item in items:
        if item.nodeid.startswith('tests/robottelo/') and 'test_junit' not in item.nodeid:
            # Unit test, no testimony markers
            continue

        # apply the marks for importance, component, and assignee
        # Find matches from docstrings starting at smallest scope
        item_docstrings = [
            d
            for d in map(inspect.getdoc, (item.function, getattr(item, 'cls', None), item.module))
            if d is not None
        ]
        item_mark_names = [m.name for m in item.iter_markers()]
        for docstring in item_docstrings:
            # Add marker starting at smallest docstring scope
            # only add the mark if it hasn't already been applied at a lower scope
            doc_component = component_regex.findall(docstring)
            if doc_component and 'component' not in item_mark_names:
                item.add_marker(pytest.mark.component(doc_component[0]))
            doc_importance = importance_regex.findall(docstring)
            if doc_importance and 'importance' not in item_mark_names:
                item.add_marker(pytest.mark.importance(doc_importance[0]))
            doc_assignee = assignee_regex.findall(docstring)
            if doc_assignee and 'assignee' not in item_mark_names:
                item.add_marker(pytest.mark.assignee(doc_assignee[0]))

        # add markers as user_properties so they are recorded in XML properties of the report
        for marker in item.iter_markers():
            item.user_properties.append((marker.name, next(iter(marker.args), None)))
        item.user_properties.append(
            ("start_time", datetime.datetime.utcnow().strftime(FMT_XUNIT_TIME))
        )

        # exit early if no filters were passed
        if importance or component or assignee:
            # Filter test collection based on CLI options for filtering
            # filters should be applied together
            # such that --component Repository --importance Critical --assignee jsmith
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
            assignee_marker = item.get_closest_marker('assignee').args[0]
            if assignee and assignee_marker not in assignee:
                logger.debug(
                    f'Deselected test {item.nodeid} due to "--assignee {assignee}",'
                    f'test has assignee mark: {assignee_marker}'
                )
                deselected.append(item)
                continue
            selected.append(item)

    # selected will be empty if no filter option was passed, defaulting to full items list
    items[:] = selected if deselected else items
    config.hook.pytest_deselected(items=deselected)
