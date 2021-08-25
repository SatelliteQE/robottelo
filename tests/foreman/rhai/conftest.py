import nailgun.entities
import pytest
from airgun.session import Session
from broker.broker import VMBroker
from fauxfactory import gen_string
from requests.exceptions import HTTPError

from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import DISTRO_RHEL8
from robottelo.hosts import ContentHost
from robottelo.logging import logger


@pytest.fixture(scope='module')
def module_org():
    org_name = f'insights_{gen_string("alpha", 6)}'
    org = nailgun.entities.Organization(name=org_name).create()
    nailgun.entities.Parameter(
        name='remote_execution_connect_by_ip', value='Yes', organization=org.id
    ).create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    yield org


@pytest.fixture(scope='module')
def module_user(request, module_org):
    """Creates admin user with default org set to module org and shares that
    user for all tests in the same test module. User's login contains test
    module name as a prefix.

    :rtype: :class:`nailgun.entities.Organization`
    """
    # take only "module" from "tests.foreman.rhai.test_module"
    test_module_name = request.module.__name__.split('.')[-1].split('_', 1)[-1]
    login = f'{test_module_name}_{gen_string("alphanumeric")}'
    password = gen_string('alphanumeric')
    logger.debug('Creating session user %r', login)
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
        logger.debug('Deleting session user %r', user.login)
        user.delete(synchronous=False)
    except HTTPError as err:
        logger.warning(f'Unable to delete session user: {err}')


@pytest.fixture
def autosession(test_name, module_user):
    """Session fixture which automatically initializes and starts airgun UI
    session and correctly passes current test name to it. Use it when you want
    to have a session started before test steps and closed after all of them,
    i.e., when you don't need manual control over when the session is started or
    closed.

    Usage::

        def test_foo(autosession):
            # your ui test steps here
            autosession.architecture.create({'name': 'bar'})

    """
    with Session(test_name, module_user.login, module_user.password) as started_session:
        yield started_session


@pytest.fixture(scope='module')
def activation_key(module_org):
    ak = nailgun.entities.ActivationKey(
        auto_attach=True,
        content_view=module_org.default_content_view.id,
        environment=module_org.library.id,
        name=gen_string('alpha'),
        organization=module_org,
    ).create()
    yield ak
    ak.delete()


@pytest.fixture(scope='module')
def attach_subscription(module_org, activation_key):
    for subs in nailgun.entities.Subscription(organization=module_org).search():
        if subs.name == DEFAULT_SUBSCRIPTION_NAME:
            # "quantity" must be 1, not subscription["quantity"]. Greater
            # values produce this error: "RuntimeError: Error: Only pools
            # with multi-entitlement product subscriptions can be added to
            # the activation key with a quantity greater than one."
            activation_key.add_subscriptions(data={'quantity': 1, 'subscription_id': subs.id})
            break
    else:
        raise Exception(f"{module_org.name} organization doesn't have {DEFAULT_SUBSCRIPTION_NAME}")


@pytest.fixture
def vm(activation_key, module_org, default_sat):
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}) as vm:
        vm.configure_rhai_client(
            satellite=default_sat,
            activation_key=activation_key.name,
            org=module_org.label,
            rhel_distro=DISTRO_RHEL7,
        )
        yield vm


@pytest.fixture
def vm_rhel8(activation_key, module_org, default_sat):
    with VMBroker(nick='rhel8', host_classes={'host': ContentHost}) as vm:
        vm.configure_rhai_client(
            satellite=default_sat,
            activation_key=activation_key.name,
            org=module_org.label,
            rhel_distro=DISTRO_RHEL8,
            register_insights=False,
        )
        vm.add_rex_key(satellite=default_sat)
        yield vm


@pytest.fixture
def ansible_fixable_vm(vm_rhel8):
    vm_rhel8.run('dnf update -y dnf')
    vm_rhel8.run("sed -i -e '/^best/d' /etc/dnf/dnf.conf")
    vm_rhel8.run('insights-client --register')
