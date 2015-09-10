# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery"""
from robottelo.decorators import stubbed
from robottelo.test import UITestCase


class Discovery(UITestCase):
    """Implements Foreman discovery tests in UI."""

    @stubbed()
    def test_host_discovery_1(self):
        """@Test: Discover a host in legacy mode by setting
        "proxy.type=foreman" in PXE default

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured

        @Steps: PXE boot a host/VM

        @Assert: Host should be successfully discovered

        @Status: Manual

        """

    @stubbed()
    def test_host_discovery_2(self):
        """@Test: Discover a host via proxy by setting "proxy.type=proxy" in
        PXE default

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured

        @Steps: PXE boot a host/VM

        @Assert: Host should be successfully discovered

        @Status: Manual

        """

    @stubbed()
    def test_host_discovery_facts(self):
        """@Test: Check all facts of discovered hosts are correctly displayed

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured

        @Steps: Validate IP, memory, mac etc of discovered host

        @Assert: All facts should be displayed correctly

        @Status: Manual

        """

    @stubbed()
    def test_provision_discovered_host_1(self):
        """@Test: Provision the selected discovered host by selecting
        'provision' button

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should be provisioned successfully and entry from
        discovered host should be auto removed

        @Status: Manual

        """

    @stubbed()
    def test_provision_discovered_host_2(self):
        """@Test: Provision the selected discovered host from facts page by
        clicking 'provision'

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should be provisioned successfully and entry from
        discovered host should be auto removed

        @Status: Manual

        """

    @stubbed()
    def test_delete_discovered_host_1(self):
        """@Test: Delete the selected discovered host

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        @Status: Manual

        """

    @stubbed()
    def test_delete_discovered_host_2(self):
        """@Test: Delete the selected discovered host from facts page

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        @Status: Manual

        """

    @stubbed()
    def test_delete_multiple_discovered_hosts(self):
        """@Test: Delete multiple discovered hosts from 'Select Action'
        drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        @Status: Manual

        """

    @stubbed()
    def test_refresh_discovered_host_facts(self):
        """@Test: Refresh the facts of discovered hosts

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Facts should be refreshed successfully
        ToDo: Need to check what we change on host that its updated with
        refresh facts

        @Status: Manual

        """

    @stubbed()
    def test_change_default_org(self):
        """@Test: Change the default org of more than one discovered hosts
        from 'Select Action' drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Default org should be successfully changed for multiple hosts

        @Status: Manual

        """

    @stubbed()
    def test_change_default_location(self):
        """@Test: Change the default location of more than one discovered hosts
        from 'Select Action' drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Default Location should be successfully changed for multiple
        hosts

        @Status: Manual

        """

    @stubbed()
    def test_create_discovery_rule_1(self):
        """@Test: Create a new discovery rule

        Set query as (e.g IP=IP_of_discovered_host)

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should reboot and provision

        @Status: Manual

        """

    @stubbed()
    def test_create_discovery_rule_2(self):
        """@Test: Create a new discovery rule with (host_limit = 0)
        that applies to multi hosts.
        Set query as cpu_count = 1 OR mem > 500

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: All Hosts of same subnet should reboot and provision

        @Status: Manual

        """

    @stubbed()
    def test_create_discovery_rule_3(self):
        """@Test: Create multiple discovery rules with different priority

        @Feature: Foreman Discovery

        @Setup: Multiple hosts should already be discovered

        @Assert: Host with lower count have higher priority
        and that rule should be executed first

        @Status: Manual

        """

    @stubbed()
    def test_create_discovery_rule_4(self):
        """@Test: Create a discovery rule and execute it when
        "auto_provisioning" flag set to 'false'

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should not be rebooted automatically

        @Status: Manual

        """

    @stubbed()
    def test_create_discovery_rule_5(self):
        """@Test: Create a discovery rule with invalid query
        e.g. BIOS = xyz

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Rule should automatically be skipped on clicking
        'Auto provision'. UI Should raise 'No matching rule found'

        @Status: Manual

        """

    @stubbed()
    def test_create_discovery_rule_6(self):
        """@Test: Create a discovery rule (CPU_COUNT = 2) with host limit 1 and
        provision more than one host with same rule

        @Feature: Foreman Discovery

        @Setup: Host with two CPUs should already be discovered

        @Assert: Rule should only be applied to one discovered host and for
        other rule should already be skipped.

        @Status: Manual

        """

    @stubbed()
    def test_rule_with_invalid_host_limit(self):
        """@Test: Create a discovery rule with invalid(-ve/text value) host
        limit

        @Feature: Foreman Discovery

        @Setup: Host with two CPUs should already be discovered

        @Assert: Validation error should be raised

        @Status: Manual

        """

    @stubbed()
    def test_rule_with_invalid_priority(self):
        """@Test: Create a discovery rule with invalid(text value) priority

        @Feature: Foreman Discovery

        @Setup: Host with two CPUs should already be discovered

        @Assert: Validation error should be raised

        @Status: Manual

        """

    @stubbed()
    def test_create_rule_with_long_name(self):
        """@Test: Create a discovery rule with more than 255 char

        @Feature: Foreman Discovery

        @Setup: Host with two CPUs should already be discovered

        @Assert: Validation error should be raised

        @Status: Manual

        """

    @stubbed()
    def test_delete_discovery_rule(self):
        """@Test: Delete a discovery rule

        @Feature: Foreman Discovery

        @Assert: Rule should be deleted successfully

        @Status: Manual

        """

    @stubbed()
    def test_update_discovery_rule_1(self):
        """@Test: Update an existing rule and execute it

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: User should be able to update the rule and it should be
        executed on discovered host

        @Status: Manual

        """

    @stubbed()
    def test_update_discovery_rule_2(self):
        """@Test: Update the discovered host name and provision it

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: The hostname should be updated and host should be provisioned

        @Status: Manual

        """

    @stubbed()
    def test_update_discovery_prefix(self):
        """@Test: Update the discovery_prefix parameter other than mac

        @Feature: Foreman Discovery

        @Steps:

        1. Goto settings &#8592; Discovered tab -> discovery_prefix

        2. Edit discovery_prefix using any text that must start with a letter

        @Setup: Host should already be discovered

        @Assert: discovery_prefix is updated and provisioned host has same
        prefix in its hostname

        @Status: Manual

        """

    @stubbed()
    def test_auto_provision_all(self):
        """@Test: Discover a bunch of hosts and auto-provision all

        @Feature: Foreman Discovery

        @Assert: All host should be successfully rebooted and provisioned

        @Status: Manual

        """

    @stubbed()
    def test_add_new_discovery_fact(self):
        """@Test: Add a new fact column to display on discovered host page

        @Feature: Foreman Discovery

        @Steps:

        1. Goto settings -> Discovered tab -> discovery_fact_coloumn

        2. Edit discovery_fact_coloumn

        3. Add uuid or os

        @Assert: The added fact should be displayed on 'discovered_host' page
        after successful discovery

        @Status: Manual

        """

    @stubbed()
    def test_add_invalid_discovery_fact(self):
        """@Test: Add a new fact column with invalid fact to display on
        discovered host page

        @Feature: Foreman Discovery

        @Steps:

        1. Goto settings -> Discovered tab -> discovery_fact_coloumn

        2. Edit discovery_fact_coloumn

        3. Add 'test'

        @Assert: The added fact should be displayed on 'discovered_host' page
        after successful discovery and shows 'N/A'

        @Status: Manual

        """

    @stubbed()
    def test_discovery_manager_role(self):
        """@Test: Assign 'Discovery_Manager' role to a normal user

        @Feature: Foreman Discovery

        @Assert: User should be able to view, provision, edit and destroy one
        or more discovered host as well view, create_new, edit, execute and
        delete discovery rules.

        @Status: Manual

        """

    @stubbed()
    def test_discovery_role(self):
        """@Test: Assign 'Discovery" role to a normal user

        @Feature: Foreman Discovery

        @Assert: User should be able to view, provision, edit and destroy one
        or more discovered host

        @Status: Manual

        """
