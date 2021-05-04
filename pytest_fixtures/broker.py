import pytest
from broker.broker import VMBroker
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import BROKER_RHEL77
from robottelo.hosts import Capsule
from robottelo.hosts import ContentHost
from robottelo.hosts import Satellite


@pytest.fixture(scope='session')
def satellite_factory():
    def factory(retry_limit=3, delay=300, **broker_args):
        vmb = VMBroker(
            host_classes={'host': Satellite},
            workflow=settings.server.deploy_workflow,
            **broker_args
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
            host_classes={'host': Capsule},
            workflow=settings.capsule.deploy_workflow,
            **broker_args
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
def satellite_latest():
    """A fixture that provides a latest Satellite"""
    with VMBroker(
        host_classes={'host': Satellite}, workflow=settings.server.deploy_workflow
    ) as sat:
        yield sat


@pytest.fixture
def capsule_latest():
    """A fixture that provides an unconfigured latest Capsule"""
    with VMBroker(
        host_classes={'host': Capsule}, workflow=settings.capsule.deploy_workflow
    ) as cap:
        yield cap
