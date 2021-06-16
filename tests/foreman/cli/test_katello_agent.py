"""CLI tests for ``katello-agent``.

:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Katello-agent

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import time

import pytest
from broker import VMBroker

from robottelo.api.utils import wait_for_errata_applicability_task
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.factory import make_activation_key
from robottelo.cli.factory import make_host_collection
from robottelo.cli.factory import setup_org_for_a_custom_repo
from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.cli.host import Host
from robottelo.cli.hostcollection import HostCollection
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_GROUP
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_GROUP_NAME
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_ERRATA_ID
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE_NAME
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants.repos import FAKE_1_YUM_REPO
from robottelo.hosts import ContentHost


pytestmark = [pytest.mark.skip_if_not_set('clients', 'fake_manifest')]


@pytest.fixture(scope='module')
def katello_agent_repos(module_ak, module_cv, module_lce, module_org):
    """Create Org, Lifecycle Environment, Content View, Activation key"""
    setup_org_for_a_rh_repo(
        {
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': module_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': module_ak.id,
        }
    )
    # Create custom repository content
    setup_org_for_a_custom_repo(
        {
            'url': FAKE_1_YUM_REPO,
            'organization-id': module_org.id,
            'content-view-id': module_cv.id,
            'lifecycle-environment-id': module_lce.id,
            'activationkey-id': module_ak.id,
        }
    )
    return {
        'ak': module_ak,
        'cv': module_cv,
        'lce': module_lce,
        'org': module_org,
    }


@pytest.fixture
def katello_agent_client(katello_agent_repos, rhel7_contenthost):
    rhel7_contenthost.install_katello_ca()
    # Register content host and install katello-agent
    rhel7_contenthost.register_contenthost(
        katello_agent_repos['org'].label,
        katello_agent_repos['ak'].name,
    )
    assert rhel7_contenthost.subscribed
    host_info = Host.info({'name': rhel7_contenthost.hostname})
    rhel7_contenthost.enable_repo(REPOS['rhst7']['id'])
    rhel7_contenthost.install_katello_agent()
    yield {'client': rhel7_contenthost, 'host_info': host_info}


@pytest.mark.tier3
def test_positive_get_errata_info(katello_agent_client):
    """Get errata info

    :id: afb5ab34-1703-49dc-8ddc-5e032c1b86d7

    :expectedresults: Errata info was displayed

    :CaseLevel: System
    """
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    result = Host.errata_info({'host-id': host_info['id'], 'id': FAKE_1_ERRATA_ID})
    assert result[0]['errata-id'] == FAKE_1_ERRATA_ID
    assert FAKE_2_CUSTOM_PACKAGE in result[0]['packages']


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_apply_errata(katello_agent_client):
    """Apply errata to a host

    :id: 8d0e5c93-f9fd-4ec0-9a61-aa93082a30c5

    :expectedresults: Errata is scheduled for installation

    :CaseLevel: System
    """
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    Host.errata_apply({'errata-ids': FAKE_1_ERRATA_ID, 'host-id': host_info['id']})


@pytest.mark.tier3
def test_positive_apply_security_erratum(katello_agent_client):
    """Apply security erratum to a host

    :id: 4d1095c8-d354-42ac-af44-adf6dbb46deb

    :expectedresults: erratum is recognized by the
        `yum update --security` command on client

    :CaseLevel: System

    :BZ: 1420671, 1740790
    """
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.download_install_rpm(FAKE_1_YUM_REPO, FAKE_2_CUSTOM_PACKAGE)
    # Check the system is up to date
    result = client.run('yum update --security | grep "No packages needed for security"')
    assert result.status == 0
    before_downgrade = int(time.time())
    # Downgrade walrus package
    client.run(f'yum downgrade -y {FAKE_2_CUSTOM_PACKAGE_NAME}')
    # Wait for errata applicability cache is counted
    wait_for_errata_applicability_task(int(host_info['id']), before_downgrade)
    # Check that host has applicable errata
    host_errata = Host.errata_list({'host-id': host_info['id']})
    assert host_errata[0]['erratum-id'] == FAKE_1_ERRATA_ID
    assert host_errata[0]['installable'] == 'true'
    # Check the erratum becomes available
    result = client.run('yum update --assumeno --security | grep "No packages needed for security"')
    assert result.status == 1


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_install_package(katello_agent_client):
    """Install a package to a host remotely

    :id: b1009bba-0c7e-4b00-8ac4-256e5cfe4a78

    :expectedresults: Package was successfully installed

    :CaseLevel: System
    """
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    Host.package_install({'host-id': host_info['id'], 'packages': FAKE_0_CUSTOM_PACKAGE_NAME})
    result = client.run(f'rpm -q {FAKE_0_CUSTOM_PACKAGE_NAME}')
    assert result.status == 0


@pytest.mark.tier3
def test_positive_remove_package(katello_agent_client):
    """Remove a package from a host remotely

    :id: 573dec11-8f14-411f-9e41-84426b0f23b5

    :expectedresults: Package was successfully removed

    :CaseLevel: System
    """
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    Host.package_remove({'host-id': host_info['id'], 'packages': FAKE_1_CUSTOM_PACKAGE_NAME})
    result = client.run(f'rpm -q {FAKE_1_CUSTOM_PACKAGE_NAME}')
    assert result.status != 0


@pytest.mark.tier3
def test_positive_upgrade_package(katello_agent_client):
    """Upgrade a host package remotely

    :id: ad751c63-7175-40ae-8bc4-800462cd9c29

    :expectedresults: Package was successfully upgraded

    :CaseLevel: System
    """
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    Host.package_upgrade({'host-id': host_info['id'], 'packages': FAKE_1_CUSTOM_PACKAGE_NAME})
    result = client.run(f'rpm -q {FAKE_2_CUSTOM_PACKAGE}')
    assert result.status == 0


@pytest.mark.tier3
def test_positive_upgrade_packages_all(katello_agent_client):
    """Upgrade all the host packages remotely

    :id: 003101c7-bb95-4e51-a598-57977b2858a9

    :expectedresults: Packages (at least 1 with newer version available)
        were successfully upgraded

    :CaseLevel: System
    """
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    Host.package_upgrade_all({'host-id': host_info['id']})
    result = client.run(f'rpm -q {FAKE_2_CUSTOM_PACKAGE}')
    assert result.status == 0


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_install_and_remove_package_group(katello_agent_client):
    """Install and remove a package group to a host remotely

    :id: ded20a89-cfd9-48d5-8829-739b1a4d4042

    :expectedresults: Package group was successfully installed
        and removed

    :CaseLevel: System
    """
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    hammer_args = {'groups': FAKE_0_CUSTOM_PACKAGE_GROUP_NAME, 'host-id': host_info['id']}
    Host.package_group_install(hammer_args)
    for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
        result = client.run(f'rpm -q {package}')
        assert result.status == 0
    Host.package_group_remove(hammer_args)
    for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
        result = client.run(f'rpm -q {package}')
        assert result.status != 0


@pytest.mark.tier3
def test_negative_unregister_and_pull_content(katello_agent_client):
    """Attempt to retrieve content after host has been unregistered from Satellite

    :id: de0d0d91-b1e1-4f0e-8a41-c27df4d6b6fd

    :expectedresults: Host can no longer retrieve content from satellite

    :CaseLevel: System
    """
    client = katello_agent_client['client']
    result = client.run('subscription-manager unregister')
    assert result.status == 0
    result = client.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    assert result.status != 0


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_register_host_ak_with_host_collection(
    katello_agent_client, module_cv, module_lce, module_org, rhel7_contenthost
):
    """Attempt to register a host using activation key with host collection

    :id: 7daf4e40-3fa6-42af-b3f7-1ca1a5c9bfeb

    :BZ: 1385814

    :expectedresults: Host successfully registered and listed in host
        collection

    :CaseLevel: System
    """
    # client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    # create a new activation key
    activation_key = make_activation_key(
        {
            'lifecycle-environment-id': module_lce.id,
            'organization-id': module_org.id,
            'content-view-id': module_cv.id,
        }
    )
    hc = make_host_collection({'organization-id': module_org.id})
    ActivationKey.add_host_collection(
        {
            'id': activation_key['id'],
            'organization-id': module_org.id,
            'host-collection-id': hc['id'],
        }
    )
    # add the registered instance host to collection
    HostCollection.add_host(
        {'id': hc['id'], 'organization-id': module_org.id, 'host-ids': host_info['id']}
    )

    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}) as vm:
        vm.install_katello_ca()
        # register the client host with the current activation key
        vm.register_contenthost(module_org.name, activation_key=activation_key['name'])
        assert vm.subscribed
        # note: when registering the host, it should be automatically added to the host-collection
        client_host = Host.info({'name': vm.hostname})
        hosts = HostCollection.hosts({'id': hc['id'], 'organization-id': module_org.id})
        assert len(hosts) == 2
        expected_hosts_ids = {host_info['id'], client_host['id']}
        hosts_ids = {host['id'] for host in hosts}
        assert hosts_ids == expected_hosts_ids
