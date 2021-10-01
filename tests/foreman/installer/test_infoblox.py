"""Tests for Infoblox Plugin

:Requirement: Infoblox

:CaseLevel: System

:CaseComponent: DHCPDNS

:Assignee: dsynk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.helpers import InstallerCommand


@pytest.mark.tier4
def test_isc_dhcp_plugin_installation(default_sat):
    """Check that there are no packaging issues with ISC DHCP plugin
    :id: 6fc3827b-e431-4105-b2e9-f302044bdc09

    :Steps: Run installer with option
        --enable-foreman-proxy-plugin-dhcp-remote-isc

    :expectedresults: Plugin installs successfully

    :CaseAutomation: Automated

    :CaseLevel: System

    :CaseComponent: DHCPDNS

    :Assignee: dsynk

    :TestType: Functional

    :CaseImportance: High

    :Upstream: No

    :Requirement: Installer

    :customerscenario: true

    :BZ: 1994490
    """
    installer_obj = InstallerCommand('enable-foreman-proxy-plugin-dhcp-remote-isc')
    command_output = default_sat.execute(installer_obj.get_command())
    assert 'Success!' in command_output.stdout
    rpm_result = default_sat.execute('rpm -q tfm-rubygem-smart_proxy_dhcp_remote_isc')
    assert rpm_result.status == 0


@pytest.mark.tier4
def test_infoblox_dhcp_plugin_installation(default_sat):
    """Check that there are no packaging issues with Infoblox DHCP plugin
    :id: 83f4596c-9641-4df5-ba3d-fb1e5b99ff9b

    :Steps: Run installer with options
        --enable-foreman-proxy-plugin-dhcp-infoblox
        --foreman-proxy-plugin-dhcp-infoblox-username fakeusername
        --foreman-proxy-plugin-dhcp-infoblox-password fakepassword

    :expectedresults: Plugin installs successfully

    :CaseAutomation: Automated

    :CaseLevel: System

    :CaseComponent: DHCPDNS

    :Assignee: dsynk

    :TestType: Functional

    :CaseImportance: High

    :Upstream: No

    :Requirement: Installer

    :BZ: 2000237
    """
    command_args = 'enable-foreman-proxy-plugin-dhcp-infoblox'
    command_opts = {
        'foreman-proxy-plugin-dhcp-infoblox-username': 'fakeusername',
        'foreman-proxy-plugin-dhcp-infoblox-password': 'fakepassword',
    }
    installer_obj = InstallerCommand(command_args, **command_opts)
    command_output = default_sat.execute(installer_obj.get_command())
    assert 'Success!' in command_output.stdout
    rpm_result = default_sat.execute(
        'echo tfm-rubygem-infoblox tfm-rubygem-smart_proxy_dhcp_infoblox | xargs rpm -q'
    )
    assert rpm_result.status == 0


@pytest.mark.tier4
def test_infoblox_dns_plugin_installation(default_sat):
    """Check that there are no packaging issues with Infoblox DNS plugin
    :id: 2ffa6b48-8033-4541-892e-c139f67080a4

    :Steps: Run installer with options
        --enable-foreman-proxy-plugin-dns-infoblox
        --foreman-proxy-plugin-dns-infoblox-username fakeusername
        --foreman-proxy-plugin-dns-infoblox-password fakepassword

    :expectedresults: Plugin installs successfully

    :CaseAutomation: Automated

    :CaseLevel: System

    :CaseComponent: DHCPDNS

    :Assignee: dsynk

    :TestType: Functional

    :CaseImportance: High

    :Upstream: No

    :Requirement: Installer

    :BZ: 2000237
    """
    command_args = 'enable-foreman-proxy-plugin-dns-infoblox'
    command_opts = {
        'foreman-proxy-plugin-dns-infoblox-username': 'fakeusername',
        'foreman-proxy-plugin-dns-infoblox-password': 'fakepassword',
        'foreman-proxy-plugin-dns-infoblox-dns-server': 'infoblox.example.com',
    }
    installer_obj = InstallerCommand(command_args, **command_opts)
    command_output = default_sat.execute(installer_obj.get_command())
    assert 'Success!' in command_output.stdout
    rpm_result = default_sat.execute(
        'echo tfm-rubygem-infoblox tfm-rubygem-smart_proxy_dns_infoblox | xargs rpm -q'
    )
    assert rpm_result.status == 0


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.upgrade
def test_set_dns_provider():
    """Check Infoblox DNS plugin is set as provider

    :id: 23f76fa8-79bb-11e6-a3d4-68f72889dc7f

    :Steps: Set infoblox as dns provider with options
        --foreman-proxy-dns=true
        --foreman-proxy-plugin-provider=infoblox
        --enable-foreman-proxy-plugin-dns-infoblox
        --foreman-proxy-plugin-dns-infoblox-dns-server=<ip>
        --foreman-proxy-plugin-dns-infoblox-username=<username>
        --foreman-proxy-plugin-dns-infoblox-password=<password>

    :expectedresults: Check inflobox is set as DNS provider

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.upgrade
def test_set_dhcp_provider():
    """Check Infoblox DHCP plugin is set as provider

    :id: 40783976-7e68-11e6-b728-68f72889dc7f

    :Steps: Set infoblox as dhcp provider with options
        --foreman-proxy-dhcp=true
        --foreman-proxy-plugin-dhcp-provider=infoblox
        --enable-foreman-proxy-plugin-dhcp-infoblox
        --foreman-proxy-plugin-dhcp-infoblox-dhcp-server=<ip>
        --foreman-proxy-plugin-dhcp-infoblox-username=<username>
        --foreman-proxy-plugin-dhcp-infoblox-password=<password>

    :expectedresults: Check inflobox is set as DHCP provider

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_update_dns_appliance_credentials():
    """Check infoblox appliance credentials are updated

    :id: 2e84a8b4-79b6-11e6-8bf8-68f72889dc7f

    :Steps: Pass appliance credentials via installer options
        --foreman-proxy-plugin-dns-infoblox-username=<username>
        --foreman-proxy-plugin-dns-infoblox-password=<password>

    :expectedresults: config/dns_infoblox.yml should be updated with
        infoblox_hostname, username & password

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.upgrade
def test_enable_dns_plugin():
    """Check Infoblox DNS plugin can be enabled on server

    :id: f8be8c34-79b2-11e6-8992-68f72889dc7f

    :Steps: Enable Infoblox plugin via installer options
        --enable-foreman-proxy-plugin-dns-infoblox

    :CaseLevel: System

    :expectedresults: Check DNS plugin is enabled on host

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_disable_dns_plugin():
    """Check Infoblox DNS plugin can be disabled on host

    :id: c5f563c6-79b3-11e6-8cb6-68f72889dc7f

    :Steps: Disable Infoblox plugin via installer

    :expectedresults: Check DNS plugin is disabled on host

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.upgrade
def test_enable_dhcp_plugin():
    """Check Infoblox DHCP plugin can be enabled on host

    :id: 75650c06-79b6-11e6-ad91-68f72889dc7f

    :Steps: Enable Infoblox plugin via installer option
        --enable-foreman-proxy-plugin-dhcp-infoblox

    :expectedresults: Check DHCP plugin is enabled on host

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_disable_dhcp_plugin():
    """Check Infoblox DHCP plugin can be disabled on host

    :id: ea347f34-79b7-11e6-bb03-68f72889dc7f

    :Steps: Disable Infoblox plugin via installer

    :expectedresults: Check DHCP plugin is disabled on host

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.upgrade
def test_dhcp_ip_range():
    """Check host get IP from Infoblox IP range while provisioning a host

    :id: ba957e82-79bb-11e6-94c5-68f72889dc7f

    :Steps: Provision a host with infoblox as dhcp provider

    :expectedresults: Check host ip is on infoblox range configured by
        option --foreman-proxy-plugin-dhcp-infoblox-use-ranges=true

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.upgrade
def test_dns_records():
    """Check DNS records are updated via infoblox DNS plugin

    :id: 007ad06e-79bc-11e6-885f-68f72889dc7f

    :Steps:

        1. Provision a host with infoblox as dns provider
        2. Update a DNS record on infoblox

    :expectedresults: Check host dns is updated accordingly to infoblox

    :CaseLevel: System

    :CaseAutomation: NotAutomated
    """
