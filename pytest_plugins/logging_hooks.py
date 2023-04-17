import logging
from xdist import is_xdist_worker, get_xdist_worker_id

from robottelo.logging import logger
from robottelo.logging import defaultFormatter
from robottelo.logging import robottelo_log_dir

try:
    from pytest_reportportal import RPLogger
    from pytest_reportportal import RPLogHandler
except ImportError:
    pass


def pytest_fixture_setup(fixturedef, request):
    if fixturedef.argname == 'worker_id':
        return
    worker_id = request.getfixturevalue('worker_id')

    if request.node.nodeid:
        log_file_name = request.node.nodeid.replace('/', '.')
    elif request.scope == 'session':
        log_file_name = 'session'
    # remove other fixture or test handlers
    handlers_to_remove = [
        h for h in logger.handlers if h.name == 'fixture' or h.name == 'test'
    ]
    logger.debug(f'fixture_setup - removing handlers: {handlers_to_remove}')
    for handler in handlers_to_remove:
        logger.removeHandler(handler)

    log_handler = logging.FileHandler(
        robottelo_log_dir.joinpath(f'fixture__{worker_id}__{log_file_name}.log')
    )
    log_handler.name = 'fixture'
    log_handler.setFormatter(defaultFormatter)
    logger.addHandler(log_handler)
    logger.info(f'Started Fixture: {request.fixturename}')


def pytest_runtest_call(item):
    handlers_to_remove = [
        h for h in logger.handlers if h.name == 'fixture' or h.name == 'test'
    ]
    logger.debug(f'runtest_setup - attached handlers: {logger.handlers}')
    logger.debug(f'runtest_setup - removing handlers: {handlers_to_remove}')
    for handler in handlers_to_remove:
        logger.removeHandler(handler)

    log_handler = logging.FileHandler(
        robottelo_log_dir.joinpath(f'test__{get_xdist_worker_id(item)}__{item.nodeid.replace("/", ".")}.log')
    )
    log_handler.name = 'test'
    log_handler.setFormatter(defaultFormatter)
    logger.addHandler(log_handler)
    logger.info(f'Started Test: {item.nodeid}')
    item.session.logger = logger


def pytest_runtest_logfinish(nodeid, location):
    logger.info(f'Finished Test: {nodeid}')
