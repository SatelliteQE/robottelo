# -*- encoding: utf-8 -*-
"""Test class for CLI Foreman Discovery"""
from robottelo.decorators import run_only_on, stubbed, tier3
from robottelo.test import CLITestCase


class DiscoveryTestCase(CLITestCase):
    """Implements Foreman discovery CLI tests."""

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_custom_facts_pxeless_discovery(self):
        """Check if defined custom facts of pxeless host are correctly
        displayed under host's facts

        @Feature: Foreman Discovery - PXELess

        @Setup:

        1. Provisioning should be configured

        2. Host is already discovered

        @Steps: Validate specified custom facts

        @Assert: All defined custom facts should be displayed correctly

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_custom_facts_pxe_discovery(self):
        """Check if defined custom facts of pxe-based discovered host are
        correctly displayed under host's facts

        @Feature: Foreman Discovery - PXEBased

        @Setup:

        1. Provisioning should be configured

        2. Host is already discovered

        @Steps: Validate specified custom facts

        @Assert: All defined custom facts should be displayed correctly

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_pxeless_host(self):
        """Provision the pxe-less discovered host from cli

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should be provisioned successfully and entry from
        discovered host list should be auto removed

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_pxe_host(self):
        """Provision the pxe based discovered host from cli

        @Feature: Foreman Discovery - PXEBased

        @Setup: Host should already be discovered

        @Assert: Host should be provisioned successfully and entry from
        discovered host list should be automatically removed.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_delete_pxeless_host(self):
        """Delete the selected pxe-less discovered host

        @Feature: Foreman Discovery - PXELess

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_delete_pxe_host(self):
        """Delete the selected pxe-based discovered host

        @Feature: Foreman Discovery - PXELess

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_refresh_facts_pxe_host(self):
        """Refresh the facts of pxe based discovered hosts by adding a new NIC

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Facts should be refreshed successfully with a new NIC

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_refresh_facts_of_pxeless_host(self):
        """Refresh the facts of pxeless discovered hosts by adding a new NIC

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Facts should be refreshed successfully with a new NIC

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_reboot_pxe_host(self):
        """Reboot pxe based discovered hosts

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host is rebooted

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_reboot_pxeless_host(self):
        """Reboot pxe-less discovered hosts

        @Feature: Foreman Discovery

        @Setup: PXELess host should already be discovered

        @Assert: Host is rebooted

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_auto_provision_pxe_host(self):
        """Discover a pxe based host and auto-provision it with
        discovery rule and by enabling auto-provision flag

        @Feature: Foreman Discovery

        @Assert: Host should be successfully rebooted and provisioned

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_auto_provision_pxeless_host(self):
        """Discover a pxe-less host and auto-provision it with
        discovery rule and by enabling auto-provision flag

        @Feature: Foreman Discovery

        @Assert: Host should be successfully rebooted and provisioned

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_discovered_host(self):
        """List pxe-based and pxe-less discovered hosts

        @Feature: Foreman Discovery

        @Assert: Host should be discovered and listed with names.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_assign_discovery_manager_role(self):
        """Assign 'Discovery_Manager' role to a normal user

        @Feature: Foreman Discovery

        @Assert: User should be able to view, provision, edit and destroy one
        or more discovered host as well view, create_new, edit, execute and
        delete discovery rules.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_assign_discovery_role(self):
        """Assign 'Discovery" role to a normal user

        @Feature: Foreman Discovery

        @Assert: User should be able to list, provision, and destroy one
        or more discovered host

        @Status: Manual
        """
