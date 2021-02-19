"""Configurations for py.test runner"""
import datetime
import logging

import pytest

try:
    from pytest_reportportal import RPLogger, RPLogHandler
except ImportError:
    pass
from _pytest.junitxml import xml_key
from robottelo.config import settings
from robottelo.decorators import setting_is_set

FMT_XUNIT_TIME = "%Y-%m-%dT%H:%M:%S"


def log(message, level="DEBUG"):
    """Pytest has a limitation to use logging.logger from conftest.py
    so we need to emulate the logger by stdouting the output
    """
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with open('robottelo.log', 'a') as log_file:
        log_file.write(f'{now} - conftest - {level} - {message}\n')


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
    messages.append(
        'shared_function enabled - {} - scope: {} - storage: {}'.format(
            shared_function_enabled, scope, storage
        )
    )
    # workaround for https://github.com/pytest-dev/pytest/issues/7767
    # remove if resolved and set autouse=True for record_testsuite_timestamp_xml fixture
    if config.pluginmanager.hasplugin("junitxml"):
        now = datetime.datetime.utcnow()
        xml = config._store.get(xml_key, None)
        if xml:
            xml.add_global_property('start_time', now.strftime(FMT_XUNIT_TIME))
    return messages


@pytest.fixture(scope="session")
def configured_settings():
    if not settings.configured:
        settings.configure()
    return settings


@pytest.fixture(autouse=True, scope='session')
def robottelo_logger(request, worker_id):
    """Set up a separate logger for each pytest-xdist worker
    if worker_id != 'master' then xdist is running in multi-threading so
    a logfile named 'robottelo_gw{worker_id}.log' will be created.
    """
    logger = logging.getLogger('robottelo')
    use_rp_logger = getattr(request.session.config, '_reportportal_configured', False)
    if use_rp_logger:
        logging.setLoggerClass(RPLogger)

    if f'{worker_id}' not in [h.get_name() for h in logger.handlers]:
        if worker_id != 'master':
            formatter = logging.Formatter(
                fmt='%(asctime)s - {} - %(name)s - %(levelname)s -'
                ' %(message)s'.format(worker_id),
                datefmt='%Y-%m-%d %H:%M:%S',
            )
            handler = logging.FileHandler(f'robottelo_{worker_id}.log')
            handler.set_name(f'{worker_id}')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            # Nailgun HTTP logs should also be included in gw* logs
            logging.getLogger('nailgun').addHandler(handler)
            if use_rp_logger:
                rp_handler = RPLogHandler(request.node.config.py_test_service)
                rp_handler.set_name(f'{worker_id}')
                rp_handler.setFormatter(formatter)
                logger.addHandler(rp_handler)
                logging.getLogger('nailgun').addHandler(rp_handler)
    return logger


@pytest.fixture(autouse=True)
def log_test_execution(robottelo_logger, test_name):
    robottelo_logger.debug(f'Started Test: {test_name}')
    yield
    robottelo_logger.debug(f'Finished Test: {test_name}')


@pytest.fixture
def test_name(request):
    """Returns current test full name, prefixed by module name and test class
    name (if present).

    Examples::

        tests.foreman.ui.test_activationkey::test_positive_create
        tests.foreman.api.test_errata::TestErrata::test_positive_list

    """
    return request.node._nodeid


def pytest_collection_modifyitems(session, items, config):
    """Called after collection has been performed, may filter or re-order
    the items in-place.
    """

    log(f"Collected {len(items)} test cases")

    # Modify items based on collected issue_data
    deselected_items = []

    for item in items:
        # 1. Deselect tests marked with @pytest.mark.deselect
        # WONTFIX BZs makes test to be dynamically marked as deselect.
        deselect = item.get_closest_marker('deselect')
        if deselect:
            deselected_items.append(item)
            reason = deselect.kwargs.get('reason', deselect.args)
            log(f"Deselected test '{item.name}' reason: {reason}")
            # Do nothing more with deselected tests
            continue

    config.hook.pytest_deselected(items=deselected_items)
    items[:] = [item for item in items if item not in deselected_items]


@pytest.fixture(autouse=False, scope="session")
def record_testsuite_timestamp_xml(record_testsuite_property):
    now = datetime.datetime.utcnow()
    record_testsuite_property("start_time", now.strftime(FMT_XUNIT_TIME))


@pytest.fixture(autouse=True, scope="function")
def record_test_timestamp_xml(record_property):
    now = datetime.datetime.utcnow()
    record_property("start_time", now.strftime(FMT_XUNIT_TIME))
