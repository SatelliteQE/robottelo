import logging

import nailgun.entities
from airgun.session import Session
from fauxfactory import gen_string
from robottelo.constants import DEFAULT_ORG, DEFAULT_LOC
from requests.exceptions import HTTPError
from robottelo.decorators import fixture


LOGGER = logging.getLogger('robottelo')


@fixture(scope='module')
def module_org():
    """Shares the same organization for all tests in specific test module.
    Returns 'Default Organization' by default, override this fixture on

    :rtype: :class:`nailgun.entities.Organization`
    """
    default_org_id = nailgun.entities.Organization().search(
        query={'search': 'name="{}"'.format(DEFAULT_ORG)})[0].id
    return nailgun.entities.Organization(id=default_org_id).read()


@fixture(scope='module')
def module_loc():
    """Shares the same location for all tests in specific test module.
    Returns 'Default Location' by default, override this fixture on

    :rtype: :class:`nailgun.entities.Organization`
    """
    default_loc_id = nailgun.entities.Location().search(
        query={'search': 'name="{}"'.format(DEFAULT_LOC)})[0].id
    return nailgun.entities.Location(id=default_loc_id).read()


@fixture(scope='module')
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
    LOGGER.debug('Creating session user %r', login)
    user = nailgun.entities.User(
        admin=True,
        default_organization=module_org,
        default_location=module_loc,
        description='created automatically by airgun for module "{}"'.format(
            test_module_name),
        login=login,
        password=password,
    ).create()
    user.password = password
    yield user
    try:
        LOGGER.debug('Deleting session user %r', user.login)
        user.delete(synchronous=False)
    except HTTPError as err:
        LOGGER.warning('Unable to delete session user: %s', str(err))


@fixture(scope='module')
def module_viewer_user(module_org):
    """Custom user with viewer role for tests validating visibility of entities or fields created
    by some other user. Created only when accessed, unlike `module_user`.
    """
    viewer_role = nailgun.entities.Role().search(query={'search': 'name="Viewer"'})[0]
    default_loc_id = nailgun.entities.Location().search(
        query={'search': 'name="{}"'.format(DEFAULT_LOC)})[0].id
    custom_password = gen_string('alphanumeric')
    custom_user = nailgun.entities.User(
        admin=False,
        default_organization=module_org,
        location=[default_loc_id],
        organization=[module_org],
        role=[viewer_role],
        password=custom_password,
    ).create()
    custom_user.password = custom_password
    return custom_user


@fixture()
def test_name(request):
    """Returns current test full name, prefixed by module name and test class
    name (if present).

    Examples::

        tests.foreman.ui.test_activationkey.test_positive_create
        tests.foreman.api.test_errata.ErrataTestCase.test_positive_list

    """
    # test module name, e.g. 'test_activationkey'
    name = [request.module.__name__, ]
    # test class name (if present), e.g. 'ActivationKeyTestCase'
    if request.instance:
        name.append(request.instance.__class__.__name__)
    # test name, e.g. 'test_positive_create'
    name.append(request.node.name)
    return '.'.join(name)


@fixture()
def session(test_name, module_user):
    """Session fixture which automatically initializes (but does not start!)
    airgun UI session and correctly passes current test name to it. Uses shared
    module user credentials to log in.


    Usage::

    Case 1: In case if you want to land on dashboard page after login.

        def test_foo(session):
            with session() as session:
                # your ui test steps here
                session.architecture.create({'name': 'bar'})


    Case 2: In case if you want to land on entity page after login.
    e.g. https://satllite_server/products

        def test_foo(session):
            with session('products') as session:
                # your ui test steps here
                session.product.create({'name': 'bar'})

    """
    def _relative_path(path=""):
        return Session(test_name, module_user.login, module_user.password, relative_path=path)

    return _relative_path


@fixture()
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
    test_name = '{}.{}'.format(request.module.__name__, request.node.name)
    login = module_user.login
    password = module_user.password
    with Session(test_name, login, password) as started_session:
        yield started_session
