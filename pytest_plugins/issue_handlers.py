from collections import defaultdict
import inspect
import re

import pytest

from robottelo.utils import slugify_component
from robottelo.utils.issue_handlers import (
    add_workaround,
    should_deselect,
)


def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    pass


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(session, items, config):
    """Generate the issue collection
    This collection includes pre-processed `is_open` status for each issue
    """
    # generate_issue_collection will process issue data
    pytest.issue_data = generate_issue_collection(items, config)


IS_OPEN = re.compile(
    # To match `if is_open('SAT:123456'):`
    r"\s*if\sis_open\(\S(?P<src>\D{2})\s*:\s*(?P<num>\d*)\S\)\d*"
)

NOT_IS_OPEN = re.compile(
    # To match `if not is_open('SAT:123456'):`
    r"\s*if\snot\sis_open\(\S(?P<src>\D{2})\s*:\s*(?P<num>\d*)\S\)\d*"
)

COMPONENT = re.compile(
    # To match :CaseComponent: FooBar
    r"\s*:CaseComponent:\s*(?P<component>\S*)",
    re.IGNORECASE,
)

IMPORTANCE = re.compile(
    # To match :CaseImportance: Critical
    r"\s*:CaseImportance:\s*(?P<importance>\S*)",
    re.IGNORECASE,
)


def generate_issue_collection(items, config):  # pragma: no cover
    """Generates a dictionary with the usage of Issue blockers

    For use in pytest_collection_modifyitems hook

    Arguments:
        items {list} - List of pytest test case objects.
        config {dict} - Pytest config object.

    Returns:
        [List of dicts] - Dicts indexed by "<handler>:<issue>"

        Example of return data::

            {
                "SAT:1625783" {
                    "data": {
                        # data taken from REST api,
                        "status": ...,
                        "resolution": ...,
                        ...
                        # Calculated data
                        "is_open": bool,
                        "is_deselected": bool,
                        "clones": [list],
                        "dupe_data": {dict}
                    },
                    "used_in" [
                        {
                            "filepath": "tests/foreman/ui/test_sync.py",
                            "lineno": 124,
                            "testcase": "test_positive_sync_custom_ostree_repo",
                            "component": "Repositories",
                        },
                        ...
                    ]
                },
                ...
            }
    """
    valid_markers = ["skip", "deselect"]
    collected_data = defaultdict(lambda: {"data": {}, "used_in": []})

    deselect_data = {}  # a local cache for deselected tests

    test_modules = set()

    # --- Build the issue marked usage collection ---
    for item in items:
        if item.nodeid.startswith('tests/robottelo/'):
            # Unit test, no issue processing
            # TODO: We very likely don't need to include component and importance in collected_data
            # Removing these would unravel issue_handlers dependence on testimony
            # Allowing for issue_handler use in unit tests
            continue

        # register test module as processed
        test_modules.add(item.module)

        filepath, lineno, testcase = item.location
        # Component and importance marks are determined by testimony tokens
        # Testimony.yaml as of writing has both as required, so any
        if not (components := item.get_closest_marker('component')):
            continue
        component_mark = components.args[0]
        component_slug = slugify_component(component_mark, False)
        importance_mark = item.get_closest_marker('importance').args[0]
        for marker in item.iter_markers():
            if marker.name in valid_markers:
                issue = marker.kwargs.get('reason') or marker.args[0]
                issue_key = issue.strip()
                collected_data[issue_key]['used_in'].append(
                    {
                        'filepath': filepath,
                        'lineno': lineno,
                        'testcase': testcase,
                        'component': component_mark,
                        'importance': importance_mark,
                        'component_mark': component_slug,
                        'usage': marker.name,
                    }
                )

                # Store issue key to lookup in the deselection process
                deselect_data[item.location] = issue_key

        # Then take the workarounds using `is_open` helper.
        source = inspect.getsource(item.function)
        if 'is_open(' in source:
            kwargs = {
                'filepath': filepath,
                'lineno': lineno,
                'testcase': testcase,
                'component': component_mark,
                'importance': importance_mark,
                'component_mark': component_slug,
            }
            add_workaround(collected_data, IS_OPEN.findall(source), 'is_open', **kwargs)
            add_workaround(collected_data, NOT_IS_OPEN.findall(source), 'not is_open', **kwargs)

    # Take uses of `is_open` from outside of test cases e.g: SetUp methods
    for test_module in test_modules:
        module_source = inspect.getsource(test_module)
        component_matches = COMPONENT.findall(module_source)
        module_component = None
        if component_matches:
            module_component = component_matches[0]
        if 'is_open(' in module_source:
            kwargs = {
                'filepath': test_module.__file__,
                'lineno': 1,
                'testcase': test_module.__name__,
                'component': module_component,
            }

            def validation(data, issue, usage, **kwargs):
                return issue not in data

            add_workaround(
                collected_data,
                IS_OPEN.findall(module_source),
                'is_open',
                validation=validation,
                **kwargs,
            )
            add_workaround(
                collected_data,
                NOT_IS_OPEN.findall(module_source),
                'not is_open',
                validation=validation,
                **kwargs,
            )

    # --- add deselect markers dynamically ---
    for item in items:
        issue = deselect_data.get(item.location)
        if issue and should_deselect(issue, collected_data[issue]['data']):
            collected_data[issue]['data']['is_deselected'] = True
            item.add_marker(pytest.mark.deselect(reason=issue))

    return collected_data
