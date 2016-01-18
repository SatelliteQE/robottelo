# -*- encoding: utf-8 -*-
"""Test class for CLI Foreman Discovery"""
from robottelo.decorators import stubbed
from robottelo.test import CLITestCase


class DiscoveryTestCase(CLITestCase):
    """Implements Foreman discovery CLI tests."""

    @stubbed()
    def test_positive_discovered_host_facts(self):
        """Check all facts of discovered hosts are correctly displayed

        @Feature: Foreman Discovery

        @Setup:

        1. Provisioning should be configured

        2. Host is already discovered

        @Steps: Validate IP, memory, mac etc of discovered host
        #hammer discovery facts

        @Assert: All facts should be displayed correctly

        @Status: Manual

        """

    @stubbed()
    def test_positive_provision_discovered_host(self):
        """Provision the discovered host from hammer cli

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should be provisioned successfully and entry from
        discovered host should be auto removed

        @Status: Manual

        """

    @stubbed()
    def test_positive_delete_discovered_host(self):
        """Delete the selected discovered host

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        @Status: Manual

        """

    @stubbed()
    def test_positive_refresh_discovered_host_facts(self):
        """Refresh the facts of discovered hosts

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Facts should be refreshed successfully
        Add a NIC on discovered host and refresh the facts from Server

        @Status: Manual

        """

    @stubbed()
    def test_positive_reboot_discovered_host(self):
        """Reboot discovered hosts

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host is rebooted

        @Status: Manual

        """

    @stubbed()
    def test_positive_discover_and_auto_provision(self):
        """Discover a host and auto-provision it

        @Feature: Foreman Discovery

        @Assert: Host should be successfully rebooted and provisioned

        @Status: Manual

        """

    @stubbed()
    def test_positive_assign_discovery_manager_role(self):
        """Assign 'Discovery_Manager' role to a normal user

        @Feature: Foreman Discovery

        @Assert: User should be able to view, provision, edit and destroy one
        or more discovered host as well view, create_new, edit, execute and
        delete discovery rules.

        @Status: Manual

        """

    @stubbed()
    def test_positive_assign_discovery_role(self):
        """Assign 'Discovery" role to a normal user

        @Feature: Foreman Discovery

        @Assert: User should be able to list, provision, and destroy one
        or more discovered host

        @Status: Manual

        """
