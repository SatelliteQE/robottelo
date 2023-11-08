import pytest

from robottelo.hosts import Satellite


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
    for fixture in request.node.fixturenames:
        if request.fixturename != fixture:
            if isinstance(request.getfixturevalue(fixture), Satellite):
                sat = request.getfixturevalue(fixture)
                sat.record_property = record_property
