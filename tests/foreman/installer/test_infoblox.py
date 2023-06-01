"""Tests for Infoblox Plugin

:Requirement: Infoblox, Installer

:CaseLevel: System

:CaseAutomation: Automated

:CaseComponent: DHCPDNS

:Team: Rocket

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest


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
