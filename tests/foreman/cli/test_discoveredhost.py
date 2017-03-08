# -*- encoding: utf-8 -*-
"""Test class for CLI Foreman Discovery

:Requirement: Discoveredhost

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.discoveredhost import DiscoveredHost
from robottelo.cli.factory import (
    configure_env_for_provision,
    make_location,
    make_org,
)
from robottelo.cli.host import Host
from robottelo.cli.settings import Settings
from robottelo.cli.template import Template
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier3,
)
from robottelo.libvirt_discovery import LibvirtGuest
from robottelo.test import CLITestCase
from time import sleep


@run_in_one_thread
class DiscoveredTestCase(CLITestCase):
    """Implements Foreman discovery CLI tests."""

    def _assertdiscoveredhost(self, hostname):
        """Check if host is discovered and information about it can be
        retrieved back

        Introduced a delay of 300secs by polling every 10 secs to get expected
        host
        """
        for _ in range(30):
            try:
                discovered_host = DiscoveredHost.info({'name': hostname})
            except CLIReturnCodeError:
                sleep(10)
                continue
            return discovered_host

    @classmethod
    @skip_if_not_set('vlan_networking')
    def setUpClass(cls):
        """Steps to Configure foreman discovery

        1. Build PXE default template
        2. Create Organization/Location
        3. Update Global parameters to set default org and location for
           discovered hosts.
        4. Enable auto_provision flag to perform discovery via discovery
           rules.
        """
        super(DiscoveredTestCase, cls).setUpClass()

        # Build PXE default template to get default PXE file
        Template.build_pxe_default()

        # Create Org and location
        cls.org = make_org()
        cls.loc = make_location()

        # Get default settings values
        cls.default_discovery_loc = Settings.list(
            {'search': 'name=%s' % 'discovery_location'})[0]
        cls.default_discovery_org = Settings.list(
            {'search': 'name=%s' % 'discovery_organization'})[0]
        cls.default_discovery_auto = Settings.list(
            {'search': 'name=%s' % 'discovery_auto'})[0]

        # Update default org and location params to place discovered host
        Settings.set({'name': 'discovery_location', 'value': cls.loc['name']})
        Settings.set(
            {'name': 'discovery_organization', 'value': cls.org['name']})

        # Enable flag to auto provision discovered hosts via discovery rules
        Settings.set({'name': 'discovery_auto', 'value': 'true'})

        # Flag which shows whether environment is fully configured for
        # discovered host provisioning.
        cls.configured_env = False

    @classmethod
    def tearDownClass(cls):
        """Restore default global setting's values"""
        Settings.set({
            'name': 'discovery_location',
            'value': cls.default_discovery_loc['value']
        })
        Settings.set({
            'name': 'discovery_organization',
            'value': cls.default_discovery_org['value']
        })
        Settings.set({
            'name': 'discovery_auto',
            'value': cls.default_discovery_auto['value']
        })
        super(DiscoveredTestCase, cls).tearDownClass()

    @run_only_on('sat')
    @tier3
    def test_positive_pxe_based_discovery(self):
        """Discover a host via PXE boot by setting "proxy.type=proxy" in
        PXE default

        :id: 25e935fe-18f4-477e-b791-7ea5a395b4f6

        :Setup: Provisioning should be configured

        :Steps: PXE boot a host/VM

        :Assert: Host should be successfully discovered

        :CaseLevel: System
        """
        with LibvirtGuest() as pxe_host:
            hostname = pxe_host.guest_name
            host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(host)

    @run_only_on('sat')
    @tier3
    def test_positive_pxe_less_with_dhcp_unattended(self):
        """Discover a host with dhcp via bootable discovery ISO by setting
        "proxy.type=proxy" in PXE default in unattended mode.

        :id: a23bd065-8385-4876-aa45-e38470be79b8

        :Setup: Provisioning should be configured

        :Steps: Boot a host/VM using modified discovery ISO.

        :Assert: Host should be successfully discovered

        :CaseLevel: System
        """
        with LibvirtGuest(boot_iso=True) as pxe_less_host:
            hostname = pxe_less_host.guest_name
            host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(host)

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_custom_facts_pxeless_discovery(self):
        """Check if defined custom facts of pxeless host are correctly
        displayed under host's facts

        :id: 0d39f2cc-654f-41ed-8e31-4d9a37c5b9b1

        :Setup:

            1. Provisioning should be configured
            2. Host is already discovered

        :Steps: Validate specified custom facts

        :Assert: All defined custom facts should be displayed correctly

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_custom_facts_pxe_discovery(self):
        """Check if defined custom facts of pxe-based discovered host are
        correctly displayed under host's facts

        :id: 2c65925c-05d9-4f6d-b1b7-1fa1492c95a8

        :Setup:

            1. Provisioning should be configured
            2. Host is already discovered

        :Steps: Validate specified custom facts

        :Assert: All defined custom facts should be displayed correctly

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @tier3
    def test_positive_provision_pxeless_host(self):
        """Provision the pxe-less discovered host from cli

        :id: ae7f3ce2-e66e-44dc-85cb-0c3c4782cbb1

        :Setup: Host should already be discovered

        :Assert: Host should be provisioned successfully and entry from
            discovered host list should be auto removed

        :CaseLevel: System
        """
        if not self.configured_env:
            self.configured_env = configure_env_for_provision(
                org=self.org, loc=self.loc)
        with LibvirtGuest(boot_iso=True) as pxe_host:
            hostname = pxe_host.guest_name
            discovered_host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(discovered_host)
            # Provision just discovered host
            DiscoveredHost.provision({
                'name': discovered_host['name'],
                'hostgroup': self.configured_env['hostgroup']['name'],
                'root-password': gen_string('alphanumeric'),
            })
            provisioned_host = Host.info({
                'name': '{0}.{1}'.format(
                    discovered_host['name'],
                    self.configured_env['domain']['name']
                )
            })
            self.assertEqual(
                provisioned_host['network']['subnet'],
                self.configured_env['subnet']['name']
            )
            self.assertEqual(
                provisioned_host['operating-system']['partition-table'],
                self.configured_env['ptable']['name']
            )
            self.assertEqual(
                provisioned_host['operating-system']['operating-system'],
                self.configured_env['os']['title']
            )
            # Check that provisioned host is not in the list of discovered
            # hosts anymore
            with self.assertRaises(CLIReturnCodeError):
                DiscoveredHost.info({'id': discovered_host['id']})

    @run_only_on('sat')
    @tier3
    def test_positive_provision_pxe_host(self):
        """Provision the pxe based discovered host from cli

        :id: b5385fe3-d532-4373-af64-5492275ff8d4

        :Setup: Host should already be discovered

        :Assert: Host should be provisioned successfully and entry from
            discovered host list should be automatically removed.

        :CaseLevel: System
        """
        if not self.configured_env:
            self.configured_env = configure_env_for_provision(
                org=self.org, loc=self.loc)
        with LibvirtGuest() as pxe_host:
            hostname = pxe_host.guest_name
            discovered_host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(discovered_host)
            # Provision just discovered host
            DiscoveredHost.provision({
                'name': discovered_host['name'],
                'hostgroup': self.configured_env['hostgroup']['name'],
                'root-password': gen_string('alphanumeric'),
            })
            provisioned_host = Host.info({
                'name': '{0}.{1}'.format(
                    discovered_host['name'],
                    self.configured_env['domain']['name']
                )
            })
            self.assertEqual(
                provisioned_host['network']['subnet'],
                self.configured_env['subnet']['name']
            )
            self.assertEqual(
                provisioned_host['operating-system']['partition-table'],
                self.configured_env['ptable']['name']
            )
            self.assertEqual(
                provisioned_host['operating-system']['operating-system'],
                self.configured_env['os']['title']
            )
            # Check that provisioned host is not in the list of discovered
            # hosts anymore
            with self.assertRaises(CLIReturnCodeError):
                DiscoveredHost.info({'id': discovered_host['id']})

    @run_only_on('sat')
    @tier3
    def test_positive_delete_pxeless_host(self):
        """Delete the selected pxe-less discovered host

        :id: 3959abd7-a1c0-418f-a75a-dec06b5ea0e2

        :Setup: Host should already be discovered

        :Assert: Selected host should be removed successfully

        :CaseLevel: System
        """
        with LibvirtGuest(boot_iso=True) as pxe_less_host:
            hostname = pxe_less_host.guest_name
            host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(host)
        DiscoveredHost.delete({'id': host['id']})
        with self.assertRaises(CLIReturnCodeError):
            DiscoveredHost.info({'id': host['id']})

    @run_only_on('sat')
    @tier3
    def test_positive_delete_pxe_host(self):
        """Delete the selected pxe-based discovered host

        :id: c4103de8-145c-4a7d-b837-a1dec97231a2

        :Setup: Host should already be discovered

        :Assert: Selected host should be removed successfully

        :CaseLevel: System
        """
        with LibvirtGuest() as pxe_host:
            hostname = pxe_host.guest_name
            host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(host)
        DiscoveredHost.delete({'id': host['id']})
        with self.assertRaises(CLIReturnCodeError):
            DiscoveredHost.info({'id': host['id']})

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_refresh_facts_pxe_host(self):
        """Refresh the facts of pxe based discovered hosts by adding a new NIC

        :id: 410eaa5d-cc6a-44f7-8c6f-e8cfa81610f0

        :Setup: Host should already be discovered

        :Assert: Facts should be refreshed successfully with a new NIC

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_refresh_facts_of_pxeless_host(self):
        """Refresh the facts of pxeless discovered hosts by adding a new NIC

        :id: 2e199eaa-9651-47b1-a2fd-622778dfe68e

        :Setup: Host should already be discovered

        :Assert: Facts should be refreshed successfully with a new NIC

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_reboot_pxe_host(self):
        """Reboot pxe based discovered hosts

        :id: 9cc17742-f810-4be7-b410-a6c68e6cc64a

        :Setup: Host should already be discovered

        :Assert: Host is rebooted

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_reboot_pxeless_host(self):
        """Reboot pxe-less discovered hosts

        :id: e72e1607-8778-45b6-b8b9-8215514546f0

        :Setup: PXELess host should already be discovered

        :Assert: Host is rebooted

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_auto_provision_pxe_host(self):
        """Discover a pxe based host and auto-provision it with
        discovery rule and by enabling auto-provision flag

        :id: 701a1892-1c6a-4ba1-bbd8-a37b7fb02fa0

        :Assert: Host should be successfully rebooted and provisioned

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_auto_provision_pxeless_host(self):
        """Discover a pxe-less host and auto-provision it with
        discovery rule and by enabling auto-provision flag

        :id: 298417b3-d242-4999-89f9-198095704c0e

        :Assert: Host should be successfully rebooted and provisioned

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_list_discovered_host(self):
        """List pxe-based and pxe-less discovered hosts

        :id: 3a827080-3fab-4f64-a830-1b41841aa2df

        :Assert: Host should be discovered and listed with names.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_assign_discovery_manager_role(self):
        """Assign 'Discovery_Manager' role to a normal user

        :id: f694c361-5fbb-4c3a-b2ff-6dfe6ea14820

        :Assert: User should be able to view, provision, edit and destroy one
            or more discovered host as well view, create_new, edit, execute and
            delete discovery rules.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_assign_discovery_role(self):
        """Assign 'Discovery" role to a normal user

        :id: 873e8411-563d-4bf9-84ce-62e522410cfe

        :Assert: User should be able to list, provision, and destroy one or
            more discovered host

        :caseautomation: notautomated

        :CaseLevel: System
        """
