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
