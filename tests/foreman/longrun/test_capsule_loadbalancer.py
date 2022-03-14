"""Test class for Capsule Loadbalancer

:Requirement: Loadbalancer capsule

:CaseAutomation: ManualOnly

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
from broker import VMBroker
from nailgun import entities

from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.hosts import ContentHost


@pytest.fixture(scope='session')
def get_hosts_from_broker():
    def local_get_hosts(_nick, count):
        host = VMBroker(nick=_nick, host_classes={'host': ContentHost}, _count=count).checkout()
        q.put({_nick: host})

    threads = list()
    q = queue.Queue()
    results = dict()
    host_count = [['rhel7', 2], ['rhel8', 1], ['cap610', 2]]
    for host in host_count:
        threads.append(threading.Thread(target=local_get_hosts, args=(host[0], host[1])))
        sleep(2)
        threads[-1].start()
    _ = [t.join() for t in threads]

    while not q.empty():
        results.update(q.get())

    assert len(results['rhel7']) == 2, 'host not provisioned'
    assert len([results['rhel8']]) == 1, 'host not provisioned'
    assert len(results['cap610']) == 2, 'host not provisioned'

    yield results

    all_hosts = results['rhel7'] + results['cap610'] + [results['rhel8']]

    VMBroker(hosts=all_hosts).checkin()


@pytest.fixture(scope='module')
def setup_lb_content(module_org, get_hosts_from_broker):
    # Red Hat Enterprise Linux 7 Server (RPMs)
    rhel7_product = entities.Product(organization=module_org).create()
    rhel7_repo = entities.Repository(
        product=rhel7_product,
    ).create()
    rhel7_repo.url = settings.repos.RHEL7_OS
    rhel7_repo = rhel7_repo.update(['url'])

    # Red Hat Software Collections RPMs for Red Hat Enterprise Linux 7 Server
    rhscl_product = entities.Product(organization=module_org).create()
    rhscl_repo = entities.Repository(
        product=rhscl_product,
    ).create()
    rhscl_repo.url = settings.repos.RHSCL_REPO
    rhscl_repo = rhscl_repo.update(['url'])

    # Red Hat Ansible Engine 2.9 RPMs for Red Hat Enterprise Linux 7 Server
    ansible_product = entities.Product(organization=module_org).create()
    ansible_repo = entities.Repository(
        product=ansible_product,
    ).create()
    ansible_repo.url = settings.repos.ANSIBLE_REPO
    ansible_repo = ansible_repo.update(['url'])

    # Red Hat Enterprise Linux 8 for x86_64 - BaseOS
    rhel8_product = entities.Product(organization=module_org).create()
    rhel8_repo = entities.Repository(
        product=rhel8_product,
    ).create()
    rhel8_repo.url = settings.repos.RHEL8_OS.BASEOS
    rhel8_repo = rhel8_repo.update(['url'])

    # Satellite Maintenance 6
    sat_maintenance_product = entities.Product(organization=module_org).create()
    sat_maintenance_repo = entities.Repository(
        product=sat_maintenance_product,
    ).create()
    sat_maintenance_repo.url = settings.repos.SATMAINTENANCE_REPO
    sat_maintenance_repo = sat_maintenance_repo.update(['url'])

    # Satellite Capsule 6.10
    satellite_capsule_product = entities.Product(organization=module_org).create()
    satellite_capsule_repo = entities.Repository(
        product=satellite_capsule_product,
    ).create()
    satellite_capsule_repo.url = settings.repos.CAPSULE_REPO
    satellite_capsule_repo = satellite_capsule_repo.update(['url'])

    # Satellite Tools RHEL 7
    satellite_tools_rhel7_product = entities.Product(organization=module_org).create()
    satellite_tools_rhel7_repo = entities.Repository(
        product=satellite_tools_rhel7_product,
    ).create()
    satellite_tools_rhel7_repo.url = settings.repos.SATTOOLS_REPO.RHEL7
    satellite_tools_rhel7_repo = satellite_tools_rhel7_repo.update(['url'])

    # Satellite Tools RHEL 8
    satellite_tools_rhel8_product = entities.Product(organization=module_org).create()
    satellite_tools_rhel8_repo = entities.Repository(
        product=satellite_tools_rhel8_product,
    ).create()
    satellite_tools_rhel8_repo.url = settings.repos.SATTOOLS_REPO.RHEL8
    satellite_tools_rhel8_repo = satellite_tools_rhel8_repo.update(['url'])

    repo_list = [
        rhel7_repo,
        ansible_repo,
        rhel8_repo,
        rhscl_repo,
        sat_maintenance_repo,
        satellite_capsule_repo,
        satellite_tools_rhel7_repo,
        satellite_tools_rhel8_repo,
    ]

    product_ids = [repo.product.id for repo in repo_list]

    entities.ProductBulkAction().sync(data={'ids': product_ids})

    # Create LCEs
    capsule_lce = entities.LifecycleEnvironment(organization=module_org).create()
    client7_lce = entities.LifecycleEnvironment(organization=module_org).create()
    client8_lce = entities.LifecycleEnvironment(organization=module_org).create()

    # Create Content Views
    capsule_cv = entities.ContentView(
        organization=module_org,
        repository=[
            rhel7_repo,
            satellite_capsule_repo,
            satellite_tools_rhel7_repo,
            sat_maintenance_repo,
            ansible_repo,
            rhscl_repo,
        ],
    ).create()
    capsule_cv.publish()
    capsule_cv = capsule_cv.read().version[0].read()
    promote(capsule_cv, capsule_lce.id)

    client7_cv = entities.ContentView(
        organization=module_org, repository=[rhel7_repo, satellite_tools_rhel7_repo]
    ).create()
    client7_cv.publish()
    client7_cv = client7_cv.read().version[0].read()
    promote(client7_cv, client7_lce.id)

    client8_cv = entities.ContentView(
        organization=module_org, repository=[rhel8_repo, satellite_tools_rhel8_repo]
    ).create()
    client8_cv.publish()
    client8_cv = client8_cv.read().version[0].read()
    promote(client8_cv, client8_lce.id)

    # Create Activation Keys
    capsule_ak = entities.ActivationKey(
        content_view=capsule_cv.id, organization=module_org, environment=capsule_lce
    ).create()
    client7_ak = entities.ActivationKey(
        content_view=client7_cv.id, organization=module_org, environment=client7_lce
    ).create()
    client8_ak = entities.ActivationKey(
        content_view=client8_cv.id, organization=module_org, environment=client8_lce
    ).create()

    # Add the subscriptions
    org_subscriptions = entities.Subscription(organization=module_org).search()

    for subscription in org_subscriptions:
        capsule_ak.add_subscriptions(data={'subscription_id': subscription.id})
        client7_ak.add_subscriptions(data={'subscription_id': subscription.id})
        client8_ak.add_subscriptions(data={'subscription_id': subscription.id})

    return {
        'capsule_ak': capsule_ak,
        'client7_ak': client7_ak,
        'client8_ak': client8_ak,
        'rhel7_contenthost': get_hosts_from_broker['rhel7'][0],
        'haproxy': get_hosts_from_broker['rhel7'][0],
        'rhel8_contenthost': get_hosts_from_broker['rhel8'],
        'capsule_1': get_hosts_from_broker['cap610'][0],
        'capsule_2': get_hosts_from_broker['cap610'][1],
    }

@pytest.fixture(scope='module')
def setup_haproxy(setup_lb_content, module_org, default_sat):
    haproxy = setup_lb_content['haproxy']
    haproxy.install_katello_ca(default_sat)
    haproxy.register_contenthost(module_org.label, setup_lb_content['client7_ak'].name)
    assert haproxy.subscribed
    result = haproxy.execute('yum install -y haproxy')
    assert result.status == 0
    haproxy.execute('curl --output /etc/haproxy/haproxy.cfg https://gist.githubusercontent.com/akhil-jha/8aaa5752c1f5621af8f5b367d50b1c75/raw/deac6615df57c833b855d310acc58933a4aaf3a0/haproxy.cfg')
    haproxy.host_services(action='restart', services=['haproxy.service'])
    haproxy.execute('mkdir /var/lib/haproxy/dev')
    haproxy.execute('curl --output /etc/rsyslog.d/99-haproxy.conf https://gist.githubusercontent.com/akhil-jha/8aaa5752c1f5621af8f5b367d50b1c75/raw/2f46a881380d2b69ce058dedf50c0f62a3f6e237/99-haproxy.conf')
    haproxy.host_services(action='restart', services=['rsyslog'])


@pytest.fixture(scope='module')
def setup_capsules(module_org, setup_lb_content, default_sat):

    capsules = get_hosts_from_broker['cap610']
    for capsule in capsules:
        capsule.install_katello_ca(default_sat)
        capsule.register_contenthost(module_org.label, setup_lb_content['capsule_ak'].name)
        assert capsule.subscribed

# @pytest.mark.stubbed
@pytest.mark.tier1
def test_katello_cert_download_manually(module_org, setup_lb_content, setup_capsules, default_sat):
    """Download katello-ca-consumer-latest.noarch.rpm through LB

    :id: 9398d59e-e141-11ea-83a6-4ceb42ab8dbc

    :Steps: run `yum localinstall -y \
            http://loadbalancer.example.com/pub/katello-ca-consumer-latest.noarch.rpm`

    :expectedresults: Katello cert should be installed from any one of the capsules.

    """
    pass


@pytest.mark.stubbed
@pytest.mark.tier1
def test_manually_register_client_using_ak():
    """Register the client using ak to the capsule

    :id: 7318c380-e149-11ea-9b17-4ceb42ab8dbc

    :Steps: run `subscription-manager register --org=Your_Organization \
            --activationkey=Your_Activation_Key \
            --serverurl=https://loadbalancer.example.com:8443/rhsm \
            --baseurl=https://loadbalancer.example.com/pulp/repos`

    :expectedresults: The client should be registered to one of the capsules

    """
    pass


@pytest.mark.stubbed
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