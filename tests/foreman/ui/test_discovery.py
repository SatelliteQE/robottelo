# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery"""
from robottelo.test import UITestCase


class Discovery(UITestCase):
    """Implements Foreman discovery tests in UI."""

    def test_host_discovery_1(self):
        """@Test: Discover a host in legacy mode by setting
        "proxy.type=foreman" in PXE default

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured

        @Steps: PXE boot a host/VM

        @Assert: Host should be successfully discovered

        @Status: Manual

        """

    def test_host_discovery_2(self):
        """@Test: Discover a host via proxy by setting "proxy.type=proxy" in
        PXE default

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured

        @Steps: PXE boot a host/VM

        @Assert: Host should be successfully discovered

        @Status: Manual

        """

    def test_host_discovery_facts(self):
        """@Test: Check all facts of discovered hosts are correctly displayed

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured

        @Steps: Validate IP, memory, mac etc of discovered host

        @Assert: All facts should be displayed correctly

        @Status: Manual

        """

    def test_provision_discovered_host_1(self):
        """@Test: Provision the selected discovered host

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should be provisioned successfully and entry from
        discovered host should be auto removed

        @Status: Manual

        """

    def test_provision_discovered_host_2(self):
        """@Test: Provision the selected discovered host from facts page

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should be provisioned successfully and entry from
        discovered host should be auto removed

        @Status: Manual

        """

    def test_delete_discovered_host_1(self):
        """@Test: Delete the selected discovered host

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        @Status: Manual

        """

    def test_delete_discovered_host_2(self):
        """@Test: Delete the selected discovered host from facts page

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        @Status: Manual

        """

    def test_delete_multiple_discovered_hosts(self):
        """@Test: Delete multiple discovered hosts from 'Select Action'
        drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        @Status: Manual

        """

    def test_refresh_discovered_host_facts(self):
        """@Test: Delete the selected discovered host from facts page

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Facts should be refreshed successfully
        ToDo: Need to check what we change on host that its updated with
        refresh facts

        @Status: Manual

        """

    def test_change_default_org(self):
        """@Test: Change the default org of more than one discovered hosts
        from 'Select Action' drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Default org should be successfully changed for multiple hosts

        @Status: Manual

        """

    def test_change_default_location(self):
        """@Test: Change the default location of more than one discovered hosts
        from 'Select Action' drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Default Location should be successfully changed for multiple
        hosts

        @Status: Manual

        """

    def test_create_discovery_rule_1(self):
        """@Test: Create a new discovery rule

        Set query as (e.g IP=IP_of_discivered_host)

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should reboot and provision

        @Status: Manual

        """

    def test_create_discovery_rule_2(self):
        """@Test: Create a new discovery rule that applies to multi hosts
        Set query as (e.g  subnet=subnet_of discovered_hosts) OR mem > 500

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: All Hosts of same subnet should reboot and provision

        @Status: Manual

        """

    def test_create_discovery_rule_3(self):
        """@Test: Create multiple discovery rules with different priority

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host with lower count have higher priority
        and that rule should be executed first

        @Status: Manual

        """

    def test_create_discovery_rule_4(self):
        """@Test: Create a discovery rule and execute it when
        "auto_provisioning" flag set to 'false'

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: User should get proper validation error message

        @Status: Manual

        """

    def test_create_discovery_rule_5(self):
        """@Test: Create a discovery rule with invalid query
        e.g. BIOS = xyz

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Rule should automatically be skipped or handled with some
        warning message.

        @Status: Manual

        """

    def test_delete_discovery_rule(self):
        """@Test: Delete a discovery rule

        @Feature: Foreman Discovery

        @Assert: Rule should be deleted successfully

        @Status: Manual

        """

    def test_update_discovery_rule_1(self):
        """@Test: Update an existing rule and execute it

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: User should be able to update the rule and it should be
        executed on discovered host

        @Status: Manual

        """

    def test_update_discovery_rule_2(self):
        """@Test: Update the discovered host name and provision it

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: The hostname should be updated and host should be provisioned

        @Status: Manual

        """

    def test_update_discovery_rule_3(self):
        """@Test: Update the discovered host name with blank or long name

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: User should get a validation error

        @Status: Manual

        """
