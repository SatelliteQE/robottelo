"""Tests for Infoblox Plugin

:Requirement: Infoblox, Installer

:CaseLevel: System

:CaseComponent: DHCPDNS

:Assignee: dsynk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import epdb
import pytest

from robottelo.utils.installer import InstallerCommand

pytestmark = pytest.mark.destructive
params = [
    (
        'enable-foreman-proxy-plugin-dhcp-remote-isc',
        {'foreman-proxy-dhcp': 'true'},
        'rpm -q tfm-rubygem-smart_proxy_dhcp_remote_isc',
    ),
    (
        'enable-foreman-proxy-plugin-dhcp-infoblox',
        {
            'foreman-proxy-plugin-dhcp-infoblox-username': 'fakeusername',
            'foreman-proxy-plugin-dhcp-infoblox-password': 'fakepassword',
        },
        'echo tfm-rubygem-infoblox tfm-rubygem-smart_proxy_dhcp_infoblox | xargs rpm -q',
    ),
    (
        'enable-foreman-proxy-plugin-dns-infoblox',
        {
            'foreman-proxy-plugin-dns-infoblox-username': 'fakeusername',
            'foreman-proxy-plugin-dns-infoblox-password': 'fakepassword',
            'foreman-proxy-plugin-dns-infoblox-dns-server': 'infoblox.example.com',
        },
        'echo tfm-rubygem-infoblox tfm-rubygem-smart_proxy_dns_infoblox | xargs rpm -q',
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
    installer_obj = InstallerCommand(command_args, **command_opts)
    command_output = target_sat.execute(installer_obj.get_command())
    epdb.serve(port=9000)
    assert 'Success!' in command_output.stdout
    rpm_result = target_sat.execute(rpm_command)
    assert rpm_result.status == 0
