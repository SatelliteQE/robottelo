import inspect
import json
import logging
import re
from collections import defaultdict
from datetime import datetime

import pytest

from robottelo.config import settings
from robottelo.helpers import slugify_component
from robottelo.utils.issue_handlers import add_workaround
from robottelo.utils.issue_handlers import bugzilla
from robottelo.utils.issue_handlers import is_open
from robottelo.utils.issue_handlers import should_deselect
from robottelo.utils.version import search_version_key
from robottelo.utils.version import VersionEncoder

LOGGER = logging.getLogger('issue_handlers_plugin')

DEFAULT_BZ_CACHE_FILE = 'bz_cache.json'


def pytest_addoption(parser):
    """Adds custom options to pytest runner."""
    parser.addoption(
        "--bz-cache",
        action='store_true',
        help=f"Use an existing {DEFAULT_BZ_CACHE_FILE} file instead of calling BZ API."
        f"Without this flag a cache file will be created with the name {DEFAULT_BZ_CACHE_FILE}."
        "This default cache file can be used on subsequent runs by including this flag",
    )


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(session, items, config):
    """Generate the issue collection (using bz cache via bugzilla issue handler util)
    This collection includes pre-processed `is_open` status for each issue

    """
    # generate_issue_collection will save a file, set by --bz-cache value

    pytest.issue_data = generate_issue_collection(items, config)

    # No item deselect, just adding skipif markers
    for item in items:
        skip_if_open = item.get_closest_marker('skip_if_open')
        if skip_if_open:
            # marker must have `BZ:123456` as argument.
            issue = skip_if_open.kwargs.get('reason') or skip_if_open.args[0]
            item.add_marker(pytest.mark.skipif(is_open(issue), reason=issue))


IS_OPEN = re.compile(
    # To match `if is_open('BZ:123456'):`
    r"\s*if\sis_open\(\S(?P<src>\D{2})\s*:\s*(?P<num>\d*)\S\)\d*"
)

NOT_IS_OPEN = re.compile(
    # To match `if not is_open('BZ:123456'):`
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

BZ = re.compile(
    # To match :BZ: 123456, 456789
    r"\s*:BZ:\s*(?P<bz>.*\S*)",
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
                "XX:1625783" {
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
                            "usage": "skip_if_open"
                        },
                        ...
                    ]
                },
                ...
            }
    """
    if not settings.configured:
        settings.configure()
    valid_markers = ["skip_if_open", "skip", "deselect"]
    collected_data = defaultdict(lambda: {"data": {}, "used_in": []})

    use_bz_cache = config.getvalue('bz_cache')  # use existing json cache?
    cached_data = None
    if use_bz_cache:
        try:
            with open(DEFAULT_BZ_CACHE_FILE, 'r') as bz_cache_file:
                LOGGER.info(f'Using BZ cache file for issue collection: {DEFAULT_BZ_CACHE_FILE}')
                cached_data = {
                    k: search_version_key(k, v) for k, v in json.load(bz_cache_file).items()
                }
        except FileNotFoundError:
            # no bz cache file exists
            LOGGER.warning(
                f'--bz-cache option used, cache file [{DEFAULT_BZ_CACHE_FILE}] not found'
            )

    deselect_data = {}  # a local cache for deselected tests

    test_modules = set()

    # --- Build the issue marked usage collection ---
    for item in items:
        component = None
        bzs = None
        importance = None

        # register test module as processed
        test_modules.add(item.module)

        # Find matches from docstrings top-down from: module, class, function.
        mod_cls_fun = (item.module, getattr(item, 'cls', None), item.function)
        for docstring in [d for d in map(inspect.getdoc, mod_cls_fun) if d is not None]:
            component_matches = COMPONENT.findall(docstring)
            if component_matches:
                component = component_matches[-1]
            bz_matches = BZ.findall(docstring)
            if bz_matches:
                bzs = bz_matches[-1]
            importance_matches = IMPORTANCE.findall(docstring)
            if importance_matches:
                importance = importance_matches[-1]

        filepath, lineno, testcase = item.location
        component_mark = slugify_component(component, False) if component is not None else None
        for marker in item.iter_markers():
            if marker.name in valid_markers:
                issue = marker.kwargs.get('reason') or marker.args[0]
                issue_key = issue.strip()
                collected_data[issue_key]['used_in'].append(
                    {
                        'filepath': filepath,
                        'lineno': lineno,
                        'testcase': testcase,
                        'component': component,
                        'importance': importance,
                        'component_mark': component_mark,
                        'usage': marker.name,
                    }
                )

                # Store issue key to lookup in the deselection process
                deselect_data[item.location] = issue_key
                # Add issue as a marker to enable filtering e.g: "-m BZ_123456"
                item.add_marker(getattr(pytest.mark, issue_key.replace(':', '_')))

        # Then take the workarounds using `is_open` helper.
        source = inspect.getsource(item.function)
        if 'is_open(' in source:
            kwargs = {
                'filepath': filepath,
                'lineno': lineno,
                'testcase': testcase,
                'component': component,
                'importance': importance,
                'component_mark': component_mark,
            }
            add_workaround(collected_data, IS_OPEN.findall(source), 'is_open', **kwargs)
            add_workaround(collected_data, NOT_IS_OPEN.findall(source), 'not is_open', **kwargs)

        # Add component as a marker to anable filtering e.g: "-m contentviews"
        if component_mark is not None:
            item.add_marker(getattr(pytest.mark, component_mark))

        # Add BZs from tokens as a marker to enable filter e.g: "-m BZ_123456"
        if bzs:
            for bz in bzs.split(','):
                item.add_marker(getattr(pytest.mark, f'BZ_{bz.strip()}'))

        # Add importance as a token
        if importance:
            item.add_marker(getattr(pytest.mark, importance.lower().strip()))

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

    # --- Collect BUGZILLA data ---
    bugzilla.collect_data_bz(collected_data, cached_data)

    # --- add deselect markers dynamically ---
    for item in items:
        issue = deselect_data.get(item.location)
        if issue and should_deselect(issue, collected_data[issue]['data']):
            collected_data[issue]['data']['is_deselected'] = True
            item.add_marker(pytest.mark.deselect(reason=issue))

    # --- if no cache file existed write a new cache file ---
    if cached_data is None and use_bz_cache:
        collected_data['_meta'] = {
            "version": settings.server.version,
            "hostname": settings.server.hostname,
            "created": datetime.now().isoformat(),
            "pytest": {"args": config.args, "pwd": str(config.invocation_dir)},
        }
        # bz_cache_filename could be None from the option not being passed, write the file anyway
        with open(DEFAULT_BZ_CACHE_FILE, 'w') as collect_file:
            json.dump(collected_data, collect_file, indent=4, cls=VersionEncoder)
            LOGGER.info(f"Generated BZ cache file {DEFAULT_BZ_CACHE_FILE}")

    return collected_data
