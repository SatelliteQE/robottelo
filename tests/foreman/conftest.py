# coding: utf-8
"""Configurations for py.test runner"""
import datetime
import inspect
import json
import logging
import re

import pytest
try:
    from pytest_reportportal import RPLogger, RPLogHandler
except ImportError:
    pass

from robottelo.config import settings
from robottelo.decorators import setting_is_set


BEGIN_BZ = re.compile(
    # To match `# BEGIN BZ:12345`
    r"\s*#\s*BEGIN\s*(?P<source>\D{2})\s*:\s*(?P<number>\d*)"
)
COMPONENT = re.compile(
    # To match :CaseComponent: FooBar
    r"\s*:CaseComponent:\s*(?P<component>\S*)",
    re.IGNORECASE
)


def log(message, level="DEBUG"):
    """Pytest has a limitation to use logging.logger from conftest.py
    so we need to emulate the logger by stdouting the output
    """
    now = datetime.datetime.utcnow()
    full_message = "{date} - conftest - {level} - {message}\n".format(
        date=now.strftime("%Y-%m-%d %H:%M:%S"),
        level=level,
        message=message
    )
    print(full_message)  # noqa
    with open('robottelo.log', 'a') as log_file:
        log_file.write(full_message)


def pytest_report_header(config):
    """Called when pytest session starts"""
    messages = []

    shared_function_enabled = 'OFF'
    scope = ''
    storage = 'file'
    if setting_is_set('shared_function'):
        if settings.shared_function.enabled:
            shared_function_enabled = 'ON'
        scope = settings.shared_function.scope
        if not scope:
            scope = ''
        storage = settings.shared_function.storage
    if pytest.config.pluginmanager.hasplugin("junitxml"):
        junit = getattr(config, "_xml", None)
        if junit is not None:
            now = datetime.datetime.utcnow()
            junit.add_global_property("start_time", now.strftime("%Y-%m-%dT%H:%M:%S"))
    messages.append(
        'shared_function enabled - {0} - scope: {1} - storage: {2}'.format(
            shared_function_enabled, scope, storage))

    return messages


@pytest.fixture(scope="session")
def worker_id(request):
    """Gets the worker ID when running in multi-threading with xdist
    """
    if hasattr(request.config, 'slaveinput'):
        # return gw+(0..n)
        return request.config.slaveinput['slaveid']
    else:
        return 'master'


@pytest.fixture(scope="session")
def configured_settings():
    if not settings.configured:
        settings.configure()
    return settings


@pytest.fixture(autouse=True, scope='module')
def robottelo_logger(request, worker_id):
    """Set up a separate logger for each pytest-xdist worker
    if worker_id != 'master' then xdist is running in multi-threading so
    a logfile named 'robottelo_gw{worker_id}.log' will be created.
    """
    logger = logging.getLogger('robottelo')
    if (hasattr(request.session.config, '_reportportal_configured') and
       request.session.config._reportportal_configured):
        logging.setLoggerClass(RPLogger)
    if '{0}'.format(worker_id) not in [h.get_name() for h in logger.handlers]:
        if worker_id != 'master':
            formatter = logging.Formatter(
                fmt='%(asctime)s - {0} - %(name)s - %(levelname)s -'
                    ' %(message)s'.format(worker_id),
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler = logging.FileHandler(
                'robottelo_{0}.log'.format(worker_id)
            )
            handler.set_name('{0}'.format(worker_id))
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            # Nailgun HTTP logs should also be included in gw* logs
            logging.getLogger('nailgun').addHandler(handler)
            if (hasattr(request.session.config, '_reportportal_configured') and
               request.session.config._reportportal_configured):
                rp_handler = RPLogHandler(request.node.config.py_test_service)
                rp_handler.set_name('{0}'.format(worker_id))
                rp_handler.setFormatter(formatter)
                logger.addHandler(rp_handler)
                logging.getLogger('nailgun').addHandler(rp_handler)
    return logger


@pytest.fixture(autouse=True)
def log_test_execution(robottelo_logger, request):
    test_name = request.node.name
    parent_name = request.node.parent.name
    test_full_name = '{}/{}'.format(parent_name, test_name)
    robottelo_logger.debug('Started Test: {}'.format(test_full_name))
    yield None
    robottelo_logger.debug('Finished Test: {}'.format(test_full_name))


def generate_bz_collection(items, config, filename):
    """Generates a dictionary with the usage of BZ blockers"""

    bzcollect_data = {
        'skip': [],
        'deselect': [],
        'workaround': [],
        'skip_if': []
    }

    for item in items:
        filepath, lineno, testcase = item.location
        # Take the module level :CaseComponent:
        module_component = None
        with open(item.module.__file__, 'r') as modulefile:
            text = modulefile.read()
            matches = COMPONENT.findall(text)
            if matches:
                module_component = matches[0]
        # Then take from source of function if exists
        source = inspect.getsource(item.function)
        if ':CaseComponent:' in source:
            matches = COMPONENT.findall(source)
            if matches:
                module_component = matches[0]

        for marker in item.iter_markers():
            if marker.name in bzcollect_data.keys():
                bzcollect_data[marker.name].append(
                    {
                        'reason': marker.kwargs.get('reason'),
                        'filepath': filepath,
                        'lineno': lineno,
                        'testcase': testcase,
                        'component': module_component
                    }
                )

        # Then take the BEGIN BZ: workaround marker if exists
        if 'BEGIN BZ:' in source:
            matches = BEGIN_BZ.findall(source)
            for match in matches:
                bzcollect_data['workaround'].append(
                    {
                        'reason': "{0}:{1}".format(*match),
                        'filepath': filepath,
                        'lineno': lineno,
                        'testcase': testcase,
                        'component': module_component
                    }
                )
    print(json.dumps(bzcollect_data, indent=4))
    with open(filename, 'w') as bzcollect_file:
        json.dump(bzcollect_data, bzcollect_file, indent=4)
        log("Generated file {} with BZ collect data".format(filename))


def pytest_collection_modifyitems(items, config):
    """Called after collection has been performed, may filter or re-order
    the items in-place.

    1. If `--bzcollect` is passed, then only collect BZ numbers.

    2. Deselects all tests explicitly marked with
       @pytest.mark.deselect(reason='BZ 123145 is closed wontfix...').
    """
    deselected_items = []
    log("Collected %s test cases" % len(items))

    # 1. If `--bzcollect` is passed, then only collect BZ numbers.
    bzcollect = config.getvalue("bzcollect")
    if bzcollect:
        generate_bz_collection(items, config, filename=bzcollect)
        # if `--bzcollect` do not run any test
        config.hook.pytest_deselected(items=items)
        items[:] = []
        return

    for item in items:
        # 2. Deselect tests marked with @pytest.mark.deselect
        deselect = item.get_closest_marker('deselect')
        if deselect:
            deselected_items.append(item)
            reason = deselect.kwargs.get('reason', deselect.args)
            log(
                "Deselected test '{name}' reason: {reason}".format(
                    name=item.name, reason=reason
                )
            )

    config.hook.pytest_deselected(items=deselected_items)
    items[:] = [item for item in items if item not in deselected_items]


@pytest.fixture(autouse=True, scope="function")
def record_test_timestamp_xml(record_property):
    now = datetime.datetime.utcnow()
    record_property("start_time", now.strftime("%Y-%m-%dT%H:%M:%S"))


def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    markers = [
        "stubbed: Tests that are not automates yet.",
        "deselect(reason=None): Mark test to be removed from collection.",
        "tier1: CRUD tests",
        "tier2: Association tests",
        "tier3: Systems integration tests",
        "tier4: Long running tests",
        "destructive: Destructive tests",
        "upgrade: Upgrade tests",
        "run_in_one_thread: Sequential tests",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


def pytest_addoption(parser):
    """Adds custom options to pytest runner."""
    parser.addoption(
        "--bzcollect",
        nargs='?',
        default='bzcollect.json',
        const='bzcollect.json',
        help="Collect BZ information from test case markers and outputs JSON",
    )
    """Run `py.test path/to/tests --bzcollect file.json` and it will
    generate a file containing data for `skip`, `deselect` and `workaround`
    bugzilla markers.
    """
