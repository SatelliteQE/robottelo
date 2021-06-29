import pytest
from broker.broker import VMBroker
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import BROKER_RHEL77
from robottelo.hosts import Capsule
from robottelo.hosts import ContentHost
from robottelo.hosts import Satellite


@pytest.fixture(scope='session')
def default_sat():
    """Returns a Satellite object for settings.server.hostname"""
    if settings.server.hostname:
        return Satellite()


@pytest.fixture(scope='session')
def satellite_factory():
    def factory(retry_limit=3, delay=300, **broker_args):
        vmb = VMBroker(
            host_classes={'host': Satellite},
            workflow=settings.server.deploy_workflow,
            **broker_args,
        )
        timeout = (1200 + delay) * retry_limit
        sat = wait_for(
            vmb.checkout, func_kwargs=broker_args, timeout=timeout, delay=delay, fail_condition=[]
        )
        return sat.out

    return factory


@pytest.fixture(scope='session')
def capsule_factory():
    def factory(retry_limit=3, delay=300, **broker_args):
        vmb = VMBroker(
            host_classes={'host': Capsule}, workflow=settings.capsule.deploy_workflow, **broker_args
        )
        timeout = (1200 + delay) * retry_limit
        cap = wait_for(
            vmb.checkout, func_kwargs=broker_args, timeout=timeout, delay=delay, fail_condition=[]
        )
        return cap.out

    return factory


@pytest.fixture
def rhel7_host():
    """A function-level fixture that provides a host object based on the rhel7 nick"""
    with VMBroker(nick='rhel7') as host:
        yield host


@pytest.fixture
def rhel_contenthost(request):
    """A function-level fixture that provides a content host object parametrized"""
    # Request should be parametrized through pytest_fixtures.fixture_markers
    # unpack params dict
    workflow = request.param.get('workflow', settings.content_host.deploy_workflow)
    rhel_version = request.param.get('rhel', settings.content_host.default_rhel_version)
    # TODO: target_memory/cores, host type, other fields?
    with VMBroker(
        workflow=workflow, rhel_version=rhel_version, host_classes={'host': ContentHost}
    ) as host:
        yield host


@pytest.fixture
def rhel7_contenthost():
    """A function-level fixture that provides a content host object based on the rhel7 nick"""
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture
def rhel7_contenthost_fips():
    """A function-level fixture that provides a content host object based on the rhel7_fips nick"""
    with VMBroker(nick='rhel7_fips', host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(scope="module")
def rhel7_contenthost_module():
    """A module-level fixture that provides a content host object based on the rhel7 nick"""
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture
def rhel8_contenthost():
    """A fixture that provides a content host object based on the rhel8 nick"""
    with VMBroker(nick='rhel8', host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture
def rhel8_contenthost_fips():
    """A function-level fixture that provides a content host object based on the rhel8_fips nick"""
    with VMBroker(nick='rhel8_fips', host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture
def rhel6_contenthost():
    """A function-level fixture that provides a content host object based on the rhel6 nick"""
    with VMBroker(nick='rhel6', host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(scope="module")
def rhel77_host_module():
    """A module-level fixture that provides a RHEL7.7 host object"""
    with VMBroker(**BROKER_RHEL77) as host:
        yield host


@pytest.fixture(scope="module")
def rhel77_contenthost_module():
    """A module-level fixture that provides a RHEL7.7 Content Host object"""
    with VMBroker(host_classes={'host': ContentHost}, **BROKER_RHEL77) as host:
        yield host


@pytest.fixture(scope="class")
def rhel77_contenthost_class(request):
    """A fixture for use with unittest classes. Provides a Content Host object"""
    with VMBroker(host_classes={'host': ContentHost}, **BROKER_RHEL77) as host:
        request.cls.content_host = host
        yield host


@pytest.fixture
def satellite_latest(default_sat):
    """A fixture that provides a latest Satellite"""
    version_args = dict(
        deploy_sat_version=default_sat.version or settings.server.version.get('release', ''),
        deploy_snap_version=settings.server.version.get('snap', ''),
    )

    with VMBroker(
        host_classes={'host': Satellite}, workflow=settings.server.deploy_workflow, **version_args
    ) as sat:
        yield sat


@pytest.fixture
def capsule_latest(default_sat):
    """A fixture that provides an unconfigured latest Capsule"""
    version_args = dict(
        deploy_sat_version=default_sat.version or settings.server.version.get('release', ''),
        deploy_snap_version=settings.server.version.get('snap', ''),
    )

    with VMBroker(
        host_classes={'host': Capsule},
        workflow=str(settings.capsule.deploy_workflow),
        **version_args,
    ) as cap:
        yield cap


@pytest.fixture
def capsule_configured(capsule_latest):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    capsule_latest.install_katello_ca()
    capsule_latest.register_contenthost()
    capsule_latest.capsule_setup()
    yield capsule_latest


@pytest.fixture(scope='module')
def content_hosts():
    """A module-level fixture that provides two content hosts object based on the rhel7 nick"""
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}, _count=2) as hosts:
        hosts[0].set_infrastructure_type('physical')
        yield hosts


@pytest.fixture(scope='module')
def registered_hosts(organization_ak_setup, content_hosts):
    """Fixture that registers content hosts to Satellite."""
    org, ak = organization_ak_setup
    for vm in content_hosts:
        vm.install_katello_ca()
        vm.register_contenthost(org.label, ak.name)
        assert vm.subscribed
    return content_hosts


@pytest.fixture
def destructive_sat(satellite_latest):
    """Destructive tests require changing settings.server.hostname for now"""
    with satellite_latest as sat:
        yield sat
