"""Test class for Capsule Loadbalancer

:Requirement: Loadbalancer capsule

:CaseAutomation: Automated

:CaseLevel: Integration

:CaseComponent: Capsule

:Assignee: akjha

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import queue
import threading
from time import sleep

import pytest
from broker import Broker

from robottelo import constants
from robottelo.cli.capsule import Capsule as ContentCapsule
from robottelo.cli.factory import setup_org_for_a_custom_repo
from robottelo.config import settings
from robottelo.helpers import get_data_file
from robottelo.helpers import InstallerCommand
from robottelo.hosts import Capsule
from robottelo.hosts import ContentHost


@pytest.fixture(scope='session')
def get_hosts_from_broker():
    """Get hosts from broker.
       Using threading to reduce the checkout time.
    :return: Capsule and haproxy host
    """

    def _get_hosts(vm_nick, vm_count):
        if 'cap' in vm_nick:
            host_class = Capsule
        if 'rhel' in vm_nick:
            host_class = ContentHost

        host = Broker(nick=vm_nick, host_classes={'host': host_class}, _count=vm_count).checkout()
        q.put({vm_nick: host})

    threads = list()
    q = queue.Queue()
    results = dict()
    host_count = [['rhel7', 1], ['cap611_8', 1], ['cap611_7', 1]]
    for host in host_count:
        threads.append(threading.Thread(target=_get_hosts, args=(host[0], host[1])))
        sleep(1)
        threads[-1].start()
    _ = [t.join() for t in threads]

    while not q.empty():
        results.update(q.get())

    yield results

    all_hosts = [results['rhel7'], results['cap611_8'], results['cap611_7']]
    Broker(hosts=all_hosts).checkin()


@pytest.fixture(scope='module')
def content_for_client(module_org, module_target_sat, module_lce, module_cv, module_ak):
    """Setup content to be used by haproxy and client

    :return: Activation key, client lifecycle environment(used by setup_capsules())
    """
    setup_org_for_a_custom_repo(
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
def setup_capsules(module_org, get_hosts_from_broker, module_target_sat, content_for_client):
    """Install capsules with loadbalancer options"""
    extra_cert_var = {'foreman-proxy-cname': get_hosts_from_broker['rhel7'].hostname}
    extra_installer_var = {'certs-cname': get_hosts_from_broker['rhel7'].hostname}

    for capsule in [get_hosts_from_broker['cap611_8'], get_hosts_from_broker['cap611_7']]:
        capsule.register_contenthost(
            org=None,
            lce=None,
            username=settings.subscription.rhn_username,
            password=settings.subscription.rhn_password,
        )
        result = capsule.subscription_manager_attach_pool([settings.subscription.rhn_poolid])[0]
        assert result.status == 0
        version = capsule.os_version.major
        for repo in getattr(constants, f'OHSNAP_RHEL{version}_REPOS'):
            capsule.enable_repo(repo=repo, force=True)
        capsule.download_repos(repo_name='capsule', version=version)

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
        ContentCapsule.content_add_lifecycle_environment(
            {
                'id': capsule.nailgun_capsule.id,
                'organization-id': module_org.id,
                'environment': content_for_client['client_lce'].name,
            }
        )
        ContentCapsule.content_synchronize(
            {'id': capsule.nailgun_capsule.id, 'organization-id': module_org.id}
        )
    yield {
        'capsule_1': get_hosts_from_broker["cap611_8"],
        'capsule_2': get_hosts_from_broker["cap611_7"],
    }

    _ = [
        capsule.unregister()
        for capsule in [get_hosts_from_broker['cap611_8'], get_hosts_from_broker['cap611_7']]
    ]


@pytest.fixture(scope='module')
def setup_haproxy(
    module_org, get_hosts_from_broker, content_for_client, module_target_sat, setup_capsules
):
    """Install and configure haproxy and setup logging"""
    haproxy = get_hosts_from_broker['rhel7']
    client_ak = content_for_client['client_ak']
    haproxy.execute('firewall-cmd --add-service RH-Satellite-6-capsule')
    haproxy.execute('firewall-cmd --runtime-to-permanent')
    haproxy.install_katello_ca(module_target_sat)
    haproxy.register_contenthost(module_org.label, client_ak.name)
    result = haproxy.execute('yum install haproxy policycoreutils-python -y')
    assert result.status == 0
    haproxy.execute('rm -r /etc/haproxy/haproxy.cfg')
    haproxy.session.sftp_write(
        source=get_data_file('haproxy.cfg'), destination='/etc/haproxy/haproxy.cfg'
    )
    haproxy.execute(
        f'sed -i -e s/CAPSULE_1/{setup_capsules["capsule_1"].hostname}/g '
        f' --e s/CAPSULE_2/{setup_capsules["capsule_2"].hostname}/g '
        f' /etc/haproxy/haproxy.cfg'
    )
    haproxy.execute('systemctl restart haproxy.service')
    haproxy.execute('mkdir /var/lib/haproxy/dev')
    haproxy.session.sftp_write(
        source=get_data_file('99-haproxy.conf'), destination='/etc/rsyslog.d/99-haproxy.conf'
    )
    haproxy.execute('setenforce Permissive')
    result = haproxy.execute('systemctl restart haproxy.service rsyslog.service')
    assert result.status == 0

    return {'haproxy': haproxy}


@pytest.fixture(scope='module')
def loadbalancer_setup(
    module_org, content_for_client, setup_capsules, module_target_sat, setup_haproxy
):
    """Just to keep the tests arguments clean. Yes it's redundant"""
    return {
        'module_org': module_org,
        'content_for_client': content_for_client,
        'setup_capsules': setup_capsules,
        'module_target_sat': module_target_sat,
        'setup_haproxy': setup_haproxy,
    }


@pytest.mark.dependency()
@pytest.mark.tier1
def test_loadbalancer_register_client_using_ak_to_capsule(loadbalancer_setup, rhel7_contenthost):
    """Register the client using ak to the capsule

    :id: 7318c380-e149-11ea-9b17-4ceb42ab8dbc

    :Steps:
        1. run `subscription-manager register --org=Your_Organization \
            --activationkey=Your_Activation_Key \
            --serverurl=https://loadbalancer.example.com:8443/rhsm \
            --baseurl=https://loadbalancer.example.com/pulp/repos`

    :expectedresults: The client should be registered to one of the capsules

    :CaseLevel: Integration
    """
    url = f'https://{loadbalancer_setup["setup_haproxy"]["haproxy"].hostname}'
    server_url = f'{url}:8443/rhsm'
    base_url = f'{url}/pulp/content/'
    result = rhel7_contenthost.download_install_rpm(
        repo_url=f'{url}/pub', package_name='katello-ca-consumer-latest.noarch'
    )
    assert result.status == 0
    rhel7_contenthost.register_contenthost(
        org=loadbalancer_setup['module_org'].label,
        activation_key=loadbalancer_setup['content_for_client']['client_ak'].name,
        serverurl=server_url,
        baseurl=base_url,
    )
    result = rhel7_contenthost.execute('rpm -qa |grep katello-ca-consumer')
    assert (
        loadbalancer_setup['setup_capsules']['capsule_1'].hostname
        or loadbalancer_setup['setup_capsules']['capsule_2'].hostname in result.stdout
    )


@pytest.mark.dependency(depends=['test_loadbalancer_register_client_using_ak_to_capsule'])
@pytest.mark.tier1
def test_list_repolist():
    """List all the repositories

    :id: 973c8eb2-e14a-11ea-9a77-4ceb42ab8dbc

    :Steps: Run `yum repolist`

    :expectedresults: all the repositories are listed

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_register_using_bootstrap():
    """Register the client using bootstrap.py

    :id: ff041894-e14a-11ea-9a77-4ceb42ab8dbc

    :Steps:
        1. Download the bootstrap.py and change the permissions of the script.
        2. Run `python bootstrap.py --login=admin \
                --server loadbalancer.example.com \
                --organization="Your_Organization" \
                --location="Your_Location" \
                --hostgroup="Your_Hostgroup" \
                --activationkey=your_activation_key \
                --puppet-ca-port 8141 \
                --force`

    :expectedresults:
        1. Registration should be Successful
        2. Puppet Agent Installed
        3. CA cert AutoSigned
        4. Facts Uploaded to Satellite
    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_package_action_from_host():
    """Package installation on client

    :id: e8a3eefa-e14d-11ea-9a77-4ceb42ab8dbc

    :Steps: Run `yum install -y <package_name>`

    :expectedresults: Desired package is installed

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_loadbalancer_down():
    """Loadbalancer service/VM down

    :id: 4fc2656c-e14e-11ea-9a77-4ceb42ab8dbc

    :Steps:
        1. Stop loadbalancer service
        2. Try installing a package
        3. Start loadbalancer service
        4. Try installing a package
        5. Power off loadbalancer VM
        6. Try installing a package
        7. Power on loadbalancer VM
        8. Try installing a package

    :expectedresults:
        1. Service down: package installation fail
        2. Service up: package installation successful
        3. VM down: package installation fail
        4. VM up: package installation successful

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_capsule_down():
    """Capsule service/VM down

    :id: 887f8172-e14f-11ea-9a77-4ceb42ab8dbc

    Steps:
        1. Stop capsule_1 service
        2. Try installing a package
        3. Start capsule_1 service and stop capsule_2 service
        4. Try installing a package.
        5. Start capsule_2 service. Power off capsule_1 vm
        6. Try installing a package
        7. Start capsule_1 vm. Power off capsule_2 vm
        8. Try installing a package
        9. Both capsules vm down
        10. Try installing a package
        11. Start both capsules

    :expectedresults:
        1. Package installation successful from capsule_2(see haproxy logs)
        2. Package installation successful from capsule_1(see haproxy logs)
        3. Package installation successful from capsule_2(see haproxy logs)
        4. Package installation successful from capsule_1(see haproxy logs)
        5. Package installation fail

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_remote_execution_on_client():
    """Remote Execution on client

    :id: e911acb4-e153-11ea-9a77-4ceb42ab8dbc

    :Steps:
        1. Enable foreman-proxy-plugin-remote-execution-script on capsules
        2. Create ansible role and remote job, attach to the host(here client) and run the job

    :expectedresults:
        1. Ansible job is successful
        2. Remote job is successful

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_openscap_reporting():
    """openscap report to be uploaded

    :id: cfba6e54-e158-11ea-9a77-4ceb42ab8dbc

    :Steps:
        1. Run `Puppet agent -t --noop`
        2. Run `foreman-scap-client <id>`

    :expectedresults:
        1. Should create openscap config file
        2. Should upload reports to sat
    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_capsule_3():
    """Tests for capsule_3

    :id: 16fc8490-e15a-11ea-9a77-4ceb42ab8dbc

    :Steps:
        1. Install capsule_3 and register as "The initial setup[5]".
        2. Unregister and remove katello-ca-consumer-latest. Re-register the client.
        3. Try package installation.
        4. Run `puppet agent -t -v`.
        5. Capsule_1 and capsule_2 service down.
        6. Capsule_1 and capsule_2 VM down.
        7. Capsule_1 and capsule_2 VM up.

    :expectedresults:
        1. Capsule_3 install successful
        2. Package installation is successful
        3. Scap reports upload to satellite should be served through capsule_3
        4. Request to be severed by capsule_3 when capsule_1 and capsule_2 service/VM are down.
        5. On starting the services/VM on down capsules, all the capsules including capsule_3
            should serve the client requests
    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_multiclient():
    """Testing multiple clients to test the loadbalancer functionality

    :id: 8b59c69c-e15d-11ea-9a77-4ceb42ab8dbc

    :Steps: Use docker to spin new container client

    :expectedresults: All the clients(from docker) are registered to the capsules.

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_upgrade_the_setup():
    """Upgrading the setup previous GA to current snap

    :id: 64446c14-e15e-11ea-9a77-4ceb42ab8dbc

    :Steps:
        0. Create a setup from GA
        1. Sync new packages in the capsules content view
        2. Upgrade the satellite, upgrade the capsules.

    :expectedresults: The setup should works before and after the upgrade

    """
    pass
