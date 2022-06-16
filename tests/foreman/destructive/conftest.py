import pytest

from robottelo.constants import DEFAULT_ORG


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
    return module_target_sat.ui_session(test_name, ui_user.login, ui_user.password)
