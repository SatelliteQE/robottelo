"""Test class for Capsule Loadbalancer

:Requirement: Loadbalancer capsule

:CaseAutomation: Automated

:CaseLevel: Integration

:CaseComponent: Capsule

:Team: Platform

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from wrapanapi import VmState

from robottelo.config import settings
from robottelo.constants import DataFile
from robottelo.utils.installer import InstallerCommand

pytestmark = [pytest.mark.no_containers, pytest.mark.destructive]


@pytest.fixture(scope='module')
def content_for_client(module_target_sat, module_org, module_lce, module_cv, module_ak):
    """Setup content to be used by haproxy and client

    :return: Activation key, client lifecycle environment(used by setup_capsules())
    """
    module_target_sat.cli_factory.setup_org_for_a_custom_repo(
        {
            'url': settings.repos.RHEL7_OS,
            'organization-id': module_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': module_ak.id,
        }
    )
    return {'client_ak': module_ak, 'client_lce': module_lce}


@pytest.fixture(scope='module')
def setup_capsules(
    module_org, rhel7_contenthost_module, module_lb_capsule, module_target_sat, content_for_client
):
    """Install capsules with loadbalancer options"""
    extra_cert_var = {'foreman-proxy-cname': rhel7_contenthost_module.hostname}
    extra_installer_var = {'certs-cname': rhel7_contenthost_module.hostname}

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

    yield {
        'capsule_1': module_lb_capsule[0],
        'capsule_2': module_lb_capsule[1],
    }


@pytest.fixture(scope='module')
def setup_haproxy(
    module_org, rhel7_contenthost_module, content_for_client, module_target_sat, setup_capsules
):
    """Install and configure haproxy and setup logging"""
    haproxy = rhel7_contenthost_module
    # Using same AK for haproxy just for packages
    haproxy_ak = content_for_client['client_ak']
    haproxy.execute('firewall-cmd --add-service RH-Satellite-6-capsule')
    haproxy.execute('firewall-cmd --runtime-to-permanent')
    haproxy.install_katello_ca(module_target_sat)
    haproxy.register_contenthost(module_org.label, haproxy_ak.name)
    result = haproxy.execute('yum install haproxy policycoreutils-python -y')
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
    module_org, content_for_client, setup_capsules, module_target_sat, setup_haproxy
):
    return {
        'module_org': module_org,
        'content_for_client': content_for_client,
        'setup_capsules': setup_capsules,
        'module_target_sat': module_target_sat,
        'setup_haproxy': setup_haproxy,
    }


@pytest.mark.tier1
def test_loadbalancer_install_package(
    loadbalancer_setup, setup_capsules, rhel7_contenthost, module_org, module_location, request
):
    r"""Install packages on a content host regardless of the registered capsule being available

    :id: bd3c2e50-18e2-4be7-8a7f-c32472e17c61

    :Steps:
        1. run `subscription-manager register --org=Your_Organization \
            --activationkey=Your_Activation_Key \`
        2. Try package installation
        3. Check which capsule the host got registered.
        4. Remove the package
        5. Take down the capsule that the host was registered to
        6. Try package installation again

    :expectedresults: The client should be get the package irrespective of the capsule
        registration.

    :CaseLevel: Integration
    """
    # Register content host
    result = rhel7_contenthost.register(
        org=module_org,
        loc=module_location,
        activation_keys=loadbalancer_setup['content_for_client']['client_ak'].name,
        target=setup_capsules['capsule_1'],
        force=True,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'

    # Try package installation
    result = rhel7_contenthost.execute('yum install -y tree')
    assert result.status == 0

    hosts = loadbalancer_setup['module_target_sat'].cli.Host.list(
        {'organization-id': loadbalancer_setup['module_org'].id}
    )
    assert rhel7_contenthost.hostname in [host['name'] for host in hosts]

    result = rhel7_contenthost.execute('rpm -qa | grep katello-ca-consumer')

    # Find which capsule the host is registered to since it's RoundRobin
    # The following also asserts the above result
    registered_to_capsule = (
        loadbalancer_setup['setup_capsules']['capsule_1']
        if loadbalancer_setup['setup_capsules']['capsule_1'].hostname in result.stdout
        else loadbalancer_setup['setup_capsules']['capsule_2']
    )

    # Remove the packages from the client
    result = rhel7_contenthost.execute('yum remove -y tree')
    assert result.status == 0

    # Power off the capsule that the client is registered to
    registered_to_capsule.power_control(state=VmState.STOPPED, ensure=True)

    # Try package installation again
    result = rhel7_contenthost.execute('yum install -y tree')
    assert result.status == 0

    @request.addfinalizer
    def _finalize():
        registered_to_capsule.power_control(state=VmState.RUNNING, ensure=True)
