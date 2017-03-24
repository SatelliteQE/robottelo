# -*- encoding: utf-8 -*-
"""Test class for CLI Foreman Discovery

@Requirement: Discoveredhost

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
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

        @id: 0d39f2cc-654f-41ed-8e31-4d9a37c5b9b1

        @Setup:

        1. Provisioning should be configured

        2. Host is already discovered

        @Steps: Validate specified custom facts

        @expectedresults: All defined custom facts should be displayed
        correctly

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_custom_facts_pxe_discovery(self):
        """Check if defined custom facts of pxe-based discovered host are
        correctly displayed under host's facts

        @id: 2c65925c-05d9-4f6d-b1b7-1fa1492c95a8

        @Setup:

        1. Provisioning should be configured

        2. Host is already discovered

        @Steps: Validate specified custom facts

        @expectedresults: All defined custom facts should be displayed
        correctly

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_pxeless_host(self):
        """Provision the pxe-less discovered host from cli

        @id: ae7f3ce2-e66e-44dc-85cb-0c3c4782cbb1

        @Setup: Host should already be discovered

        @expectedresults: Host should be provisioned successfully and entry
        from discovered host list should be auto removed

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_pxe_host(self):
        """Provision the pxe based discovered host from cli

        @id: b5385fe3-d532-4373-af64-5492275ff8d4

        @Setup: Host should already be discovered

        @expectedresults: Host should be provisioned successfully and entry
        from discovered host list should be automatically removed.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_delete_pxeless_host(self):
        """Delete the selected pxe-less discovered host

        @id: 3959abd7-a1c0-418f-a75a-dec06b5ea0e2

        @Setup: Host should already be discovered

        @expectedresults: Selected host should be removed successfully

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_delete_pxe_host(self):
        """Delete the selected pxe-based discovered host

        @id: c4103de8-145c-4a7d-b837-a1dec97231a2

        @Setup: Host should already be discovered

        @expectedresults: Selected host should be removed successfully

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_refresh_facts_pxe_host(self):
        """Refresh the facts of pxe based discovered hosts by adding a new NIC

        @id: 410eaa5d-cc6a-44f7-8c6f-e8cfa81610f0

        @Setup: Host should already be discovered

        @expectedresults: Facts should be refreshed successfully with a new NIC

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_refresh_facts_of_pxeless_host(self):
        """Refresh the facts of pxeless discovered hosts by adding a new NIC

        @id: 2e199eaa-9651-47b1-a2fd-622778dfe68e

        @Setup: Host should already be discovered

        @expectedresults: Facts should be refreshed successfully with a new NIC

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_reboot_pxe_host(self):
        """Reboot pxe based discovered hosts

        @id: 9cc17742-f810-4be7-b410-a6c68e6cc64a

        @Setup: Host should already be discovered

        @expectedresults: Host is rebooted

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_reboot_pxeless_host(self):
        """Reboot pxe-less discovered hosts

        @id: e72e1607-8778-45b6-b8b9-8215514546f0

        @Setup: PXELess host should already be discovered

        @expectedresults: Host is rebooted

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_auto_provision_pxe_host(self):
        """Discover a pxe based host and auto-provision it with
        discovery rule and by enabling auto-provision flag

        @id: 701a1892-1c6a-4ba1-bbd8-a37b7fb02fa0

        @expectedresults: Host should be successfully rebooted and provisioned

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_auto_provision_pxeless_host(self):
        """Discover a pxe-less host and auto-provision it with
        discovery rule and by enabling auto-provision flag

        @id: 298417b3-d242-4999-89f9-198095704c0e

        @expectedresults: Host should be successfully rebooted and provisioned

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_discovered_host(self):
        """List pxe-based and pxe-less discovered hosts

        @id: 3a827080-3fab-4f64-a830-1b41841aa2df

        @expectedresults: Host should be discovered and listed with names.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_assign_discovery_manager_role(self):
        """Assign 'Discovery_Manager' role to a normal user

        @id: f694c361-5fbb-4c3a-b2ff-6dfe6ea14820

        @expectedresults: User should be able to view, provision, edit and
        destroy one or more discovered host as well view, create_new, edit,
        execute and delete discovery rules.

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_assign_discovery_role(self):
        """Assign 'Discovery" role to a normal user

        @id: 873e8411-563d-4bf9-84ce-62e522410cfe

        @expectedresults: User should be able to list, provision, and destroy
        one or more discovered host

        @caseautomation: notautomated

        @CaseLevel: System
        """
