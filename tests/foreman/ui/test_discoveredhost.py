# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.decorators import run_only_on, skip_if_not_set, stubbed, tier3
from robottelo.libvirt_discovery import LibvirtGuest
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import edit_param
from robottelo.ui.locators import locators, tab_locators
from robottelo.ui.session import Session
from time import sleep


class DiscoveryTestCase(UITestCase):
    """Implements Foreman discovery tests in UI."""

    def _assertdiscoveredhost(self, hostname):
        """
        Check if host is visible under 'Discovered Hosts' on UI

        Introduced a delay of 100secs by polling every 10 secs to see if
        unknown host gets discovered and become visible on UI
        """
        discovered_host = self.discoveredhosts.search(hostname)
        for _ in range(10):
            if discovered_host is None:
                sleep(10)
                discovered_host = self.discoveredhosts.search(hostname)
            else:
                break

    def _edit_discovery_fact_column_param(self, session, param_value):
        """
        Edit the 'discovery_fact_column' parameter from settings menu.

        User can populate a new column on 'Discovered Hosts' page by setting
        the value of 'discovery_fact_column'
        """
        tab_locator = tab_locators['settings.tab_discovered']
        param_name = 'discovery_fact_column'
        edit_param(
            session=session,
            tab_locator=tab_locator,
            param_name=param_name,
            value_type='input',
            param_value=param_value,
        )
        saved_element = self.settings.get_saved_value(
            tab_locator, param_name)
        self.assertEqual(param_value, saved_element)

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
        super(DiscoveryTestCase, cls).setUpClass()

        # Build PXE default template to get default PXE file
        entities.ConfigTemplate().build_pxe_default()

        # Create Org and location
        cls.org = entities.Organization(name=gen_string('alpha')).create()
        cls.org_name = cls.org.name
        cls.loc = entities.Location(
            name=gen_string('alpha'),
            organization=[cls.org],
        ).create()

        # Update default org and location params to place discovered host
        cls.discovery_loc = entities.Setting().search(
            query={'search': 'name="discovery_location"'})[0]
        cls.discovery_loc.value = cls.loc.name
        cls.discovery_loc.update({'value'})
        cls.discovery_org = entities.Setting().search(
            query={'search': 'name="discovery_organization"'})[0]
        cls.discovery_org.value = cls.org.name
        cls.discovery_org.update({'value'})

        # Enable flag to auto provision discovered hosts via discovery rules
        cls.discovery_auto = entities.Setting().search(
            query={'search': 'name="discovery_auto"'})[0]
        cls.default_discovery_auto = str(cls.discovery_auto.value)
        cls.discovery_auto.value = 'True'
        cls.discovery_auto.update({'value'})

    @classmethod
    def tearDownClass(cls):
        """Restore default 'discovery_auto' global setting's value"""
        cls.discovery_auto.value = cls.default_discovery_auto
        cls.discovery_auto.update({'value'})

        super(DiscoveryTestCase, cls).tearDownClass()

    @run_only_on('sat')
    @tier3
    def test_positive_pxe_based_discovery(self):
        """Discover a host via PXE boot by setting "proxy.type=proxy" in
        PXE default

        @Feature: Foreman Discovery - PXEBased

        @Setup: Provisioning should be configured

        @Steps: PXE boot a host/VM

        @Assert: Host should be successfully discovered

        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            with LibvirtGuest() as pxe_host:
                hostname = pxe_host.guest_name
                self._assertdiscoveredhost(hostname)
                self.assertIsNotNone(self.discoveredhosts.search(hostname))

    @run_only_on('sat')
    @tier3
    def test_positive_pxe_less_with_dhcp_unattended(self):
        """Discover a host with dhcp via bootable discovery ISO by setting
        "proxy.type=proxy" in PXE default in unattended mode.

        @Feature: Foreman Discovery - PXELess

        @Setup: Provisioning should be configured

        @Steps: Boot a host/VM using modified discovery ISO.

        @Assert: Host should be successfully discovered

        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            with LibvirtGuest(boot_iso=True) as pxe_less_host:
                hostname = pxe_less_host.guest_name
                self._assertdiscoveredhost(hostname)
                self.assertIsNotNone(self.discoveredhosts.search(hostname))

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_with_dhcp_semiauto(self):
        """Discover a host with dhcp via bootable discovery ISO in
        semi-automated mode.

        @Feature: Foreman Discovery - PXELess

        @Setup: Provisioning should be configured

        @Steps: Boot a host/VM using discovery ISO

        @Assert: Host should be successfully discovered

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_with_dhcp_interactively(self):
        """Discover a host with dhcp via bootable discovery ISO using
        interactive TUI mode.

        @Feature: Foreman Discovery - PXELess

        @Setup: Provisioning should be configured

        @Steps: Boot a host/VM using discovery ISO

        @Assert: Host should be successfully discovered

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_without_dhcp_interactively(self):
        """Discover a host with single NIC on a network without DHCP and PXE
        using ISO image in interactive TUI interface.

        @Feature: Foreman Discovery

        @Assert: Host should be discovered successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_without_dhcp_semiauto(self):
        """Discover a host with single NIC on a network without DHCP and PXE
        using ISO image in semi-automated mode.

        @Feature: Foreman Discovery

        @Assert: Host should be discovered successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_without_dhcp_unattended(self):
        """Discover a host with single NIC on a network without DHCP and PXE
        using ISO image in unattended mode.

        @Feature: Foreman Discovery

        @Assert: Host should be discovered successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_discover_pxe_less_with_efi_host_interatively(self):
        """Discover a EFI host with single NIC on a network
        using ISO image in interactive TUI mode.

        @Feature: Foreman Discovery - PXELess

        @Assert: Host should be discovered successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_discover_pxe_less_with_efi_host_unattended(self):
        """Discover a EFI host with single NIC on a network
        using ISO image in unattended mode.

        @Feature: Foreman Discovery - PXELess

        @Assert: Host should be discovered successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_multi_nic_with_dhcp_unattended(self):
        """Discover a host with multiple NIC on a network with dhcp
        using ISO image in unattended mode.

        @Feature: Foreman Discovery - PXELess

        @Assert: Host should be discovered successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_multi_nic_with_dhcp_interactively(self):
        """Discover a host with multiple NIC on a network with dhcp
        using ISO image in interactive TUI mode.

        @Feature: Foreman Discovery - PXELess

        @Assert: Host should be discovered successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_multi_nic_without_dhcp_interactively(self):
        """Discover a host with multiple NIC on a network without dhcp
        using ISO image in interactive TUI mode.

        @Feature: Foreman Discovery - PXELess

        @Assert: Host should be discovered successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_multi_nic_without_dhcp_unattended(self):
        """Discover a host with multiple NIC on a network without dhcp
        using ISO image in unattended mode.

        @Feature: Foreman Discovery - PXELess

        @Assert: Host should be discovered successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_multi_nic_unattended(self):
        """Discover a host with multiple NIC on a network with dhcp
        using pxe in unattended mode.

        @Feature: Foreman Discovery - PXEBased

        @Assert: Host should be discovered successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @tier3
    def test_custom_facts_discovery(self):
        """Check if defined custom facts are displayed under host's facts

        @Feature: Foreman Discovery - PXELess

        @Setup: Provisioning should be configured

        @Steps: Validate specified custom facts

        @Assert: All defined custom facts should be displayed correctly

        """
        param_value = 'myfact'
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            # To show new fact column 'Interfaces' on Discovered Hosts page
            self._edit_discovery_fact_column_param(session, param_value)
            with LibvirtGuest(boot_iso=True) as pxe_less_host:
                hostname = pxe_less_host.guest_name
                self._assertdiscoveredhost(hostname)
                element = locators['discoveredhosts.fetch_custom_fact']
                custom_fact = self.discoveredhosts.fetch_fact_value(
                    hostname, element)
                self.assertEqual(u'somevalue', custom_fact)

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision(self):
        """Provision the selected discovered host by selecting
        'provision' button from 'Discovered Host' page.

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should be provisioned successfully and entry from
        discovered host should be auto removed

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_from_facts(self):
        """Provision the selected discovered host from facts page by
        clicking 'provision'

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should be provisioned successfully and entry from
        discovered host should be auto removed

        @Status: Manual
        """

    @run_only_on('sat')
    @tier3
    def test_positive_delete(self):
        """Delete the selected discovered host

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            with LibvirtGuest() as pxe_host:
                hostname = pxe_host.guest_name
                self._assertdiscoveredhost(hostname)
                self.discoveredhosts.delete(hostname)

    @run_only_on('sat')
    @tier3
    def test_positive_delete_from_facts(self):
        """Delete the selected discovered host from facts page

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            with LibvirtGuest() as pxe_host:
                hostname = pxe_host.guest_name
                self._assertdiscoveredhost(hostname)
                self.discoveredhosts.delete_from_facts(hostname)
                self.assertIsNone(self.discoveredhosts.search(hostname))

    @run_only_on('sat')
    @tier3
    def test_positive_delete_multiple(self):
        """Delete multiple discovered hosts from 'Select Action'
        drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        """
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            with LibvirtGuest() as pxe_1_host:
                host_1_name = pxe_1_host.guest_name
                self._assertdiscoveredhost(host_1_name)
                with LibvirtGuest() as pxe_2_host:
                    host_2_name = pxe_2_host.guest_name
                    self._assertdiscoveredhost(host_2_name)
                    for hostname in [host_1_name, host_2_name]:
                        host = self.discoveredhosts.search(hostname)
                        if not host:
                            raise UIError(
                                'Could not find the selected discovered host '
                                '"{0}"'.format(hostname)
                            )
                        self.discoveredhosts.navigate_to_entity()
                        # To delete multiple discovered hosts
                        self.discoveredhosts.multi_delete()
                        for hostname in [host_1_name, host_2_name]:
                            self.assertIsNone(
                                self.discoveredhosts.search(hostname))

    @run_only_on('sat')
    @tier3
    def test_positive_refresh_facts_pxe(self):
        """Refresh the facts of pxe-based discovered host by adding a new NIC.

        @Feature: Foreman Discovery - PXEBased

        @Setup: Host should already be discovered

        @Assert: Facts should be refreshed successfully with new NIC

        """
        param_value = 'interfaces'
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            # To show new fact column 'Interfaces' on Discovered Hosts page
            self._edit_discovery_fact_column_param(session, param_value)
            with LibvirtGuest() as pxe_host:
                hostname = pxe_host.guest_name
                self._assertdiscoveredhost(hostname)
                self.assertIsNotNone(self.discoveredhosts.search(hostname))
                # To add a new network interface on discovered host
                pxe_host.attach_nic()
                # To refresh the facts of discovered host,
                # UI should show newly added interface on refresh_facts
                self.discoveredhosts.refresh_facts(hostname)
                element = locators['discoveredhosts.fetch_interfaces']
                host_interfaces = self.discoveredhosts.fetch_fact_value(
                    hostname, element)
                self.assertEqual(u'eth0,eth1,lo', host_interfaces)

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_refresh_facts_pxe_less(self):
        """Refresh the facts of pxe-less discovered host by adding a new NIC.

        @Feature: Foreman Discovery - PXELess

        @Setup: Host should already be discovered

        @Assert: Facts should be refreshed successfully with new NIC

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_reboot(self):
        """Reboot a discovered host.

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should be successfully rebooted.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_default_org(self):
        """Change the default org of more than one discovered hosts
        from 'Select Action' drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Default org should be successfully changed for multiple hosts

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_default_location(self):
        """Change the default location of more than one discovered hosts
        from 'Select Action' drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Default Location should be successfully changed for multiple
        hosts

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_host_with_rule(self):
        """Create a new discovery rule and provision a discovered host using
        that discovery rule.

        Set query as (e.g IP=IP_of_discovered_host)

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should reboot and provision

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_multi_host_with_rule(self):
        """Create a new discovery rule with (host_limit = 0)
        that applies to multi hosts.
        Set query as cpu_count = 1 OR mem > 500

        @Feature: Foreman Discovery

        @Setup: Multiple hosts should already be discovered in same subnet.

        @Assert: All Hosts of same subnet should reboot and provision

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_with_rule_priority(self):
        """Create multiple discovery rules with different priority and check
        rule with highest priority executed first

        @Feature: Foreman Discovery

        @Setup: Multiple hosts should already be discovered

        @Assert: Host with lower count have higher priority
        and that rule should be executed first.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_without_auto_provision(self):
        """Create a discovery rule and execute it when
        "auto_provisioning" flag set to 'false'

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should not be rebooted automatically

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_create_discovery_rule(self):
        """Create a discovery rule with invalid query
        e.g. BIOS = xyz

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Rule should automatically be skipped on clicking
        'Auto provision'. UI Should raise 'No matching rule found'

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_multi_provision_with_rule_limit(self):
        """Create a discovery rule (CPU_COUNT = 2) with host limit 1 and
        provision more than one host with same rule

        @Feature: Foreman Discovery

        @Setup: Host with two CPUs should already be discovered

        @Assert: Rule should only be applied to one discovered host and for
        other rule should already be skipped.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_discovery_rule(self):
        """Update an existing rule and execute it

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: User should be able to update the rule and it should be
        executed on discovered host

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_name(self):
        """Update the discovered host name and provision it

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: The hostname should be updated and host should be provisioned

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_discovery_prefix(self):
        """Update the discovery_prefix parameter other than mac

        @Feature: Foreman Discovery

        @Steps:

        1. Goto settings &#8592; Discovered tab -> discovery_prefix

        2. Edit discovery_prefix using any text that must start with a letter

        @Setup: Host should already be discovered

        @Assert: discovery_prefix is updated and provisioned host has same
        prefix in its hostname

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_auto_provision_all(self):
        """Discover a bunch of hosts and auto-provision all

        @Feature: Foreman Discovery

        @Assert: All host should be successfully rebooted and provisioned

        @Status: Manual
        """

    @run_only_on('sat')
    @tier3
    def test_positive_add_fact_column(self):
        """Add a new fact column to display on discovered host page

        @Feature: Foreman Discovery - PXEBased

        @Steps:

        1. Goto settings -> Discovered tab -> discovery_fact_coloumn

        2. Edit discovery_fact_coloumn

        3. Add bios_vendor

        @Assert: The added fact should be displayed on 'discovered_host' page
        after successful discovery

        """
        param_value = 'bios_vendor'
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            # To show new fact column 'Interfaces' on Discovered Hosts page
            self._edit_discovery_fact_column_param(session, param_value)
            with LibvirtGuest() as pxe_host:
                hostname = pxe_host.guest_name
                self._assertdiscoveredhost(hostname)
                element = locators['discoveredhosts.fetch_bios']
                host_bios = self.discoveredhosts.fetch_fact_value(
                    hostname, element)
                self.assertEqual(u'Seabios', host_bios)

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_add_fact(self):
        """Add a new fact column with invalid fact to display on
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

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_discovery_manager_role(self):
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
    def test_positive_discovery_reader_role(self):
        """Assign 'Discovery Reader" role to a normal user

        @Feature: Foreman Discovery

        @Assert: User should be able to view existing discovered host and rule

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_pxe_less_discovery_status_screen(self):
        """Validate all the buttons from "Discovery Status" TUI screen of a
        pxe-less discovered host

        @Feature: Foreman Discovery

        @Assert: All buttons should work

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_network_config_screen(self):
        """Validate network configuration screen by specifying invalid
        IP/gateway/DNS address notation.

        @Feature: Foreman Discovery

        @Assert: User should get an error message

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_pxe_less_discovery_without_dhcp(self):
        """Discover a host via pxe-less and select "Discover using DHCP"
        interactively when no dhcp is available.

        @Feature: Foreman Discovery - PXELess

        @Assert: User should get an error message "Unable to bring network via
        DHCP" and click on 'OK' should open the ''Network configuration screen"
        to manually specify the IP/GW/DNS.

        @Status: Manual
        """
