import nailgun.entities
import pytest
from airgun.session import Session
from fauxfactory import gen_string
from requests.exceptions import HTTPError

from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG
from robottelo.logging import logger


@pytest.fixture(scope='module')
def module_org():
    """Shares the same organization for all tests in specific test module.
    Returns 'Default Organization' by default, override this fixture on

    :rtype: :class:`nailgun.entities.Organization`
    """
    default_org_id = (
        nailgun.entities.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0].id
    )
    return nailgun.entities.Organization(id=default_org_id).read()


@pytest.fixture(scope='module')
def module_loc():
    """Shares the same location for all tests in specific test module.
    Returns 'Default Location' by default, override this fixture on

    :rtype: :class:`nailgun.entities.Organization`
    """
    default_loc_id = (
        nailgun.entities.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0].id
    )
    return nailgun.entities.Location(id=default_loc_id).read()


@pytest.fixture(scope='module')
def module_user(request, module_org, module_loc):
    """Creates admin user with default org set to module org and shares that
    user for all tests in the same test module. User's login contains test
    module name as a prefix.

    :rtype: :class:`nailgun.entities.Organization`
    """
    # take only "module" from "tests.ui.test_module"
    test_module_name = request.module.__name__.split('.')[-1].split('_', 1)[-1]
    login = '{}_{}'.format(test_module_name, gen_string('alphanumeric'))
    password = gen_string('alphanumeric')
    logger.debug('Creating session user %r', login)
    user = nailgun.entities.User(
        admin=True,
        default_organization=module_org,
        default_location=module_loc,
        description=f'created automatically by airgun for module "{test_module_name}"',
        login=login,
        password=password,
    ).create()
    user.password = password
    yield user
    try:
        logger.debug('Deleting session user %r', user.login)
        user.delete(synchronous=False)
    except HTTPError as err:
        logger.warning('Unable to delete session user: %s', str(err))


@pytest.fixture()
def session(test_name, module_user):
    """Session fixture which automatically initializes (but does not start!)
    airgun UI session and correctly passes current test name to it. Uses shared
    module user credentials to log in.


    Usage::

        def test_foo(session):
            with session:
                # your ui test steps here
                session.architecture.create({'name': 'bar'})

    """
    return Session(test_name, module_user.login, module_user.password)


@pytest.fixture()
def autosession(test_name, module_user, request):
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
    login = module_user.login
    password = module_user.password
    with Session(test_name, login, password) as started_session:
        yield started_session
