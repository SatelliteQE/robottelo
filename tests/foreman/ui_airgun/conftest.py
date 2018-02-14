import nailgun.entities
from airgun.session import Session
from fauxfactory import gen_string
from robottelo.decorators import fixture


@fixture(scope='module')
def module_org():
    """Shares the same organization for all tests in specific test module.
    Returns 'Default Organization' by default, override this fixture on

    :rtype: :class:`nailgun.entities.Organization`
    """
    return nailgun.entities.Organization(id=1).read()


@fixture(scope='module')
def module_user(request, module_org):
    """Creates admin user with default org set to module org and shares that
    user for all tests in the same test module. User's login contains test
    module name as a prefix.

    :rtype: :class:`nailgun.entities.Organization`
    """
    password = gen_string('alphanumeric')
    # take only "module" from "tests.ui.test_module"
    test_module_name = request.module.__name__.split('.')[-1].split('_', 1)[-1]
    user = nailgun.entities.User(
        admin=True,
        default_organization=module_org,
        description='created automatically by airgun for module "{}"'.format(
            test_module_name),
        login='{}_{}'.format(test_module_name, gen_string('alphanumeric')),
        password=password,
    ).create()
    user.password = password
    return user


@fixture()
def session(request, module_user):
    """Session fixture which automatically initializes (but does not start!)
    airgun UI session and correctly passes current test name to it. Uses shared
    module user credentials to log in.


    Usage::

        def test_foo(session):
            with session:
                # your ui test steps here
                session.architecture.create({'name': 'bar'})

    """
    test_name = '{}.{}'.format(request.module.__name__, request.node.name)
    return Session(test_name, module_user.login, module_user.password)
