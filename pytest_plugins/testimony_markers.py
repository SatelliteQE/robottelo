import inspect
import logging
import re

import pytest

LOGGER = logging.getLogger('robottelo')

IMPORTANCE_LEVELS = []


def pytest_addoption(parser):
    """Add CLI options related to Testimony token based mark collection"""
    parser.addoption(
        '--importance',
        help='Comma separated list of importance levels to include in collection',
    )
    parser.addoption(
        '--component',
        help="Comma separated list of component names to include in collection",
    )


def pytest_configure(config):
    """Register markers related to testimony tokens"""
    for marker in [
        'importance: CaseImportance testimony token, use --importance to filter',
        'component: Component testimony token, use --component to filter',
        # TODO: components read from testimony.yaml
    ]:
        config.addinivalue_line("markers", marker)


component_regex = re.compile(
    # To match :CaseComponent: FooBar
    r"\s*:CaseComponent:\s*(?P<component>\S*)",
    re.IGNORECASE,
)

importance_regex = re.compile(
    # To match :CaseImportance: Critical
    r"\s*:CaseImportance:\s*(?P<importance>\S*)",
    re.IGNORECASE,
)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, items, config):
    """Add markers for testimony tokens"""
    # split the option string and handle no option, single option, multiple
    # config.getoption(default) doesn't work like you think it does, hence or ''
    importance = [i for i in (config.getoption('importance') or '').split(',') if i != '']
    component = [c for c in (config.getoption('component') or '').split(',') if c != '']

    selected = []
    deselected = []
    for item in items:
        if item.nodeid.startswith('tests/robottelo/'):
            # Unit test, no testimony markers
            continue

        # apply the marks for component and importance
        # Find matches from docstrings starting at smallest scope
        item_docstrings = [
            d
            for d in map(inspect.getdoc, (item.function, getattr(item, 'cls', None), item.module))
            if d is not None
        ]
        for docstring in item_docstrings:
            item_mark_names = [m.name for m in item.iter_markers()]
            doc_component = component_regex.findall(docstring)
            if doc_component and 'component' not in item_mark_names:
                item.add_marker(pytest.mark.component(doc_component[0]))
            doc_importance = importance_regex.findall(docstring)
            if doc_importance and 'importance' not in item_mark_names:
                item.add_marker(pytest.mark.importance(doc_importance[0]))

        # exit early if no filters were passed
        if importance or component:
            # Filter test collection based on CLI options for filtering
            # filters should be applied together
            # such that --component Repository --importance Critical
            # only collects tests which have both of these marks

            # https://github.com/pytest-dev/pytest/issues/1373  Will make this way easier
            # testimony requires both importance and component, this will blow up if its forgotten
            importance_marker = item.get_closest_marker('importance').args[0]
            if importance and importance_marker not in importance:
                LOGGER.debug(
                    f'Deselected test {item.nodeid} due to "--importance {importance}",'
                    f'test has importance mark: {importance_marker}'
                )
                deselected.append(item)
                continue
            component_marker = item.get_closest_marker('component').args[0]
            if component and component_marker not in component:
                LOGGER.debug(
                    f'Deselected test {item.nodeid} due to "--component {component}",'
                    f'test has component mark: {component_marker}'
                )
                deselected.append(item)
                continue
            selected.append(item)

    items[:] = selected or items
    config.hook.pytest_deselected(items=deselected)
