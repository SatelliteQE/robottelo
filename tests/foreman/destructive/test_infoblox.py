"""Tests for Infoblox Plugin

:Requirement: Infoblox, Installer

:CaseLevel: System

:CaseComponent: DHCPDNS

:Assignee: dsynk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.hosts import get_sat_rhel_version
from robottelo.utils.installer import InstallerCommand

if get_sat_rhel_version().base_version == '7':
    dhcp_isc_package = 'tfm-rubygem-smart_proxy_dhcp_remote_isc'
    infoblox_package = 'tfm-rubygem-infoblox'
    infoblox_dhcp_package = 'tfm-rubygem-smart_proxy_dhcp_infoblox'
    infoblox_dns_package = 'tfm-rubygem-smart_proxy_dns_infoblox'
else:
    dhcp_isc_package = 'rubygem-smart_proxy_dhcp_remote_isc'
    infoblox_package = 'rubygem-infoblox'
    infoblox_dhcp_package = 'rubygem-smart_proxy_dhcp_infoblox'
    infoblox_dns_package = 'rubygem-smart_proxy_dns_infoblox'

pytestmark = pytest.mark.destructive
params = [
    (
        'enable-foreman-proxy-plugin-dhcp-remote-isc',
        {'foreman-proxy-dhcp': 'true'},
        f'rpm -q {dhcp_isc_package}',
    ),
    (
        'enable-foreman-proxy-plugin-dhcp-infoblox',
        {
            'foreman-proxy-plugin-dhcp-infoblox-username': 'fakeusername',
            'foreman-proxy-plugin-dhcp-infoblox-password': 'fakepassword',
        },
        f'echo {infoblox_package} {infoblox_dhcp_package} | xargs rpm -q',
    ),
    (
        'enable-foreman-proxy-plugin-dns-infoblox',
        {
            'foreman-proxy-plugin-dns-infoblox-username': 'fakeusername',
            'foreman-proxy-plugin-dns-infoblox-password': 'fakepassword',
            'foreman-proxy-plugin-dns-infoblox-dns-server': 'infoblox.example.com',
        },
        f'echo {infoblox_package} {infoblox_dns_package} | xargs rpm -q',
    ),
]


@pytest.mark.tier4
@pytest.mark.parametrize(
    'command_args,command_opts,rpm_command',
    params,
    ids=['isc_dhcp', 'infoblox_dhcp', 'infoblox_dns'],
)
def test_plugin_installation(target_sat, command_args, command_opts, rpm_command):
    """Check that external DNS and DHCP plugins install correctly

    :id: c75aa5f3-870a-4f4a-9d7a-0a871b47fd6f

    :Steps: Run installer with mininum options required to install plugins

    :expectedresults: Plugins install successfully

    :CaseAutomation: Automated

    :customerscenario: true

    :BZ: 1994490, 2000237
    """
    target_sat.download_repofile()
    target_sat.register_to_cdn()
    installer_obj = InstallerCommand(command_args, **command_opts)
    command_output = target_sat.execute(installer_obj.get_command())
    assert 'Success!' in command_output.stdout
    rpm_result = target_sat.execute(rpm_command)
    assert rpm_result.status == 0
