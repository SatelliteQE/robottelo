"""Test class for Capsule Loadbalancer

:Requirement: Loadbalancer capsule

:CaseAutomation: Automated

:CaseComponent: ForemanProxy

:Team: Endeavour

:CaseImportance: High

"""

import pytest
from wait_for import wait_for
from wrapanapi import VmState

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import CLIENT_PORT, DataFile
from robottelo.utils.datafactory import gen_string
from robottelo.utils.installer import InstallerCommand

pytestmark = [pytest.mark.no_containers, pytest.mark.destructive]


@pytest.fixture(scope='module')
def content_for_client(module_target_sat, module_sca_manifest_org, module_lce, module_cv):
    """Setup content to be used by haproxy and client

    :return: Activation key, client lifecycle environment(used by setup_capsules())
    """
    rhel_ver = settings.content_host.default_rhel_version
    baseos = f'rhel{rhel_ver}_bos'
    appstream = f'rhel{rhel_ver}_aps'

    rh_repos = []
    for repo in [baseos, appstream]:
        synced_repo_id = module_target_sat.api_factory.enable_sync_redhat_repo(
            constants.REPOS[repo], module_sca_manifest_org.id
        )
        repo = module_target_sat.api.Repository(id=synced_repo_id).read()
        rh_repos.append(repo)

    product = gen_string('alpha')
    container_repo_id = module_target_sat.api_factory.create_sync_custom_repo(
        module_sca_manifest_org.id,
        repo_type='docker',
        repo_url=settings.container.registry_hub,
        docker_upstream_name=settings.container.upstream_name,
        product_name=product,
    )
    container_repo = module_target_sat.api.Repository(id=container_repo_id).read()
    path = f'{module_sca_manifest_org.label}/{module_lce.label}/{module_cv.label}/{product}/{container_repo.label}'.lower()

    module_cv.repository = rh_repos + [container_repo]
    module_cv.update(['repository'])
    module_cv.publish()
    module_cv = module_cv.read()
    cvv = module_cv.version[0]
    cvv.promote(data={'environment_ids': module_lce.id})
    module_cv = module_cv.read()
    ak = module_target_sat.api.ActivationKey(
        content_view=module_cv,
        environment=module_lce,
        organization=module_sca_manifest_org,
    ).create()

    return {'client_ak': ak, 'client_lce': module_lce, 'container_path': path}


@pytest.fixture(scope='module')
def setup_capsules(
    module_org,
    module_rhel_contenthost,
    module_lb_capsule,
    module_target_sat,
    content_for_client,
):
    """Install capsules with loadbalancer options"""
    extra_cert_var = {'foreman-proxy-cname': module_rhel_contenthost.hostname}
    extra_installer_var = {'certs-cname': module_rhel_contenthost.hostname}

    for capsule in module_lb_capsule:
        capsule.register_to_cdn()
        command = InstallerCommand(
            command='capsule-certs-generate',
            foreman_proxy_fqdn=capsule.hostname,
            certs_tar=f'/root/{capsule.hostname}-certs.tar',
            **extra_cert_var,
        )
        result = module_target_sat.execute(command.get_command())
        install_cmd = InstallerCommand.from_cmd_str(cmd_str=result.stdout)
        install_cmd.opts['certs-tar-file'] = f'/root/{capsule.hostname}-certs.tar'
        module_target_sat.satellite.session.remote_copy(install_cmd.opts['certs-tar-file'], capsule)
        install_cmd.opts.update(**extra_installer_var)
        result = capsule.install(install_cmd)
        assert result.status == 0
        capsule._satellite = module_target_sat
        for i in module_target_sat.cli.Capsule.list():
            if i['name'] == capsule.hostname:
                capsule_id = i['id']
                break

        module_target_sat.cli.Capsule.content_add_lifecycle_environment(
            {
                'id': capsule_id,
                'organization-id': module_org.id,
                'lifecycle-environment': content_for_client['client_lce'].name,
            }
        )
        module_target_sat.cli.Capsule.content_synchronize(
            {'id': capsule_id, 'organization-id': module_org.id}
        )

    return {
        'capsule_1': module_lb_capsule[0],
        'capsule_2': module_lb_capsule[1],
    }


@pytest.fixture(scope='module')
def setup_haproxy(
    module_org,
    module_rhel_contenthost,
    content_for_client,
    module_target_sat,
    setup_capsules,
):
    """Install and configure haproxy and setup logging"""
    haproxy = module_rhel_contenthost
    # Using same AK for haproxy just for packages
    haproxy_ak = content_for_client['client_ak']
    haproxy.execute('firewall-cmd --add-service RH-Satellite-6-capsule')
    haproxy.execute('firewall-cmd --runtime-to-permanent')
    haproxy.register(module_org, None, haproxy_ak.name, module_target_sat)
    result = haproxy.execute('yum install haproxy policycoreutils-python-utils -y')
    assert result.status == 0
    haproxy.execute('rm -f /etc/haproxy/haproxy.cfg')
    haproxy.session.sftp_write(
        source=DataFile.DATA_DIR.joinpath('haproxy.cfg'),
        destination='/etc/haproxy/haproxy.cfg',
    )
    haproxy.execute(
        f'sed -i -e s/CAPSULE_1/{setup_capsules["capsule_1"].hostname}/g '
        f' --e s/CAPSULE_2/{setup_capsules["capsule_2"].hostname}/g '
        f' /etc/haproxy/haproxy.cfg'
    )
    haproxy.execute('systemctl restart haproxy.service')
    haproxy.execute('mkdir /var/lib/haproxy/dev')
    haproxy.session.sftp_write(
        source=DataFile.DATA_DIR.joinpath('99-haproxy.conf'),
        destination='/etc/rsyslog.d/99-haproxy.conf',
    )
    haproxy.execute('setenforce permissive')
    result = haproxy.execute('systemctl restart haproxy.service rsyslog.service')
    assert result.status == 0

    return {'haproxy': haproxy}


@pytest.fixture(scope='module')
def loadbalancer_setup(
    module_org,
    content_for_client,
    setup_capsules,
    module_target_sat,
    setup_haproxy,
    module_location,
):
    lb_hostname = setup_haproxy['haproxy'].hostname
    haproxy_url = f'https://{lb_hostname}:9090'

    for capsule in setup_capsules.values():
        # Enable Registration and Template Plugins
        opts = {
            'foreman-proxy-registration': 'true',
            'foreman-proxy-templates': 'true',
            'foreman-proxy-registration-url': f'{haproxy_url}',
            'foreman-proxy-template-url': f'{haproxy_url}',
        }
        capsule.install(InstallerCommand(installer_opts=opts))

        module_target_sat.cli.Capsule.update(
            {
                'name': capsule.hostname,
                'organization-ids': module_org.id,
                'location-ids': module_location.id,
            }
        )

    return {
        'module_org': module_org,
        'content_for_client': content_for_client,
        'setup_capsules': setup_capsules,
        'module_target_sat': module_target_sat,
        'setup_haproxy': setup_haproxy,
    }


@pytest.mark.e2e
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_loadbalancer_install_package(
    loadbalancer_setup, setup_capsules, rhel_contenthost, module_org, module_location, request
):
    r"""Install packages on a content host regardless of the registered capsule being available

    :id: bd3c2e50-18e2-4be7-8a7f-c32472e17c61

    :steps:
        1. run `subscription-manager register --org=Your_Organization \
            --activationkey=Your_Activation_Key \`
        2. Try package installation
        3. Check which capsule the host got registered.
        4. Remove the package
        5. Take down the capsule that the host was registered to
        6. Try package installation again

    :expectedresults: The client should be get the package irrespective of the capsule
        registration.

        """

    # Register content host
    result = rhel_contenthost.register(
        org=module_org,
        loc=module_location,
        activation_keys=loadbalancer_setup['content_for_client']['client_ak'].name,
        target=setup_capsules['capsule_1'],
        force=True,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'

    # Try package installation
    result = rhel_contenthost.execute('yum install -y tree')
    assert result.status == 0

    hosts = loadbalancer_setup['module_target_sat'].cli.Host.list(
        {'organization-id': loadbalancer_setup['module_org'].id}
    )
    assert rhel_contenthost.hostname in [host['name'] for host in hosts]

    # Find which capsule the host is registered to since it's RoundRobin
    # The following also asserts the above result
    registered_to_capsule = (
        loadbalancer_setup['setup_capsules']['capsule_1']
        if loadbalancer_setup['setup_capsules']['capsule_1'].hostname in result.stdout
        else loadbalancer_setup['setup_capsules']['capsule_2']
    )
    request.addfinalizer(
        lambda: registered_to_capsule.power_control(state=VmState.RUNNING, ensure=True)
    )

    # Remove the packages from the client
    result = rhel_contenthost.execute('yum remove -y tree')
    assert result.status == 0

    # Power off the capsule that the client is registered to
    registered_to_capsule.power_control(state=VmState.STOPPED, ensure=True)

    # Try package installation again
    result = rhel_contenthost.execute('yum install -y tree')
    assert result.status == 0


@pytest.mark.e2e
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_loadbalancer_container(
    loadbalancer_setup, setup_capsules, rhel_contenthost, module_org, module_location, request
):
    """Search and pull container images on a content host regardless the capsule availability

    :id: 99539bc0-3dd2-49ab-9a43-9cb5cfd9fdce

    :steps:
        1. Register a host via setup AK and install podman.
        2. Podman login to the load balancer.
        3. Try to search and pull container image when only one of the Capsules is running.

    :expectedresults:
        1. Content host can podman login to the load balancer.
        2. Content host can search and pull a container image from any available Capsule.

    """
    lb = loadbalancer_setup["setup_haproxy"]["haproxy"].hostname
    c1 = loadbalancer_setup['setup_capsules']['capsule_1']
    c2 = loadbalancer_setup['setup_capsules']['capsule_2']

    # Register a host via setup AK and install podman.
    result = rhel_contenthost.register(
        org=module_org,
        loc=module_location,
        activation_keys=loadbalancer_setup['content_for_client']['client_ak'].name,
        target=c1,
        force=True,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    result = rhel_contenthost.execute('yum install -y podman')
    assert result.status == 0

    # Podman login to the load balancer.
    assert (
        rhel_contenthost.execute(
            f'podman login -u {settings.server.admin_username} '
            f'-p {settings.server.admin_password} {lb}'
        ).status
        == 0
    )

    @request.addfinalizer
    def _finalize():
        rhel_contenthost.execute(f'podman logout {lb}')
        c1.power_control(state=VmState.RUNNING, ensure=True)
        c2.power_control(state=VmState.RUNNING, ensure=True)

    # Try to search and pull container image when only one of the Capsules is running.
    path = loadbalancer_setup['content_for_client']['container_path']

    c1.power_control(state=VmState.STOPPED, ensure=True)
    wait_for(  # provide a few seconds to the HA proxy to recognize new situation
        lambda: path in rhel_contenthost.execute(f'podman search {lb}/{path}').stdout,
        timeout=30,
        delay=5,
    )
    assert rhel_contenthost.execute(f'podman pull {lb}/{path}').status == 0
    assert rhel_contenthost.execute('podman rmi -a').status == 0

    c1.power_control(state=VmState.RUNNING, ensure=True)
    c2.power_control(state=VmState.STOPPED, ensure=True)
    wait_for(  # provide a few seconds to the HA proxy to recognize new situation
        lambda: path in rhel_contenthost.execute(f'podman search {lb}/{path}').stdout,
        timeout=30,
        delay=5,
    )
    assert rhel_contenthost.execute(f'podman pull {lb}/{path}').status == 0
    assert rhel_contenthost.execute('podman rmi -a').status == 0


@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_client_register_through_lb(
    loadbalancer_setup,
    rhel_contenthost,
    module_org,
    module_location,
    setup_capsules,
):
    """Register the client through loadbalancer

    :id: c7e47d61-167b-4fc2-8d1a-d9a64350fdc4

    :steps:
        1. Setup capsules, host and loadbalancer.
        2. Generate curl command for host registration.
        3. Register host through loadbalancer using global registration.

    :expectedresults: Global Registration should have option to register through
        loadbalancer and host should get registered successfully with Content Source set.

    :BZ: 1963266, 2254612

    :customerscenario: true
    """
    result = rhel_contenthost.register(
        org=module_org,
        loc=module_location,
        activation_keys=loadbalancer_setup['content_for_client']['client_ak'].name,
        target=setup_capsules['capsule_1'],
        force=True,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    assert (
        loadbalancer_setup['setup_haproxy']['haproxy'].hostname
        in rhel_contenthost.subscription_config['server']['hostname']
    )
    assert rhel_contenthost.subscription_config['server']['port'] == CLIENT_PORT
    host_info = loadbalancer_setup['module_target_sat'].cli.Host.info(
        {'name': rhel_contenthost.hostname}, output_format='json'
    )
    assert host_info['content-information']['content-source']['name'] in [
        setup_capsules['capsule_1'].hostname,
        setup_capsules['capsule_2'].hostname,
    ], 'Unexpected Content Source is set or missing'
    assert (
        host_info['subscription-information']['registered-to']
        == loadbalancer_setup['setup_haproxy']['haproxy'].hostname
    ), 'Unexpected registration server'

    # Host registration by Second Capsule through Loadbalancer
    result = rhel_contenthost.register(
        org=module_org,
        loc=module_location,
        activation_keys=loadbalancer_setup['content_for_client']['client_ak'].name,
        target=setup_capsules['capsule_2'],
        force=True,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    assert (
        loadbalancer_setup['setup_haproxy']['haproxy'].hostname
        in rhel_contenthost.subscription_config['server']['hostname']
    )
    assert rhel_contenthost.subscription_config['server']['port'] == CLIENT_PORT

    hosts = loadbalancer_setup['module_target_sat'].cli.Host.list(
        {'organization-id': loadbalancer_setup['module_org'].id}
    )
    assert rhel_contenthost.hostname in [host['name'] for host in hosts]
