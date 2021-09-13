"""
This module is to define pytest functions for content hosts

The functions in this module are read in the pytest_plugins/fixture_markers.py module
All functions in this module will be treated as fixtures that apply the contenthost mark
"""
import pytest
from broker.broker import VMBroker

from robottelo.config import settings
from robottelo.constants import BROKER_RHEL77
from robottelo.hosts import ContentHost


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


@pytest.fixture(scope='module')
def content_hosts():
    """A module-level fixture that provides two content hosts object based on the rhel7 nick"""
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}, _count=2) as hosts:
        hosts[0].set_infrastructure_type('physical')
        yield hosts


@pytest.fixture(scope='module')
def registered_hosts(organization_ak_setup, content_hosts, default_sat):
    """Fixture that registers content hosts to Satellite."""
    org, ak = organization_ak_setup
    for vm in content_hosts:
        vm.install_katello_ca(default_sat)
        vm.register_contenthost(org.label, ak.name)
        assert vm.subscribed
    return content_hosts
