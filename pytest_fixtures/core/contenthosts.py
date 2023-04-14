"""
This module is to define pytest functions for content hosts

The functions in this module are read in the pytest_plugins/fixture_markers.py module
All functions in this module will be treated as fixtures that apply the contenthost mark
"""
import pytest
from broker import Broker

from robottelo import constants
from robottelo.config import settings
from robottelo.hosts import Capsule
from robottelo.hosts import ContentHost
from robottelo.hosts import Satellite


def host_conf(request):
    """A function that returns arguments for Broker host deployment"""
    conf = params = {}
    if hasattr(request, 'param'):
        params = request.param
    distro = params.get('distro', 'rhel')
    _rhelver = f"{distro}{params.get('rhel_version', settings.content_host.default_rhel_version)}"
    # check to see if no-containers is passed as an argument to pytest
    deploy_kwargs = {}
    if not any(
        [
            request.config.getoption('no_containers'),
            params.get('no_containers'),
            request.node.get_closest_marker('no_containers'),
        ]
    ):
        deploy_kwargs = settings.content_host.get(_rhelver).to_dict().get('container', {})
    # if we're not using containers or a container isn't available, use a VM
    if not deploy_kwargs:
        deploy_kwargs = settings.content_host.get(_rhelver).to_dict().get('vm', {})
    conf.update(deploy_kwargs)
    return conf


@pytest.fixture
def rhel_contenthost(request):
    """A function-level fixture that provides a content host object parametrized"""
    # Request should be parametrized through pytest_fixtures.fixture_markers
    # unpack params dict
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        yield host


@pytest.fixture(params=[{'rhel_version': '7'}])
def rhel7_contenthost(request):
    """A function-level fixture that provides a rhel7 content host object"""
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        yield host


@pytest.fixture(scope="class", params=[{'rhel_version': '7'}])
def rhel7_contenthost_class(request):
    """A fixture for use with unittest classes. Provides a rhel7 Content Host object"""
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        yield host


@pytest.fixture(scope='module', params=[{'rhel_version': '7'}])
def rhel7_contenthost_module(request):
    """A module-level fixture that provides a rhel7 content host object"""
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        yield host


@pytest.fixture(params=[{'rhel_version': '8'}])
def rhel8_contenthost(request):
    """A fixture that provides a rhel8 content host object"""
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        yield host


@pytest.fixture(scope='module', params=[{'rhel_version': '8'}])
def rhel8_contenthost_module(request):
    """A module-level fixture that provides a rhel8 content host object"""
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        yield host


@pytest.fixture(params=[{'rhel_version': 6}])
def rhel6_contenthost(request):
    """A function-level fixture that provides a rhel6 content host object"""
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        yield host


@pytest.fixture()
def content_hosts(request):
    """A function-level fixture that provides two rhel content hosts object"""
    with Broker(**host_conf(request), host_class=ContentHost, _count=2) as hosts:
        hosts[0].set_infrastructure_type('physical')
        yield hosts


@pytest.fixture(scope='module')
def mod_content_hosts(request):
    """A module-level fixture that provides two rhel7 content hosts object"""
    with Broker(**host_conf(request), host_class=ContentHost, _count=2) as hosts:
        hosts[0].set_infrastructure_type('physical')
        yield hosts


@pytest.fixture()
def registered_hosts(request, target_sat, module_org):
    """Fixture that registers content hosts to Satellite, based on rh_cloud setup"""
    with Broker(**host_conf(request), host_class=ContentHost, _count=2) as hosts:
        for vm in hosts:
            repo = settings.repos['SATCLIENT_REPO'][f'RHEL{vm.os_version.major}']
            target_sat.register_host_custom_repo(module_org, vm, [repo])
            vm.install_katello_host_tools()
            vm.add_rex_key(target_sat)
        yield hosts


@pytest.fixture
def katello_host_tools_host(target_sat, module_org, rhel_contenthost):
    """Register content host to Satellite and install katello-host-tools on the host."""
    repo = settings.repos['SATCLIENT_REPO'][f'RHEL{rhel_contenthost.os_version.major}']
    target_sat.register_host_custom_repo(module_org, rhel_contenthost, [repo])
    rhel_contenthost.install_katello_host_tools()
    yield rhel_contenthost


@pytest.fixture
def cockpit_host(class_target_sat, class_org, rhel_contenthost):
    """Register content host to Satellite and install cockpit on the host."""
    rhelver = rhel_contenthost.os_version.major
    if rhelver > 7:
        repo = [settings.repos[f'rhel{rhelver}_os']['baseos']]
    else:
        repo = [settings.repos['rhel7_os'], settings.repos['rhel7_extras']]
    class_target_sat.register_host_custom_repo(class_org, rhel_contenthost, repo)
    rhel_contenthost.execute(f"hostnamectl set-hostname {rhel_contenthost.hostname} --static")
    rhel_contenthost.install_cockpit()
    rhel_contenthost.add_rex_key(satellite=class_target_sat)
    yield rhel_contenthost


@pytest.fixture
def rex_contenthost(request, module_org, target_sat):
    request.param['no_containers'] = True
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        # Register content host to Satellite
        repo = settings.repos['SATCLIENT_REPO'][f'RHEL{host.os_version.major}']
        target_sat.register_host_custom_repo(module_org, host, [repo])
        # Enable remote execution on the host
        host.add_rex_key(satellite=target_sat)
        yield host


@pytest.fixture
def katello_host_tools_tracer_host(rex_contenthost, target_sat):
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
def container_contenthost(request, target_sat):
    """Fixture that installs docker on the content host"""
    request.param = {
        "rhel_version": "7",
        "distro": "rhel",
        "no_containers": True,
    }
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        host.install_katello_ca(target_sat)
        repos = {
            'server': settings.repos.rhel7_os,
            'optional': settings.repos.rhel7_optional,
            'extras': settings.repos.rhel7_extras,
        }
        host.create_custom_repos(**repos)
        for service in constants.CONTAINER_CLIENTS:
            host.execute(f'yum -y install {service}')
            host.execute(f'systemctl start {service}')
        yield host


@pytest.fixture
def centos_host(request, version):
    request.param = {
        "rhel_version": version.split('.')[0],
        "distro": "centos",
        "no_containers": True,
    }
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        yield host


@pytest.fixture
def oracle_host(request, version):
    request.param = {
        "rhel_version": version.split('.')[0],
        "distro": "oracle",
        "no_containers": True,
    }
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        yield host


@pytest.fixture
def sat_ready_rhel(request):
    deploy_args = {
        'deploy_rhel_version': request.param,
        'deploy_flavor': 'satqe-ssd.standard.std',
        'promtail_config_template_file': 'config_sat.j2',
        'workflow': 'deploy-rhel',
    }
    # if 'deploy_rhel_version' is not set, let's default to RHEL 8
    deploy_args['deploy_rhel_version'] = deploy_args.get('deploy_rhel_version', '8')
    deploy_args['workflow'] = 'deploy-rhel'
    with Broker(**deploy_args, host_class=Satellite) as host:
        yield host


@pytest.fixture
def cap_ready_rhel():
    rhel8 = settings.content_host.rhel8.vm
    deploy_args = {
        'deploy_rhel_version': rhel8.deploy_rhel_version,
        'deploy_flavor': 'satqe-ssd.standard.std',
        'workflow': rhel8.workflow,
    }
    with Broker(**deploy_args, host_class=Capsule) as host:
        yield host


@pytest.fixture(scope='module', params=[{'rhel_version': 8, 'no_containers': True}])
def external_puppet_server(request):
    deploy_args = host_conf(request)
    deploy_args['target_cores'] = 2
    deploy_args['target_memory'] = '4GiB'
    with Broker(**deploy_args, host_class=ContentHost) as host:
        host.register_to_cdn()
        # Install puppet packages
        assert (
            host.execute(
                'dnf install -y https://yum.puppet.com/puppet-release-el-8.noarch.rpm'
            ).status
            == 0
        )
        assert host.execute('dnf install -y puppetserver').status == 0
        # Source puppet profiles
        host.execute('. /etc/profile.d/puppet-agent.sh')
        # Setup Puppet Server CA
        assert host.execute('puppetserver ca setup').status == 0
        # Set puppet server as $HOSTNAME
        assert host.execute('puppet config set server $HOSTNAME').status == 0
        assert host.hostname in host.execute('puppet config print server').stdout
        # Enable service and setup firewall for puppetserver
        assert host.execute('systemctl enable --now puppetserver').status == 0
        assert host.execute('firewall-cmd --permanent --add-port="8140/tcp"').status == 0
        assert host.execute('firewall-cmd --reload').status == 0
        # Install theforeman/motd puppet module
        puppet_prod_env = '/etc/puppetlabs/code/environments/production'
        host.execute('puppet module install theforeman/motd')
        host.execute(f'mkdir -p {puppet_prod_env}/manifests')
        host.execute(f'echo "include motd" > {puppet_prod_env}/manifests/site.pp')

        yield host


@pytest.fixture(scope="module")
def sat_upgrade_chost():
    """A module-level fixture that provides a UBI_8 content host for upgrade scenario testing"""
    return Broker(
        container_host=settings.content_host.rhel8.container.container_host, host_class=ContentHost
    ).checkout()


@pytest.fixture
def custom_host(request):
    """A rhel content host that passes custom host config through request.param"""
    deploy_args = request.param
    # if 'deploy_rhel_version' is not set, let's default to RHEL 8
    deploy_args['deploy_rhel_version'] = deploy_args.get('deploy_rhel_version', '8')
    deploy_args['workflow'] = 'deploy-rhel'
    with Broker(**deploy_args, host_class=Satellite) as host:
        yield host
