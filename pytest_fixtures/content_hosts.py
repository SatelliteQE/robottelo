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
def host_conf(request):
    """A function-level fixture that returns parameters for VMBroker host deployment"""
    conf = {}
    params = [*request.node.callspec.params.values()][0]
    conf['workflow'] = params.get('workflow', 'deploy_base_rhel')
    conf['rhel'] = params.get('rhel', settings.content_host.default_rhel_version)
    conf['memory'] = params.get('memory', settings.broker.clients.get(f"rhel{conf['rhel']}").memory)
    conf['cores'] = params.get('cores', settings.broker.clients.get(f"rhel{conf['rhel']}").cores)
    return conf


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


@pytest.fixture(
    params=[{'workflow': settings.content_host.deploy_workflow, 'rhel': '7'}],
    ids=[settings.content_host.deploy_workflow],
)
def rhel7_contenthost(host_conf):
    """A function-level fixture that provides a rhel7 content host object"""
    with VMBroker(
        workflow=host_conf['workflow'],
        rhel_version=host_conf['rhel'],
        memory=host_conf['memory'],
        cores=host_conf['cores'],
        host_classes={'host': ContentHost},
    ) as host:
        yield host


@pytest.fixture
def rhel7_contenthost_fips():
    """A function-level fixture that provides a content host object based on the rhel7_fips nick"""
    rhel7 = settings.broker.clients.rhel7
    with VMBroker(
        workflow='deploy-base-rhel-fips',
        rhel_version=rhel7.release,
        memory=rhel7.memory,
        cores=rhel7.cores,
        host_classes={'host': ContentHost},
    ) as host:
        yield host


@pytest.fixture(
    scope='module',
    params=[(settings.content_host.deploy_workflow, '7')],
    ids=[settings.content_host.deploy_workflow],
)
def rhel7_contenthost_module(host_conf):
    """A module-level fixture that provides a content host object based on the rhel7 nick"""
    with VMBroker(
        workflow=host_conf['workflow'],
        rhel_version=host_conf['rhel'],
        memory=host_conf['memory'],
        cores=host_conf['cores'],
        host_classes={'host': ContentHost},
    ) as host:
        yield host


@pytest.fixture(
    params=[(settings.content_host.deploy_workflow, '8')],
    ids=[settings.content_host.deploy_workflow],
)
def rhel8_contenthost(host_conf):
    """A fixture that provides a content host object based on the rhel8 nick"""
    with VMBroker(
        workflow=host_conf['workflow'],
        rhel_version=host_conf['rhel'],
        memory=host_conf['memory'],
        cores=host_conf['cores'],
        host_classes={'host': ContentHost},
    ) as host:
        yield host


@pytest.fixture
def rhel8_contenthost_fips():
    """A function-level fixture that provides a content host object based on the rhel8_fips nick"""
    rhel8 = settings.broker.clients.rhel8
    with VMBroker(
        workflow='deploy-base-rhel-fips',
        rhel_version=rhel8.release,
        memory=rhel8.memory,
        cores=rhel8.cores,
        host_classes={'host': ContentHost},
    ) as host:
        yield host


@pytest.fixture(
    scope='module',
    params=[(settings.content_host.deploy_workflow, '8')],
    ids=[settings.content_host.deploy_workflow],
)
def rhel8_contenthost_module():
    """A module-level fixture that provides a content host object based on the rhel8 nick"""
    with VMBroker(
        workflow=host_conf['workflow'],
        rhel_version=host_conf['rhel'],
        memory=host_conf['memory'],
        cores=host_conf['cores'],
        host_classes={'host': ContentHost},
    ) as host:
        yield host


@pytest.fixture(
    params=[(settings.content_host.deploy_workflow, '6')],
    ids=[settings.content_host.deploy_workflow],
)
def rhel6_contenthost():
    """A function-level fixture that provides a content host object based on the rhel6 nick"""
    with VMBroker(
        workflow=host_conf['workflow'],
        rhel_version=host_conf['rhel'],
        memory=host_conf['memory'],
        cores=host_conf['cores'],
        host_classes={'host': ContentHost},
    ) as host:
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


@pytest.fixture(
    scope='module',
    params=[(settings.content_host.deploy_workflow, '7')],
    ids=[settings.content_host.deploy_workflow],
)
def content_hosts():
    """A module-level fixture that provides two content hosts object based on the rhel7 nick"""
    with VMBroker(
        workflow=host_conf['workflow'],
        rhel_version=host_conf['rhel'],
        memory=host_conf['memory'],
        cores=host_conf['cores'],
        host_classes={'host': ContentHost},
        _count=2,
    ) as hosts:
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
