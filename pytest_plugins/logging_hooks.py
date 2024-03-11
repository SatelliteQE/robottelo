import contextlib
import logging

import logzero
import pytest
from xdist import is_xdist_worker

from robottelo.logging import (
    DEFAULT_DATE_FORMAT,
    broker_log_setup,
    logger,
    logging_yaml,
    robottelo_log_dir,
    robottelo_log_file,
)

with contextlib.suppress(ImportError):
    from pytest_reportportal import RPLogger, RPLogHandler


@pytest.fixture(autouse=True, scope='session')
def configure_logging(request, worker_id):
    """Handle xdist and ReportPortal logging configuration at session start

    Set up a separate logger for each pytest-xdist worker
    if worker_id != 'master' then xdist is running in multi-threading so
    a logfile named 'robottelo_gw{worker_id}.log' will be created.

    Add a handler for ReportPortal logging
    """
    worker_formatter = logzero.LogFormatter(
        fmt=f'%(asctime)s - {worker_id} - %(name)s - %(levelname)s - %(message)s',
        datefmt=DEFAULT_DATE_FORMAT,
    )
    use_rp_logger = hasattr(request.node.config, 'py_test_service')
    if use_rp_logger:
        logging.setLoggerClass(RPLogger)

    if is_xdist_worker(request) and f'{worker_id}' not in [h.get_name() for h in logger.handlers]:
        # Track the core logger's file handler level, set it in case core logger wasn't set
        worker_log_level = 'INFO'
        handlers_to_remove = [
            h
            for h in logger.handlers
            if isinstance(h, logging.FileHandler)
            and getattr(h, 'baseFilename', None) == str(robottelo_log_file)
        ]
        for handler in handlers_to_remove:
            logger.removeHandler(handler)
            worker_log_level = handler.level
        worker_handler = logging.FileHandler(
            robottelo_log_dir.joinpath(f'robottelo_{worker_id}.log')
        )
        worker_handler.set_name(f'{worker_id}')
        worker_handler.setFormatter(worker_formatter)
        worker_handler.setLevel(worker_log_level)
        logger.addHandler(worker_handler)
        broker_log_setup(
            level=logging_yaml.broker.level,
            file_level=logging_yaml.broker.fileLevel,
            formatter=worker_formatter,
            path=robottelo_log_dir.joinpath(f'robottelo_{worker_id}.log'),
        )

        if use_rp_logger:
            rp_handler = RPLogHandler(request.node.config.py_test_service)
            rp_handler.setFormatter(worker_formatter)
            # logger.addHandler(rp_handler)


def pytest_runtest_logstart(nodeid, location):
    logger.info(f'Started Test: {nodeid}')


def pytest_runtest_logreport(report):
    """Process the TestReport produced for each of the setup,
    call and teardown runtest phases of an item."""
    logger.info('Finished %s for test: %s, result: %s', report.when, report.nodeid, report.outcome)
