"""CLI tests for ``katello-agent``.

:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: katello-agent

:team: Phoenix-subscriptions

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.utils import ohsnap

pytestmark = [
    pytest.mark.run_in_one_thread,
    pytest.mark.destructive,
    pytest.mark.no_containers,
    pytest.mark.tier5,
    pytest.mark.upgrade,
]


@pytest.mark.rhel_ver_match(r'[\d]+')
def test_positive_apply_errata(katello_agent_client):
    """Apply errata on a host

    :id: 8d0e5c93-f9fd-4ec0-9a61-aa93082a30c5

    :expectedresults: Errata is scheduled for installation

    :parametrized: yes

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
    assert client.run(f'rpm -q {constants.FAKE_2_CUSTOM_PACKAGE}').status == 0


@pytest.mark.rhel_ver_match(r'[\d]+')
def test_positive_install_and_remove_package(katello_agent_client):
    """Install and remove a package on a host remotely

    :id: b1009bba-0c7e-4b00-8ac4-256e5cfe4a78

    :expectedresults: Package successfully installed and removed

    :parametrized: yes

    """
    sat = katello_agent_client['sat']
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    sat.cli.Host.package_install(
        {'host-id': host_info['id'], 'packages': constants.FAKE_0_CUSTOM_PACKAGE_NAME}
    )
    assert client.run(f'rpm -q {constants.FAKE_0_CUSTOM_PACKAGE_NAME}').status == 0
    sat.cli.Host.package_remove(
        {'host-id': host_info['id'], 'packages': constants.FAKE_0_CUSTOM_PACKAGE_NAME}
    )
    assert client.run(f'rpm -q {constants.FAKE_0_CUSTOM_PACKAGE_NAME}').status != 0


@pytest.mark.rhel_ver_match(r'[\d]+')
def test_positive_upgrade_package(katello_agent_client):
    """Upgrade a package on a host remotely

    :id: ad751c63-7175-40ae-8bc4-800462cd9c29

    :expectedresults: Package successfully upgraded

    :parametrized: yes

    """
    sat = katello_agent_client['sat']
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.run(f'yum install -y {constants.FAKE_1_CUSTOM_PACKAGE}')
    sat.cli.Host.package_upgrade(
        {'host-id': host_info['id'], 'packages': constants.FAKE_1_CUSTOM_PACKAGE_NAME}
    )
    assert client.run(f'rpm -q {constants.FAKE_2_CUSTOM_PACKAGE}').status == 0


@pytest.mark.rhel_ver_match(r'[\d]+')
def test_positive_upgrade_packages_all(katello_agent_client):
    """Upgrade all packages on a host remotely

    :id: 003101c7-bb95-4e51-a598-57977b2858a9

    :expectedresults: Packages successfully upgraded (at least 1 with newer version available)

    :parametrized: yes

    """
    sat = katello_agent_client['sat']
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    client.run(f'yum install -y {constants.FAKE_1_CUSTOM_PACKAGE}')
    sat.cli.Host.package_upgrade_all({'host-id': host_info['id']})
    assert client.run(f'rpm -q {constants.FAKE_2_CUSTOM_PACKAGE}').status == 0


@pytest.mark.rhel_ver_match(r'[\d]+')
def test_positive_install_and_remove_package_group(katello_agent_client):
    """Install and remove a package group on a host remotely

    :id: ded20a89-cfd9-48d5-8829-739b1a4d4042

    :expectedresults: Package group successfully installed and removed

    :parametrized: yes

    """
    sat = katello_agent_client['sat']
    client = katello_agent_client['client']
    host_info = katello_agent_client['host_info']
    hammer_args = {'groups': constants.FAKE_0_CUSTOM_PACKAGE_GROUP_NAME, 'host-id': host_info['id']}
    sat.cli.Host.package_group_install(hammer_args)
    for package in constants.FAKE_0_CUSTOM_PACKAGE_GROUP:
        assert client.run(f'rpm -q {package}').status == 0
    sat.cli.Host.package_group_remove(hammer_args)
    for package in constants.FAKE_0_CUSTOM_PACKAGE_GROUP:
        assert client.run(f'rpm -q {package}').status != 0


def test_positive_upgrade_warning(sat_with_katello_agent):
    """Ensure a warning is dispayed when upgrading with katello-agent enabled.

    :id: 2bfc5e3e-e147-4e7a-a25c-85be22ef6921

    :expectedresults: Upgrade check fails and warning with proper message is displayed.

    """
    sat = sat_with_katello_agent
    ver = sat.version.split('.')
    target_ver = f'{ver[0]}.{int(ver[1]) + 1}'
    warning = (
        'The katello-agent feature is enabled on this system. As of Satellite 6.15, katello-agent '
        'is removed and will no longer function. Before proceeding with the upgrade, you should '
        'ensure that you have deployed and configured an alternative tool for remote package '
        'management and patching for content hosts, such as Remote Execution (REX) with pull-based '
        'transport. See the Managing Hosts guide in the Satellite documentation for more info. '
        'Disable katello-agent with the command `satellite-installer --foreman-proxy-content-enable'
        '-katello-agent false` before proceeding with the upgrade. Alternatively, you may skip '
        'this check and proceed by running satellite-maintain again with the `--whitelist` option, '
        'which will automatically uninstall katello-agent.'
    )

    maintain_repo = ohsnap.dogfood_repository(
        settings.ohsnap,
        product='satellite',
        repo='maintenance',
        release=target_ver,
        os_release=settings.server.version.rhel_version,
    )
    sat.create_custom_repos(next_maintain=maintain_repo.baseurl)

    sat.cli.Upgrade.list_versions()  # f-m self-update
    res = sat.cli.Upgrade.list_versions()
    assert res.status == 0, 'Upgrade list-versions command failed'
    assert target_ver in res.stdout, 'Target version or Scenario not found'

    res = sat.cli.Upgrade.check(
        options={
            'target-version': target_ver,
            'whitelist': 'repositories-setup,repositories-validate',
            'assumeyes': True,
        }
    )
    assert res.status, 'Upgrade check passed unexpectedly'
    assert warning in res.stdout, 'Katello-agent warning message missing or changed'
