import pytest
from box import Box

from robottelo.config import settings
from robottelo.utils.installer import InstallerCommand


@pytest.fixture(scope='module')
def sat_with_katello_agent(module_target_sat):
    """Assert that katello-agent feature is enabled on module_target_sat"""
    result = module_target_sat.install(
        InstallerCommand(help='| grep foreman-proxy-content-enable-katello-agent')
    )
    assert 'true' in result.stdout, 'katello-agent feature is not enabled on Satellite'
    yield module_target_sat


@pytest.fixture
def katello_agent_client_for_upgrade(sat_with_katello_agent, sat_upgrade_chost, module_org):
    """Register content host to Satellite and install katello-agent on the host."""
    client_repo = settings.repos['SATCLIENT_REPO'][f'RHEL{sat_upgrade_chost.os_version.major}']
    sat_with_katello_agent.register_host_custom_repo(
        module_org, sat_upgrade_chost, [client_repo, settings.repos.yum_1.url]
    )
    sat_upgrade_chost.install_katello_agent()
    host_info = sat_with_katello_agent.cli.Host.info({'name': sat_upgrade_chost.hostname})
    yield Box(
        {
            'client': sat_upgrade_chost,
            'host_info': host_info,
            'sat': sat_with_katello_agent,
        }
    )


@pytest.fixture
def katello_agent_client(sat_with_katello_agent, rhel_contenthost):
    """Register content host to Satellite and install katello-agent on the host."""
    org = sat_with_katello_agent.api.Organization().create()
    client_repo = settings.repos['SATCLIENT_REPO'][f'RHEL{rhel_contenthost.os_version.major}']
    sat_with_katello_agent.register_host_custom_repo(
        org, rhel_contenthost, [client_repo, settings.repos.yum_1.url]
    )
    rhel_contenthost.install_katello_agent()
    host_info = sat_with_katello_agent.cli.Host.info({'name': rhel_contenthost.hostname})
    yield Box({'client': rhel_contenthost, 'host_info': host_info, 'sat': sat_with_katello_agent})
