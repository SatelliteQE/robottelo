import pytest

from robottelo.constants import DEFAULT_ORG
from robottelo.hosts import Satellite


@pytest.fixture
def default_org(target_sat):
    return target_sat.api.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0]


@pytest.fixture
def session(module_target_sat, test_name, ui_user, request):
    """Session fixture which automatically initializes (but does not start!)
    airgun UI session and correctly passes current test name to it. Uses shared
    module user credentials to log in.

    Usage::

        def test_foo(session):
            with session:
                # your ui test steps here
                session.architecture.create({'name': 'bar'})

    """
    with module_target_sat.ui_session(test_name, ui_user.login, ui_user.password) as session:
        yield session


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
