"""Configurations for py.test runner"""
import pytest

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
