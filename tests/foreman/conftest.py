# coding: utf-8
"""Configurations for py.test runner"""
import datetime
import logging

import pytest
try:
    from pytest_reportportal import RPLogger, RPLogHandler
except ImportError:
    pass
from nailgun import entities
from robottelo.cleanup import EntitiesCleaner
from robottelo.config import settings
from robottelo.decorators import setting_is_set
from robottelo.bz_helpers import get_deselect_bug_ids, group_by_key
from robottelo.helpers import get_func_name


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


@pytest.fixture(scope="module", autouse=True)
def entities_cleaner(robottelo_logger, configured_settings):
    if configured_settings.cleanup:
        robottelo_logger.info('Entities cleaner enabled')
        cleaner = EntitiesCleaner(
            entities.Organization,
            entities.Host,
            entities.HostGroup
        )
        yield cleaner
        robottelo_logger.info('Cleaning entities')
        cleaner.clean()
    else:
        robottelo_logger.info('Entities cleaner disabled')
        yield None


@pytest.fixture(autouse=True)
def log_test_execution(robottelo_logger, request):
    test_name = request.node.name
    parent_name = request.node.parent.name
    test_full_name = '{}/{}'.format(parent_name, test_name)
    robottelo_logger.debug('Started Test: {}'.format(test_full_name))
    yield None
    robottelo_logger.debug('Finished Test: {}'.format(test_full_name))


def pytest_namespace():
    """return dict of name->object to be made globally available in
    the pytest namespace.  This hook is called at plugin registration
    time.
    Object is accessible only via dotted notation `item.key.nested_key`

    Exposes the list of all WONTFIX bugs and a mapping between decorated
    functions and Bug IDS (populated by decorator).
    """
    log("Registering custom pytest_namespace")
    return {
        'bugzilla': {
            'removal_ids': get_deselect_bug_ids(log=log),
            'decorated_functions': []
        }
    }


def _extract_setup_class_ids(item):
    setup_class_method = getattr(item.parent.obj, 'setUpClass', None)
    return getattr(setup_class_method, 'bugzilla_ids', [])


def pytest_collection_modifyitems(items, config):
    """ called after collection has been performed, may filter or re-order
    the items in-place.

    Deselecting all tests skipped due to WONTFIX BZ.
    """
    if not settings.configured:
        settings.configure()

    if settings.bugzilla.wontfix_lookup is not True:
        # if lookup is disable return all collection unmodified
        log('BZ deselect is disabled in settings')
        return items

    deselected_items = []
    decorated_functions = group_by_key(pytest.bugzilla.decorated_functions)

    log("Collected %s test cases" % len(items))

    for item in items:
        name = get_func_name(item.function, test_item=item)
        bug_ids = list(decorated_functions.get(name, []))
        bug_ids.extend(_extract_setup_class_ids(item))
        if any(bug_id in pytest.bugzilla.removal_ids for bug_id in bug_ids):
            deselected_items.append(item)
            log("Deselected test %s" % name)

    config.hook.pytest_deselected(items=deselected_items)
    items[:] = [item for item in items if item not in deselected_items]


@pytest.fixture(autouse=True, scope="function")
def record_test_timestamp_xml(record_property):
    now = datetime.datetime.utcnow()
    record_property("start_time", now.strftime("%Y-%m-%dT%H:%M:%S"))
