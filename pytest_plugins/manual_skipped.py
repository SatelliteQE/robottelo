import logging

import pytest

from robottelo.constants import NOT_IMPLEMENTED

LOGGER = logging.getLogger(__name__)


def pytest_configure(config):
    """Register custom marker for stubbed test cases."""
    marker = "stubbed: Tests that are not automated yet or manual only."
    config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(session, config, items):
    """
    Collects tests based on pytest option to select tests marked as failed on Report Portal
    """
    mark_passed = config.getvalue('mark_manuals_passed')
    mark_skipped = config.getvalue('mark_manuals_skipped')
    if mark_passed or (not mark_skipped):
        return
    for item in items:
        if item.get_closest_marker(name='stubbed'):
            item.add_marker(marker=pytest.mark.skip(reason=NOT_IMPLEMENTED))


def pytest_addoption(parser):
    """Add options to pytest to modify manual tests as skipped"""
    parser.addoption(
        "--mark-manuals-skipped",
        action='store_true',
        default=True,
        help='Mark stubbed tests as skipped tests.',
    )
    parser.addoption(
        "--mark-manuals-passed",
        action='store_true',
        default=False,
        help='Mark stubbed tests as passed tests.',
    )
