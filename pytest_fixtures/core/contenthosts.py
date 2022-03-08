"""
This module is to define pytest functions for content hosts

The functions in this module are read in the pytest_plugins/fixture_markers.py module
All functions in this module will be treated as fixtures that apply the contenthost mark
"""
import pytest
from broker import VMBroker
from fauxfactory import gen_string
from nailgun import entities

from robottelo import constants
from robottelo.config import settings
from robottelo.hosts import ContentHost


def host_conf(request):
    """A function that returns arguments for VMBroker host deployment"""
    conf = params = {}
    if hasattr(request, 'param'):
        params = request.param
    _rhelver = f"rhel{params.get('rhel_version', settings.content_host.default_rhel_version)}"
    rhel_compose_id = settings.get(f"content_host.hardware.{_rhelver}.compose")
    if rhel_compose_id:
        conf['deploy_rhel_compose_id'] = rhel_compose_id
    default_workflow = (
        settings.content_host.deploy_workflow.get(_rhelver)
        or settings.content_host.deploy_workflow.default
    )
    conf['workflow'] = params.get('workflow', default_workflow)
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
        vm.add_rex_key(default_sat)
        assert vm.subscribed
    return content_hosts


@pytest.fixture(scope="function")
def katello_host_tools_host(default_sat, module_org, rhel_contenthost):
    """Register content host to Satellite and install katello-host-tools on the host."""
    repo = settings.repos['SATCLIENT_REPO'][f'RHEL{rhel_contenthost.os_version.major}']
    register_host_custom_repo(default_sat, module_org, rhel_contenthost, [repo])
    rhel_contenthost.install_katello_host_tools()
    yield rhel_contenthost


@pytest.fixture(scope="function")
def cockpit_host(default_sat, module_org, rhel_contenthost):
    """Register content host to Satellite and install cockpit on the host."""
    rhelver = rhel_contenthost.os_version.major
    if rhelver > 7:
        repo = [settings.repos[f'rhel{rhelver}_os']['baseos']]
    else:
        repo = [settings.repos['rhel7_os'], settings.repos['rhel7_extras']]
    register_host_custom_repo(default_sat, module_org, rhel_contenthost, repo)
    rhel_contenthost.execute(f"hostnamectl set-hostname {rhel_contenthost.hostname} --static")
    rhel_contenthost.install_cockpit()
    rhel_contenthost.add_rex_key(satellite=default_sat)
    yield rhel_contenthost


def register_host_custom_repo(default_sat, module_org, rhel_contenthost, repo_urls):
    """Register content host to Satellite and sync repos"""
    # prepare Product and appropriate Satellite Client repo on satellite
    rhelver = rhel_contenthost.os_version.major
    prod = entities.Product(
        organization=module_org, name=f'rhel{rhelver}_{gen_string("alpha")}'
    ).create()
    for url in repo_urls:
        repo = entities.Repository(
            organization=module_org,
            product=prod,
            content_type='yum',
            url=url,
        ).create()
        repo.sync(timeout=1200)
    subs = entities.Subscription(organization=module_org, name=prod.name).search()
    assert len(subs), f'Subscription for sat client product: {prod.name} was not found.'
    subscription = subs[0]

    # finally, prepare the host end
    rhel_contenthost.install_katello_ca(default_sat)
    register = rhel_contenthost.register_contenthost(
        org=module_org.label,
        lce='Library',
        name=f'{gen_string("alpha")}-{rhel_contenthost.hostname}',
        force=True,
    )
    assert register.status == 0, (
        f'Failed to register the host: {rhel_contenthost.hostname}:'
        'rc: {register.status}: {register.stderr}'
    )
    # attach product subscription to the host
    rhel_contenthost.nailgun_host.bulk_add_subscriptions(
        data={
            "organization_id": module_org.id,
            "included": {"ids": [rhel_contenthost.nailgun_host.id]},
            "subscriptions": [{"id": subscription.id, "quantity": 1}],
        }
    )
    # refresh repository metadata
    rhel_contenthost.execute('subscription-manager repos --list')


@pytest.fixture
def rex_contenthost(katello_host_tools_host, default_sat):
    """Fixture that enables remote execution on the host"""
    katello_host_tools_host.add_rex_key(satellite=default_sat)
    yield katello_host_tools_host


@pytest.fixture(scope="function")
def katello_host_tools_tracer_host(rex_contenthost, default_sat):
    """Install katello-host-tools-tracer, create custom
    repositories on the host"""
    # create a custom, rhel version-specific OS repo
    rhelver = rex_contenthost.os_version.major
    if rhelver > 7:
        rex_contenthost.create_custom_repos(**settings.repos[f'rhel{rhelver}_os'])
    else:
        rex_contenthost.create_custom_repos(
            **{f'rhel{rhelver}_os': settings.repos[f'rhel{rhelver}_os']}
        )
    rex_contenthost.install_tracer()
    yield rex_contenthost


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
