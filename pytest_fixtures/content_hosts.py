"""
This module is to define pytest functions for content hosts

The functions in this module are read in the pytest_plugins/fixture_markers.py module
All functions in this module will be treated as fixtures that apply the contenthost mark
"""
import pytest
from broker.broker import VMBroker

from robottelo.config import settings
from robottelo.hosts import ContentHost


@pytest.fixture
def host_conf(request):
    """A function-level fixture that returns parameters for VMBroker host deployment"""
    conf = params = {}
    if hasattr(request.node, 'callspec'):
        params = [*request.node.callspec.params.values()][0]
    conf['workflow'] = params.get('workflow', settings.content_host.deploy_workflow)
    _rhelver = f"rhel{params.get('rhel_version', settings.content_host.default_rhel_version)}"
    conf['rhel_ver'] = settings.content_host.hardware.get(_rhelver).release
    conf['memory'] = params.get('memory', settings.content_host.hardware.get(_rhelver).memory)
    conf['cores'] = params.get('cores', settings.content_host.hardware.get(_rhelver).cores)
    return conf


@pytest.fixture
def rhel_contenthost(host_conf):
    """A function-level fixture that provides a content host object parametrized"""
    # Request should be parametrized through pytest_fixtures.fixture_markers
    # unpack params dict
    with VMBroker(**host_conf, host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(params=[{'rhel_version': '7'}])
def rhel7_contenthost(host_conf):
    """A function-level fixture that provides a rhel7 content host object"""
    with VMBroker(**host_conf, host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(scope="class", params=[{'rhel_version': '7'}])
def rhel7_contenthost_class(host_conf):
    """A fixture for use with unittest classes. Provides a rhel7 Content Host object"""
    with VMBroker(**host_conf, host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(scope='module', params=[{'rhel_version': '7'}])
def rhel7_contenthost_module(host_conf):
    """A module-level fixture that provides a rhel7 content host object"""
    with VMBroker(**host_conf, host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(params=[{'rhel_version': '8'}])
def rhel8_contenthost(host_conf):
    """A fixture that provides a rhel8 content host object"""
    with VMBroker(**host_conf, host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(scope='module', params=[{'rhel_version': '8'}])
def rhel8_contenthost_module(host_conf):
    """A module-level fixture that provides a rhel8 content host object"""
    with VMBroker(**host_conf, host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(params=[{'rhel_version': 6}])
def rhel6_contenthost(host_conf):
    """A function-level fixture that provides a rhel6 content host object"""
    with VMBroker(**host_conf, host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(scope='module')
def content_hosts(host_conf):
    """A module-level fixture that provides two rhel7 content hosts object"""
    with VMBroker(**host_conf, host_classes={'host': ContentHost}, _count=2) as hosts:
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
