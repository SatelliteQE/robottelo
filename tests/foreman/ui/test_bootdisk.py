"""Test classes for Boot disk tests

:Requirement: Bootdisk

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import stubbed, tier3, upgrade
from robottelo.test import UITestCase


class BootdiskTestCase(UITestCase):
    """Tests for Bootdisk"""

    @stubbed()
    @tier3
    def test_positive_provision_using_static_full_host_bootdisk(self):
        """Provision a host in a dhcpless environment through static IP Full
        Host bootdisk.

        :id: caee2156-c553-47cc-8be4-76dd715a36b9

        :Setup:

            1. Define a Static subnet without dhcp proxy
            2. Create new host with required network configuration.

        :Steps:

            1. Navigate to All Hosts -> Select hosts
            2. On host details page -> Go to 'BootDisk' dropdown
            3. Download the Full host FQDN image
            4. Boot the host from ISO, it configures the network
                and downloads kickstart from HTTP.

        :expectedresults: Host should successfully provisioned through
            Static IP full host bootdisk.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_provision_using_full_host_bootdisk_with_dhcp(self):
        """Provision a host through Full Host bootdisk where dhcp service is
        enabled.

        :id: ec78913b-7ffa-49a7-8085-d136eed5a33e

        :Setup:

            1. Define a subnet w/ dhcp proxy
            2. Create new host with required network configuration.

        :Steps:

            1. Navigate to All Hosts -> Select hosts
            2. On host details page -> Go to 'BootDisk' dropdown
            3. Download the Full host FQDN image
            4. Boot the host from ISO, it configures the network through dhcp
                and downloads kickstart from http.

        :expectedresults: Host should successfully provisioned through full
            host bootdisk.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """
