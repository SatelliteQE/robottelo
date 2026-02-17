"""Test class for Capsule Loadbalancer

:Requirement: Loadbalancer capsule

:CaseAutomation: Automated

:CaseComponent: ForemanProxy

:Team: Endeavour

:CaseImportance: High

"""

import pytest
from wrapanapi import VmState

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import CLIENT_PORT, DataFile
from robottelo.utils.installer import InstallerCommand

pytestmark = [pytest.mark.no_containers]


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

    module_cv.repository = rh_repos
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

    return {'client_ak': ak, 'client_lce': module_lce}


@pytest.fixture(scope='module')
def setup_capsules(
    module_org,
    module_location,
    module_haproxy,
    module_lb_capsules,
    module_target_sat,
    content_for_client,
):
    """Install capsules with loadbalancer options"""
    extra_cert_var = {'foreman-proxy-cname': module_haproxy.hostname}
    extra_installer_var = {'certs-cname': module_haproxy.hostname}

    for capsule in module_lb_capsules:
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
        module_target_sat.cli.Capsule.update(
            {
                'name': capsule.hostname,
                'organization-ids': module_org.id,
                'location-ids': module_location.id,
            }
        )

    return module_lb_capsules


@pytest.fixture(scope='module')
def setup_haproxy(
    module_org,
    module_haproxy,
    content_for_client,
    module_target_sat,
    setup_capsules,
):
    """Install and configure haproxy and setup logging"""
    # Using same AK for haproxy just for packages
    haproxy_ak = content_for_client['client_ak']
    module_haproxy.execute('firewall-cmd --add-service RH-Satellite-6-capsule')
    module_haproxy.execute('firewall-cmd --runtime-to-permanent')
    module_haproxy.register(module_org, None, haproxy_ak.name, module_target_sat)
    result = module_haproxy.execute('yum install -y haproxy policycoreutils-python-utils')
    assert result.status == 0
    config_file = '/etc/haproxy/haproxy.cfg'
    module_haproxy.execute(f'mv {config_file} {config_file}.bak')
    module_haproxy.session.sftp_write(
        source=DataFile.DATA_DIR.joinpath('haproxy.cfg'),
        destination=config_file,
    )
    module_haproxy.execute(
        f'sed -i -e s/CAPSULE_1/{setup_capsules[0].hostname}/g '
        f'-e s/CAPSULE_2/{setup_capsules[1].hostname}/g '
        f'{config_file}'
    )
    module_haproxy.execute('systemctl enable haproxy.service')
    module_haproxy.execute('semanage boolean -m --on haproxy_connect_any')
    # HAProxy logging setup
    module_haproxy.execute('mkdir /var/lib/haproxy/dev')
    module_haproxy.session.sftp_write(
        source=DataFile.DATA_DIR.joinpath('99-haproxy.conf'),
        destination='/etc/rsyslog.d/99-haproxy.conf',
    )
    module_haproxy.execute('setenforce permissive')  # logging setup requires permissive mode
    assert module_haproxy.execute('systemctl restart haproxy.service rsyslog.service').status == 0

    haproxy_url = f'https://{module_haproxy.hostname}:9090'
    # Enable Registration and Template Plugins
    opts = {
        'foreman-proxy-registration': 'true',
        'foreman-proxy-templates': 'true',
        'foreman-proxy-registration-url': f'{haproxy_url}',
        'foreman-proxy-template-url': f'{haproxy_url}',
    }
    for capsule in setup_capsules:
        assert capsule.install(InstallerCommand(installer_opts=opts)).status == 0, (
            'Installer failed to enable Registration and Template plugins with loadbalancer'
        )

    return module_haproxy


@pytest.mark.e2e
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_loadbalancer_install_package(
    setup_haproxy,
    setup_capsules,
    content_for_client,
    module_target_sat,
    module_org,
    module_location,
    rhel_contenthost,
    request,
):
    r"""Install packages on a content host regardless of the registered capsule being available

    :id: bd3c2e50-18e2-4be7-8a7f-c32472e17c61

    :steps:
        1. run `subscription-manager register --org=<Organization> --activationkey=<AK>`
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
        activation_keys=content_for_client['client_ak'].name,
        target=setup_capsules[0],
        force=True,
    )
    if rhel_contenthost.os_version.major != 6:
        assert result.status == 0, f'Failed to register host: {result.stderr}'

    # Try package installation
    result = rhel_contenthost.execute('yum install -y tree')
    assert result.status == 0

    hosts = module_target_sat.cli.Host.list({'organization-id': module_org.id})
    assert rhel_contenthost.hostname in [host['name'] for host in hosts]

    # Find which capsule the host is registered to since it's RoundRobin
    # The following also asserts the above result
    registered_to_capsule = (
        setup_capsules[0] if setup_capsules[0].hostname in result.stdout else setup_capsules[1]
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


@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_client_register_through_lb(
    setup_haproxy,
    setup_capsules,
    content_for_client,
    module_target_sat,
    module_org,
    module_location,
    rhel_contenthost,
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
        activation_keys=content_for_client['client_ak'].name,
        target=setup_capsules[0],
        force=True,
    )
    if rhel_contenthost.os_version.major != 6:
        assert result.status == 0, f'Failed to register host: {result.stderr}'
    assert setup_haproxy.hostname in rhel_contenthost.subscription_config['server']['hostname']
    assert rhel_contenthost.subscription_config['server']['port'] == CLIENT_PORT
    host_info = module_target_sat.cli.Host.info(
        {'name': rhel_contenthost.hostname}, output_format='json'
    )
    assert host_info['content-information']['content-source']['name'] in [
        setup_capsules[0].hostname,
        setup_capsules[1].hostname,
    ], 'Unexpected Content Source is set or missing'
    assert host_info['subscription-information']['registered-to'] == setup_haproxy.hostname, (
        'Unexpected registration server'
    )

    # Host registration by Second Capsule through Loadbalancer
    result = rhel_contenthost.register(
        org=module_org,
        loc=module_location,
        activation_keys=content_for_client['client_ak'].name,
        target=setup_capsules[1],
        force=True,
    )
    if rhel_contenthost.os_version.major != 6:
        assert result.status == 0, f'Failed to register host: {result.stderr}'
    assert setup_haproxy.hostname in rhel_contenthost.subscription_config['server']['hostname']
    assert rhel_contenthost.subscription_config['server']['port'] == CLIENT_PORT

    hosts = module_target_sat.cli.Host.list({'organization-id': module_org.id})
    assert rhel_contenthost.hostname in [host['name'] for host in hosts]
