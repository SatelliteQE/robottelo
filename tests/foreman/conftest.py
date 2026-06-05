"""Configurations for py.test runner"""

import pytest

from robottelo.hosts import Satellite
from robottelo.logging import collection_logger


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

    collection_logger.debug(f'Collected {len(items)} test cases')

    # Modify items based on collected issue_data
    deselected_items = []

    for item in items:
        if any("manifest" in f for f in getattr(item, "fixturenames", ())):
            item.add_marker("manifester")
        if any("ldap" in f for f in getattr(item, "fixturenames", ())):
            item.add_marker("ldap")
        # 1. Deselect tests marked with @pytest.mark.deselect
        # WONTFIX BZs makes test to be dynamically marked as deselect.
        deselect = item.get_closest_marker('deselect')
        if deselect:
            deselected_items.append(item)
            reason = deselect.kwargs.get('reason', deselect.args)
            collection_logger.debug(f'Deselected test "{item.name}" reason: {reason}')
            # Do nothing more with deselected tests
            continue

    config.hook.pytest_deselected(items=deselected_items)
    items[:] = [item for item in items if item not in deselected_items]


@pytest.fixture(autouse=True)
def ui_session_record_property(request, record_property):
    """
    Autouse fixture to set the record_property attribute for Satellite instances in the test.

    This fixture iterates over all fixtures in the current test node
    (excluding the current fixture) and sets the record_property attribute
    for instances of the Satellite class.

    Args:
        request: The pytest request object.
        record_property: The value to set for the record_property attribute.
    """
    test_directories = [
        'tests/foreman/destructive',
        'tests/foreman/ui',
        'tests/foreman/sanity',
        'tests/foreman/virtwho',
    ]
    test_file_path = request.node.fspath.strpath
    if any(directory in test_file_path for directory in test_directories):
        for fixture in request.node.fixturenames:
            if request.fixturename != fixture and isinstance(
                request.getfixturevalue(fixture), Satellite
            ):
                sat = request.getfixturevalue(fixture)
                sat.record_property = record_property
