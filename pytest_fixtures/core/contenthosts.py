"""
This module is to define pytest functions for content hosts

The functions in this module are read in the pytest_plugins/fixture_markers.py module
All functions in this module will be treated as fixtures that apply the contenthost mark
"""
import pytest
from broker import VMBroker

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import REPOS
from robottelo.hosts import ContentHost


def host_conf(request):
    """A function that returns arguments for VMBroker host deployment"""
    conf = params = {}
    if hasattr(request, 'param'):
        params = request.param
    conf['workflow'] = params.get('workflow', settings.content_host.deploy_workflow)
    _rhelver = f"rhel{params.get('rhel_version', settings.content_host.default_rhel_version)}"
    rhel_compose_id = settings.get(f"content_host.hardware.{_rhelver}.compose")
    if rhel_compose_id:
        conf['deploy_rhel_compose_id'] = rhel_compose_id
    conf['deploy_rhel_version'] = settings.content_host.hardware.get(_rhelver).release
    conf['memory'] = params.get('memory', settings.content_host.hardware.get(_rhelver).memory)
    conf['cores'] = params.get('cores', settings.content_host.hardware.get(_rhelver).cores)
    return conf


@pytest.fixture
def rhel_contenthost(request):
    """A function-level fixture that provides a content host object parametrized"""
    # Request should be parametrized through pytest_fixtures.fixture_markers
    # unpack params dict
    with VMBroker(**host_conf(request), host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(params=[{'rhel_version': '7'}])
def rhel7_contenthost(request):
    """A function-level fixture that provides a rhel7 content host object"""
    with VMBroker(**host_conf(request), host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(scope="class", params=[{'rhel_version': '7'}])
def rhel7_contenthost_class(request):
    """A fixture for use with unittest classes. Provides a rhel7 Content Host object"""
    with VMBroker(**host_conf(request), host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(scope='module', params=[{'rhel_version': '7'}])
def rhel7_contenthost_module(request):
    """A module-level fixture that provides a rhel7 content host object"""
    with VMBroker(**host_conf(request), host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(params=[{'rhel_version': '8'}])
def rhel8_contenthost(request):
    """A fixture that provides a rhel8 content host object"""
    with VMBroker(**host_conf(request), host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(scope='module', params=[{'rhel_version': '8'}])
def rhel8_contenthost_module(request):
    """A module-level fixture that provides a rhel8 content host object"""
    with VMBroker(**host_conf(request), host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(params=[{'rhel_version': 6}])
def rhel6_contenthost(request):
    """A function-level fixture that provides a rhel6 content host object"""
    with VMBroker(**host_conf(request), host_classes={'host': ContentHost}) as host:
        yield host


@pytest.fixture(scope='module')
def content_hosts(request):
    """A module-level fixture that provides two rhel7 content hosts object"""
    with VMBroker(**host_conf(request), host_classes={'host': ContentHost}, _count=2) as hosts:
        hosts[0].set_infrastructure_type('physical')
        yield hosts


@pytest.fixture(scope='module')
def registered_hosts(organization_ak_setup, content_hosts, default_sat):
    """Fixture that registers content hosts to Satellite, based on rh_cloud setup"""
    org, ak = organization_ak_setup
    for vm in content_hosts:
        vm.install_katello_ca(default_sat)
        vm.register_contenthost(org.label, ak.name)
        assert vm.subscribed
    return content_hosts


@pytest.fixture(scope="function")
def katello_host_tools_host(setup_rhst_repo, rhel7_contenthost, default_sat):
    """Register content host to Satellite and install katello-host-tools on the host,
    based on hosts setup"""
    rhel7_contenthost.install_katello_ca(default_sat)
    rhel7_contenthost.register_contenthost(
        setup_rhst_repo['org'].label,
        setup_rhst_repo['ak'].name,
    )
    assert rhel7_contenthost.subscribed
    rhel7_contenthost.enable_repo(REPOS[setup_rhst_repo['repo_name']]['id'])
    rhel7_contenthost.install_katello_host_tools()
    yield rhel7_contenthost


@pytest.fixture(scope="function")
def katello_host_tools_tracer_host(katello_host_tools_host, default_sat):
    """Install katello-host-tools-tracer, add REx key and create custom
    repositories on the host"""
    katello_host_tools_host.install_tracer()
    katello_host_tools_host.add_rex_key(satellite=default_sat)
    katello_host_tools_host.create_custom_rhel_repo_file_to_downgrade_packages()
    yield katello_host_tools_host


@pytest.fixture
def container_contenthost(rhel7_contenthost, default_sat):
    """Fixture that installs docker on the content host"""
    rhel7_contenthost.install_katello_ca(default_sat)

    repos = {
        'server': settings.repos.rhel7_os,
        'optional': settings.repos.rhel7_optional,
        'extras': settings.repos.rhel7_extras,
    }
    rhel7_contenthost.create_custom_repos(**repos)
    for service in constants.CONTAINER_CLIENTS:
        rhel7_contenthost.execute(f'yum -y install {service}')
        rhel7_contenthost.execute(f'systemctl start {service}')
    return rhel7_contenthost
