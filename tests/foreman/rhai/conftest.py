import logging

import nailgun.entities
from airgun.session import Session
from fauxfactory import gen_string
from requests.exceptions import HTTPError

from robottelo.constants import DEFAULT_ORG
from robottelo.decorators import fixture


LOGGER = logging.getLogger('robottelo')


@fixture(scope='module')
def module_org():
    """Shares the same organization for all tests in specific test module.
    Returns 'Default Organization' by default, override this fixture on

    :rtype: :class:`nailgun.entities.Organization`
    """
    default_org_id = (
        nailgun.entities.Organization().search(query={'search': f'name="{DEFAULT_ORG}"'})[0].id
    )
    return nailgun.entities.Organization(id=default_org_id).read()


@fixture(scope='module')
def module_user(request, module_org):
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
        description=f'created automatically by airgun for module "{test_module_name}"',
        login=login,
        password=password,
    ).create()
    user.password = password
    yield user
    try:
        LOGGER.debug('Deleting session user %r', user.login)
        user.delete(synchronous=False)
    except HTTPError as err:
        LOGGER.warning(f'Unable to delete session user: {err}')


@fixture()
def test_name(request):
    """Returns current test full name, prefixed by module name and test class
    name (if present).

    Examples::

        tests.foreman.ui.test_activationkey.test_positive_create
        tests.foreman.api.test_errata.ErrataTestCase.test_positive_list

    """
    # test module name, e.g. 'test_activationkey'
    name = [request.module.__name__]
    # test class name (if present), e.g. 'ActivationKeyTestCase'
    if request.instance:
        name.append(request.instance.__class__.__name__)
    # test name, e.g. 'test_positive_create'
    name.append(request.node.name)
    return '.'.join(name)


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
    test_name = f'{request.module.__name__}.{request.node.name}'
    login = module_user.login
    password = module_user.password
    with Session(test_name, login, password) as started_session:
        yield started_session
