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
import pytest

from robottelo import constants
from robottelo.cli.factory import setup_org_for_a_custom_repo
from robottelo.cli.factory import setup_org_for_a_rh_repo
from robottelo.config import settings
from robottelo.helpers import InstallerCommand


pytestmark = [
    pytest.mark.run_in_one_thread,
    pytest.mark.skip_if_not_set('clients', 'fake_manifest'),
    pytest.mark.destructive,
]


@pytest.fixture(scope='module')
def sat_with_katello_agent(module_destructive_sat):
    """Enable katello-agent on destructive_sat"""
    module_destructive_sat.register_to_dogfood()
    # Enable katello-agent from satellite-installer
    result = module_destructive_sat.install(
        InstallerCommand('foreman-proxy-content-enable-katello-agent true')
    )
    assert result.status == 0
    # Verify katello-agent is enabled
    result = module_destructive_sat.install(
        InstallerCommand(help='| grep foreman-proxy-content-enable-katello-agent')
    )
    assert 'true' in result.stdout
    yield module_destructive_sat


@pytest.fixture(scope='module')
def katello_agent_repos(sat_with_katello_agent):
    """Create Org, Lifecycle Environment, Content View, Activation key"""
    sat = sat_with_katello_agent
    org = sat.api.Organization().create()
    lce = sat.api.LifecycleEnvironment(organization=org).create()
    cv = sat.api.ContentView(organization=org).create()
    ak = sat.api.ActivationKey(environment=lce, organization=org).create()
    setup_org_for_a_rh_repo(
        {
            'product': constants.PRDS['rhel'],
            'repository-set': constants.REPOSET['rhst7'],
            'repository': constants.REPOS['rhst7']['name'],
            'organization-id': org.id,
            'content-view-id': cv.id,
            'lifecycle-environment-id': lce.id,
            'activationkey-id': ak.id,
        }
    )
    # Create custom repository content
    setup_org_for_a_custom_repo(
        {
            'url': settings.repos.yum_1.url,
            'organization-id': org.id,
            'content-view-id': cv.id,
            'lifecycle-environment-id': lce.id,
            'activationkey-id': ak.id,
        }
    )
    return {
        'ak': ak,
        'cv': cv,
        'lce': lce,
        'org': org,
    }, sat_with_katello_agent


@pytest.fixture
def katello_agent_client(katello_agent_repos, rhel7_contenthost):
    katello_agent_repos, sat_with_katello_agent = katello_agent_repos
    rhel7_contenthost.install_katello_ca(sat_with_katello_agent)
    # Register content host and install katello-agent
    rhel7_contenthost.register_contenthost(
        katello_agent_repos['org'].label,
        katello_agent_repos['ak'].name,
    )
    assert rhel7_contenthost.subscribed
    host_info = sat_with_katello_agent.cli.Host.info({'name': rhel7_contenthost.hostname})
    rhel7_contenthost.enable_repo(constants.REPOS['rhst7']['id'])
    rhel7_contenthost.install_katello_agent()
    yield {'client': rhel7_contenthost, 'host_info': host_info, 'sat': sat_with_katello_agent}


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_apply_errata(katello_agent_client):
    """Apply errata to a host

    :id: 8d0e5c93-f9fd-4ec0-9a61-aa93082a30c5

    :expectedresults: Errata is scheduled for installation

    :CaseLevel: System
    """
    sat = katello_agent_client['sat']
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.run(f'yum install -y {constants.FAKE_1_CUSTOM_PACKAGE}')
    result = sat.cli.Host.errata_info(
        {'host-id': host_info['id'], 'id': settings.repos.yum_0.errata[1]}
    )
    assert result[0]['errata-id'] == settings.repos.yum_0.errata[1]
    assert constants.FAKE_2_CUSTOM_PACKAGE in result[0]['packages']

    sat.cli.Host.errata_apply(
        {'errata-ids': settings.repos.yum_0.errata[1], 'host-id': host_info['id']}
    )
    result = client.run(f'rpm -q {constants.FAKE_2_CUSTOM_PACKAGE}')
    assert result.status == 0


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_install_package(katello_agent_client):
    """Install a package to a host remotely

    :id: b1009bba-0c7e-4b00-8ac4-256e5cfe4a78

    :expectedresults: Package was successfully installed

    :CaseLevel: System
    """
    sat = katello_agent_client['sat']
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    sat.cli.Host.package_install(
        {'host-id': host_info['id'], 'packages': constants.FAKE_0_CUSTOM_PACKAGE_NAME}
    )
    result = client.run(f'rpm -q {constants.FAKE_0_CUSTOM_PACKAGE_NAME}')
    assert result.status == 0


@pytest.mark.tier3
def test_positive_remove_package(katello_agent_client):
    """Remove a package from a host remotely

    :id: 573dec11-8f14-411f-9e41-84426b0f23b5

    :expectedresults: Package was successfully removed

    :CaseLevel: System
    """
    sat = katello_agent_client['sat']
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.run(f'yum install -y {constants.FAKE_1_CUSTOM_PACKAGE}')
    sat.cli.Host.package_remove(
        {'host-id': host_info['id'], 'packages': constants.FAKE_1_CUSTOM_PACKAGE_NAME}
    )
    result = client.run(f'rpm -q {constants.FAKE_1_CUSTOM_PACKAGE_NAME}')
    assert result.status != 0


@pytest.mark.tier3
def test_positive_upgrade_package(katello_agent_client):
    """Upgrade a host package remotely

    :id: ad751c63-7175-40ae-8bc4-800462cd9c29

    :expectedresults: Package was successfully upgraded

    :CaseLevel: System
    """
    sat = katello_agent_client['sat']
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.run(f'yum install -y {constants.FAKE_1_CUSTOM_PACKAGE}')
    sat.cli.Host.package_upgrade(
        {'host-id': host_info['id'], 'packages': constants.FAKE_1_CUSTOM_PACKAGE_NAME}
    )
    result = client.run(f'rpm -q {constants.FAKE_2_CUSTOM_PACKAGE}')
    assert result.status == 0


@pytest.mark.tier3
def test_positive_upgrade_packages_all(katello_agent_client):
    """Upgrade all the host packages remotely

    :id: 003101c7-bb95-4e51-a598-57977b2858a9

    :expectedresults: Packages (at least 1 with newer version available)
        were successfully upgraded

    :CaseLevel: System
    """
    sat = katello_agent_client['sat']
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.run(f'yum install -y {constants.FAKE_1_CUSTOM_PACKAGE}')
    sat.cli.Host.package_upgrade_all({'host-id': host_info['id']})
    result = client.run(f'rpm -q {constants.FAKE_2_CUSTOM_PACKAGE}')
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
    sat = katello_agent_client['sat']
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    hammer_args = {'groups': constants.FAKE_0_CUSTOM_PACKAGE_GROUP_NAME, 'host-id': host_info['id']}
    sat.cli.Host.package_group_install(hammer_args)
    for package in constants.FAKE_0_CUSTOM_PACKAGE_GROUP:
        result = client.run(f'rpm -q {package}')
        assert result.status == 0
    sat.cli.Host.package_group_remove(hammer_args)
    for package in constants.FAKE_0_CUSTOM_PACKAGE_GROUP:
        result = client.run(f'rpm -q {package}')
        assert result.status != 0
