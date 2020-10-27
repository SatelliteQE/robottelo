import pytest
from broker.broker import VMBroker

from robottelo.constants import BROKER_RHEL77
from robottelo.hosts import ContentHost


@pytest.fixture
def rhel7_host():
    """A function-level fixture that provides a host object based on the rhel7 nick"""
    with VMBroker(nick='rhel7') as host:
        yield host


@pytest.fixture
def rhel7_contenthost():
    """A fixture that provides a content host object based on the rhel7 nick"""
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(scope="module")
def rhel77_host_module():
    """A module-level fixture that provides a host object"""
    with VMBroker(**BROKER_RHEL77) as host:
        yield host


@pytest.fixture(scope="module")
def rhel77_contenthost_module():
    """A module-level fixture that provides a ContentHost object"""
    with VMBroker(host_classes={'host': ContentHost}, **BROKER_RHEL77) as host:
        yield host


@pytest.fixture(scope="class")
def rhel77_contenthost_class(request):
    """A fixture for use with unittest classes. Provided a ContentHost object"""
    with VMBroker(host_classes={'host': ContentHost}, **BROKER_RHEL77) as host:
        request.cls.content_host = host
        yield
