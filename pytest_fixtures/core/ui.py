from fauxfactory import gen_string
import pytest
from requests.exceptions import HTTPError

from robottelo.hosts import Satellite
from robottelo.logging import logger


@pytest.fixture(scope='module')
def ui_user(request, module_org, module_location, module_target_sat):
    """Creates admin user with default org set to module org and shares that
    user for all tests in the same test module. User's login contains test
    module name as a prefix.

    :rtype: :class:`nailgun.entities.Organization`
    """
    # take only "module" from "tests.ui.test_module"
    test_module_name = request.module.__name__.split('.')[-1].split('_', 1)[-1]
    login = f"{test_module_name}_{gen_string('alphanumeric')}"
    password = gen_string('alphanumeric')
    admin = request.param.get('admin', True) if hasattr(request, 'param') else True
    logger.debug('Creating session user %r', login)
    user = module_target_sat.api.User(
        admin=admin,
        organization=[module_org],
        location=[module_location],
        default_organization=module_org,
        default_location=module_location,
        description=f'created automatically by airgun for module "{test_module_name}"',
        login=login,
        password=password,
    ).create()
    user.password = password
    if not admin:
        # give all the permissions
        user.role = module_target_sat.api.Role().search(query={'per_page': 'all'})
        user.update(['role'])
    yield user
    try:
        logger.debug('Deleting session user %r', user.login)
        user.delete(synchronous=False)
    except HTTPError as err:
        logger.warning('Unable to delete session user: %s', str(err))


@pytest.fixture
def session(target_sat, test_name, ui_user, request):
    """Session fixture which automatically initializes (but does not start!)
    airgun UI session and correctly passes current test name to it. Uses shared
    module user credentials to log in.

    Usage::

        def test_foo(session):
            with session:
                # your ui test steps here
                session.architecture.create({'name': 'bar'})

    """
    with target_sat.ui_session(test_name, ui_user.login, ui_user.password) as session:
        yield session


@pytest.fixture
def autosession(target_sat, test_name, ui_user, request):
    """Session fixture which automatically initializes and starts airgun UI
    session and correctly passes current test name to it. Use it when you want
    to have a session started before test steps and closed after all of them,
    i.e. when you don't need manual control over when the session is started or
    closed.

    Usage::

        def test_foo(autosession):
            # your ui test steps here
            autosession.architecture.create({'name': 'bar'})

    """
    with target_sat.ui_session(test_name, ui_user.login, ui_user.password) as started_session:
        yield started_session


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
