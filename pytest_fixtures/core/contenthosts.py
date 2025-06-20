"""
This module is to define pytest functions for content hosts

The functions in this module are read in the pytest_plugins/fixture_markers.py module
All functions in this module will be treated as fixtures that apply the contenthost mark
"""

from broker import Broker
import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.enums import NetworkType
from robottelo.hosts import ContentHost, Satellite


def host_conf(request):
    """A function that returns arguments for Broker host deployment"""
    conf = params = {}
    if hasattr(request, 'param'):
        params = request.param
    distro = params.get('distro', 'rhel')
    network = params.get('network')
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
        if deploy_kwargs and network:
            deploy_kwargs.update({'Container': str(network)})
    # if we're not using containers or a container isn't available, use a VM
    if not deploy_kwargs:
        deploy_kwargs = settings.content_host.get(_rhelver).to_dict().get('vm', {})
        if network:
            deploy_kwargs.update({'deploy_network_type': network})
    if network:
        # pass the network type to the deploy kwargs, so the host class can use it
        deploy_kwargs.update({'net_type': network})
    conf.update(deploy_kwargs)
    return conf


@pytest.fixture
def rhel_contenthost(request):
    """A function-level fixture that provides a content host object parametrized"""
    # Request should be parametrized through pytest_fixtures.fixture_markers
    # unpack params dict
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        yield host


@pytest.fixture(scope='module')
def module_rhel_contenthost(request):
    """A module-level fixture that provides a content host object parametrized"""
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


@pytest.fixture(params=[{'rhel_version': '9'}])
def rhel9_contenthost(request):
    """A fixture that provides a rhel9 content host object"""
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        yield host


@pytest.fixture
def content_hosts(request):
    """A function-level fixture that provides two rhel content hosts object"""
    with Broker(**host_conf(request), host_class=ContentHost, _count=2) as hosts:
        hosts[0].set_infrastructure_type('physical')
        yield hosts


@pytest.fixture(scope='module')
def mod_content_hosts(request):
    """A module-level fixture that provides two rhel content hosts object"""
    with Broker(**host_conf(request), host_class=ContentHost, _count=2) as hosts:
        hosts[0].set_infrastructure_type('physical')
        yield hosts


@pytest.fixture
def katello_host_tools_host(target_sat, module_org, rhel_contenthost):
    """Register content host to Satellite and install katello-host-tools on the host."""
    repo = settings.repos['SATCLIENT_REPO'][f'RHEL{rhel_contenthost.os_version.major}']
    ak = target_sat.api.ActivationKey(
        content_view=module_org.default_content_view,
        max_hosts=100,
        organization=module_org,
        environment=target_sat.api.LifecycleEnvironment(id=module_org.library.id),
        auto_attach=True,
    ).create()

    rhel_contenthost.register(module_org, None, ak.name, target_sat, repo_data=f'repo={repo}')
    rhel_contenthost.install_katello_host_tools()
    return rhel_contenthost


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
    return rhel_contenthost


@pytest.fixture
def rex_contenthost(request, module_org, target_sat, module_ak_with_cv):
    request.param['no_containers'] = True
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        repo = settings.repos['SATCLIENT_REPO'][f'RHEL{host.os_version.major}']
        host.register(
            module_org, None, module_ak_with_cv.name, target_sat, repo_data=f'repo={repo}'
        )
        yield host


@pytest.fixture
def rex_contenthosts(request, module_org, target_sat, module_ak_with_cv):
    request.param['no_containers'] = True
    with Broker(**host_conf(request), host_class=ContentHost, _count=2) as hosts:
        for host in hosts:
            repo = settings.repos['SATCLIENT_REPO'][f'RHEL{host.os_version.major}']
            host.register(
                module_org, None, module_ak_with_cv.name, target_sat, repo_data=f'repo={repo}'
            )
        yield hosts


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
    return rex_contenthost


@pytest.fixture
def rhel_contenthost_with_repos(request, target_sat):
    """Install katello-host-tools-tracer, create custom
    repositories on the host"""
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        # add IPv6 proxy for IPv6 communication
        if not host.network_type.has_ipv4:
            host.enable_ipv6_dnf_and_rhsm_proxy()
            host.enable_ipv6_system_proxy()

        # create a custom, rhel version-specific OS repo
        rhelver = host.os_version.major
        if rhelver > 7:
            host.create_custom_repos(**settings.repos[f'rhel{rhelver}_os'])
        else:
            host.create_custom_repos(**{f'rhel{rhelver}_os': settings.repos[f'rhel{rhelver}_os']})
        yield host


@pytest.fixture(scope='module')
def module_container_contenthost(request, module_target_sat, module_org, module_activation_key):
    """Fixture that installs docker on the content host"""
    request.param = {
        "rhel_version": "8",
        "distro": "rhel",
        "no_containers": True,
        "network": "ipv6" if module_target_sat.network_type == NetworkType.IPV6 else "ipv4",
    }
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        host.register_to_cdn()
        for client in settings.container.clients:
            assert host.execute(f'yum -y install {client}').status == 0, (
                f'{client} installation failed'
            )
        assert host.execute('systemctl enable --now podman').status == 0, (
            'Start of podman service failed'
        )
        host.unregister()
        assert (
            host.register(module_org, None, module_activation_key.name, module_target_sat).status
            == 0
        )
        yield host


@pytest.fixture(scope='module')
def module_flatpak_contenthost(request):
    request.param = {
        "rhel_version": "9",
        "distro": "rhel",
        "no_containers": True,
        "network": "ipv6" if settings.server.network_type == NetworkType.IPV6 else "ipv4",
    }
    with Broker(**host_conf(request), host_class=ContentHost) as host:
        host.register_to_cdn()
        res = host.execute('dnf -y install podman flatpak dbus-x11')
        assert res.status == 0, f'Initial installation failed: {res.stderr}'
        host.unregister()
        yield host


@pytest.fixture
def centos_host(request, version):
    request.param = {
        "rhel_version": version.split('.')[0],
        "distro": "centos",
        "no_containers": True,
    }
    with Broker(
        **host_conf(request),
        host_class=ContentHost,
        deploy_network_type=settings.content_host.network_type,
    ) as host:
        yield host


@pytest.fixture
def oracle_host(request, version):
    request.param = {
        "rhel_version": version.split('.')[0],
        "distro": "oracle",
        "no_containers": True,
    }
    with Broker(
        **host_conf(request),
        host_class=ContentHost,
        deploy_network_type=settings.content_host.network_type,
    ) as host:
        yield host


@pytest.fixture
def bootc_host():
    """Fixture to check out boot-c host"""
    with Broker(
        workflow='deploy-bootc',
        host_class=ContentHost,
        target_template='tpl-bootc-rhel-10.0',
        # TODO(sbible): Check whether this is valid for dualstack scenaro
        deploy_network_type='ipv6' if settings.server.network_type == NetworkType.IPV6 else 'ipv4',
    ) as host:
        assert (
            host.execute(
                f"echo '{constants.DUMMY_BOOTC_FACTS}' > /etc/rhsm/facts/bootc.facts"
            ).status
            == 0
        )
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
    # if 'deploy_rhel_version' is not set, let's default to what's in content_host.yaml
    deploy_args['deploy_rhel_version'] = deploy_args.get(
        'deploy_rhel_version', settings.content_host.default_rhel_version
    )
    deploy_args['workflow'] = 'deploy-rhel'
    with Broker(**deploy_args, host_class=Satellite) as host:
        yield host


@pytest.fixture
def fake_yum_repos(request, target_sat, module_org, module_product):
    """Create and sync 3 YUM repositories, with fake custom content, to target satellite."""
    repositories = {
        'yum_0': settings.repos.yum_0.url,
        'yum_6': settings.repos.yum_6.url,
        'yum_9': settings.repos.yum_9.url,
    }
    for repo, url in repositories.items():
        r = target_sat.api.Repository(
            product=module_product,
            url=url,
        ).create()
        r.sync()
        repositories[repo] = r.read()
    return list(repositories.values())


@pytest.fixture
def registered_contenthosts(request, target_sat, module_org, module_ak, module_cv, fake_yum_repos):
    """Create and register multiple contenthosts to satellite.
    Parametrize int `count` (num of registered hosts), default: 2.
        by passing a request containing param 'count'.
    Parametrize str `rhel` (deploy_rhel_version), default: DEFAULT_RHEL_VERSION.
        by passing a request containing param 'rhel'.
    Parametrize str `workflow` (used for checkout), default: 'deploy-template'.
        by passing a request containing param 'workflow'.

    default: No parametrization will result in 2 hosts of DEFAULT_RHEL Version.

    eg. distro=rhel10, count=5, default workflow:
        @pytest.mark.parametrize(
            'registered_contenthosts',
            [{'rhel': 10, 'count': 5}],
            indirect=True,
        )
    Note: Does Not make use of `markers.rhel_ver_match`,
        or `markers.rhel_ver_list`, leads to duplicate parametrizations.
    Three custom repositories will be synced & enabled initially,
    Add, enable, and sync any other repos to CV/AK for hosts, following fixture setup.
    """
    param = getattr(request, 'param', {})
    _config = host_conf(request)
    _config['_count'] = param.get('count', 2)
    assert all([isinstance(_config['_count'], int), _config['_count'] > 0]), (
        'Count must be an integer greater than zero.'
    )
    _config['workflow'] = param.get('workflow', 'deploy-rhel')
    assert isinstance(_config['workflow'], str)
    _config['deploy_rhel_version'] = str(
        param.get('rhel', settings.content_host.default_rhel_version)
    )
    _config['distro'] = 'rhel'
    _config['rhel_version'] = _config['deploy_rhel_version']
    # TODO: temp workflow until RHEL10 GA image is available
    # remove, ie use 'deploy-rhel' from default above
    if int(param.get('rhel', 0)) >= 10:
        _config['workflow'] = 'deploy-template'
    rhels_no_fips = constants.DISTROS_MAJOR_VERSION.values()  # type [int]
    rhels_w_fips = settings.supportability.content_hosts.rhel.versions  # type [str and int]
    if 'fips' in _config['deploy_rhel_version']:
        assert _config['deploy_rhel_version'] in rhels_w_fips, (
            f'{_config["deploy_rhel_version"]} not found in supported distros: \n{rhels_w_fips}'
        )
    else:
        assert int(_config['deploy_rhel_version']) in rhels_no_fips, (
            f'{_config["deploy_rhel_version"]} not found in supported distros: \n{rhels_no_fips}'
        )
    # Add the repos to CV, update, needs_publish should be True
    module_cv.repository = fake_yum_repos
    module_cv.update(['repository'])
    module_cv = module_cv.read()
    assert module_cv.needs_publish
    # Repositories (fixture: fake_yum_repos) already added to CV,
    # Checkout Broker host(s) via requested distro and count, or defaults.
    with Broker(
        **_config,
        host_class=ContentHost,
        deploy_network_type=settings.content_host.network_type,
    ) as content_hosts:
        for chost in content_hosts:
            # Add CV and 'Library' env to AK, publish a Version if needs_publish.
            # Register the client, override custom repositories to Enabled.
            setup = target_sat.api_factory.register_host_and_needed_setup(
                activation_key=module_ak,
                organization=module_org,
                content_view=module_cv,
                environment='Library',
                enable_repos=True,
                client=chost,
            )
            assert setup['result'] != 'error', f'{setup["message"]}'
            module_cv = setup['content_view'].read()
            # subscription-manager reports no error
            assert chost.execute('subscription-manager repos').status == 0
        yield content_hosts

    # cleanup: delete the fake_yum_repos,
    # first, remove environment and content-view associations from AK,
    # then, delete all of the module_cv version(s) which may contain the repos.
    module_ak = module_ak.read()
    module_ak.environment = []
    module_ak.content_view = None
    module_ak.update(['content_view', 'environment'])
    module_cv = module_cv.read()
    if len(module_cv.version) > 0:
        task = module_cv.remove_version(versions=module_cv.version)
        assert target_sat.api.ForemanTask(id=task['id']).poll()
        # delete the updated repositories
        for repo in fake_yum_repos:
            repo.read().delete()
