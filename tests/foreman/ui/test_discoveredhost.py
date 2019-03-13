# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery

:Requirement: Discoveredhost

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import subprocess
import time

from fauxfactory import gen_string
from nailgun import entities
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier3,
)
from robottelo.api.utils import configure_provisioning
from robottelo.libvirt_discovery import LibvirtGuest
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import (
    edit_param,
    make_discoveryrule,
)
from robottelo.ui.locators import locators, tab_locators
from robottelo.ui.session import Session


@run_in_one_thread
class DiscoveryTestCase(UITestCase):
    """Implements Foreman discovery tests in UI."""

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

    def _ping_host(self, host, timeout=60):
        """Helper to ensure given IP/hostname is reachable after reboot.

        :param host: A string. The IP or hostname of host.
        :param int timeout: The polling timeout in seconds.
        """
        timeup = time.time() + int(timeout)
        while True:
            command = subprocess.Popen(
                'ping -c1 {0}; echo $?'.format(host),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            output = command.communicate()[0]
            # Checking the return code of ping is 0
            if time.time() > timeup:
                return False
            if int(output.split()[-1]) == 0:
                return True
            else:
                time.sleep(5)

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

        cls.config_env = configure_provisioning(org=cls.org, loc=cls.loc)

    @classmethod
    def tearDownClass(cls):
        """Restore default 'discovery_auto' global setting's value"""
        cls.discovery_auto.value = cls.default_discovery_auto
        cls.discovery_auto.update({'value'})

        super(DiscoveryTestCase, cls).tearDownClass()

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_with_dhcp_semiauto(self):
        """Discover a host with dhcp via bootable discovery ISO in
        semi-automated mode.

        :id: 05c88618-6f15-4eb8-8501-3505160c5450

        :Setup: Provisioning should be configured

        :Steps: Boot a host/VM using discovery ISO

        :expectedresults: Host should be successfully discovered

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_with_dhcp_interactively(self):
        """Discover a host with dhcp via bootable discovery ISO using
        interactive TUI mode.

        :id: 08780627-9ac1-4837-88eb-df673d974d05

        :Setup: Provisioning should be configured

        :Steps: Boot a host/VM using discovery ISO

        :expectedresults: Host should be successfully discovered

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_without_dhcp_interactively(self):
        """Discover a host with single NIC on a network without DHCP and PXE
        using ISO image in interactive TUI interface.

        :id: 9703eb00-9857-4076-8b83-031a58d7c1cd

        :expectedresults: Host should be discovered successfully

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_without_dhcp_semiauto(self):
        """Discover a host with single NIC on a network without DHCP and PXE
        using ISO image in semi-automated mode.

        :id: 8254a85f-21c8-4483-b453-15126762f6e5

        :expectedresults: Host should be discovered successfully

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_without_dhcp_unattended(self):
        """Discover a host with single NIC on a network without DHCP and PXE
        using ISO image in unattended mode.

        :id: ae75173f-8358-4886-9420-06cff3a8510e

        :expectedresults: Host should be discovered successfully

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_discover_pxe_less_with_efi_host_interatively(self):
        """Discover a EFI host with single NIC on a network
        using ISO image in interactive TUI mode.

        :id: f13fd843-6b39-4c5e-bb7a-b9af9e71eb7b

        :expectedresults: Host should be discovered successfully

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_discover_pxe_less_with_efi_host_unattended(self):
        """Discover a EFI host with single NIC on a network
        using ISO image in unattended mode.

        :id: 515d32ce-44eb-4d27-a353-699bc80fc566

        :expectedresults: Host should be discovered successfully

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @tier3
    def test_positive_pxe_less_multi_nic_with_dhcp_unattended(self):
        """Discover a host with multiple NIC on a network with dhcp
        using ISO image in unattended mode.

        :id: cdfebc3d-d8c1-4f82-a384-cc5cd9926c65

        :expectedresults: Host should be discovered successfully

        :CaseLevel: System
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            # To show new fact column 'Interfaces' on Discovered Hosts page
            self._edit_discovery_fact_column_param(session, "interfaces")
            with LibvirtGuest(boot_iso=True, extra_nic=True) as pxe_less_host:
                hostname = pxe_less_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(hostname)
                )
                self.assertIsNotNone(self.discoveredhosts.search(hostname))
                element = locators['discoveredhosts.fetch_interfaces']
                host_interfaces = self.discoveredhosts.fetch_fact_value(
                    hostname, element)
                self.assertEqual(u'eth0,eth1,lo', host_interfaces)

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_multi_nic_with_dhcp_interactively(self):
        """Discover a host with multiple NIC on a network with dhcp
        using ISO image in interactive TUI mode.

        :id: e29c7f71-096e-42ef-9bbf-77fecac86a9c

        :expectedresults: Host should be discovered successfully

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_multi_nic_without_dhcp_interactively(self):
        """Discover a host with multiple NIC on a network without dhcp
        using ISO image in interactive TUI mode.

        :id: 206a375c-3f42-4cc8-b338-bb85127cffc9

        :expectedresults: Host should be discovered successfully

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_pxe_less_multi_nic_without_dhcp_unattended(self):
        """Discover a host with multiple NIC on a network without dhcp
        using ISO image in unattended mode.

        :id: 1e25326d-2976-4a12-8e02-c4be6705f522

        :expectedresults: Host should be discovered successfully

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @tier3
    def test_positive_pxe_multi_nic_unattended(self):
        """Discover a host with multiple NIC on a network with dhcp
        using pxe in unattended mode.

        :id: 0d004ed0-594f-492f-8756-33349094aa8e

        :expectedresults: Host should be discovered successfully

        :CaseLevel: System
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            # To show new fact column 'Interfaces' on Discovered Hosts page
            self._edit_discovery_fact_column_param(session, "interfaces")
            with LibvirtGuest(extra_nic=True) as pxe_host:
                hostname = pxe_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(hostname)
                )
                self.assertIsNotNone(self.discoveredhosts.search(hostname))
                element = locators['discoveredhosts.fetch_interfaces']
                host_interfaces = self.discoveredhosts.fetch_fact_value(
                    hostname, element)
                self.assertEqual(u'eth0,eth1,lo', host_interfaces)

    @run_only_on('sat')
    @tier3
    def test_custom_facts_discovery(self):
        """Check if defined custom facts are displayed under host's facts

        :id: 5492e063-72db-44b8-a34a-9c75c351b89a

        :Setup: Provisioning should be configured

        :Steps: Validate specified custom facts

        :expectedresults: All defined custom facts should be displayed
            correctly

        :CaseLevel: System
        """
        param_value = 'myfact'
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            # To show new fact column 'Interfaces' on Discovered Hosts page
            self._edit_discovery_fact_column_param(session, param_value)
            with LibvirtGuest(boot_iso=True) as pxe_less_host:
                hostname = pxe_less_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(hostname)
                )
                element = locators['discoveredhosts.fetch_custom_fact']
                custom_fact = self.discoveredhosts.fetch_fact_value(
                    hostname, element)
                self.assertEqual(u'somevalue', custom_fact)

    @run_only_on('sat')
    @tier3
    def test_positive_provision_from_facts(self):
        """Provision the selected discovered host from facts page by
        clicking 'provision'

        :id: 610bbf32-b342-44ef-8339-0201e0592260

        :Setup: Host should already be discovered

        :expectedresults: Host should be provisioned successfully and entry
            from discovered host should be auto removed

        :CaseLevel: System
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            with LibvirtGuest() as pxe_host:
                host_name = pxe_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(host_name)
                )
                self.discoveredhosts.provision_discoveredhost(
                    hostname=host_name,
                    hostgroup=self.config_env['host_group'],
                    org=self.org_name,
                    loc=self.loc.name,
                    facts_page=True,
                    quick_create=True)
                # the provisioning take some time to finish, when done will be
                # redirected to the created host
                # wait until redirected to host page
                pxe_host_name = '{0}.{1}'.format(
                    host_name, self.config_env['domain'])
                self.assertIsNotNone(
                    session.hosts.wait_until_element(
                        locators["host.host_page_title"] % pxe_host_name,
                        timeout=160
                    )
                )
                host_properties = session.hosts.get_host_properties(
                    pxe_host_name, ['status'])
                self.assertTrue(host_properties)
                self.assertEqual(host_properties['status'], 'OK')
                # Check that provisioned host is not in the list of discovered
                # hosts anymore
                self.assertIsNone(self.discoveredhosts.search(host_name))

    @run_only_on('sat')
    @tier3
    def test_positive_delete_from_facts(self):
        """Delete the selected discovered host from facts page

        :id: 892aa809-bcf0-46ae-8495-70d7a6483b75

        :Setup: Host should already be discovered

        :expectedresults: Selected host should be removed successfully

        :CaseLevel: System
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            with LibvirtGuest() as pxe_host:
                hostname = pxe_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(hostname)
                )
                self.discoveredhosts.delete_from_facts(hostname)
                self.assertIsNone(self.discoveredhosts.search(hostname))

    @run_only_on('sat')
    @tier3
    def test_positive_delete_multiple(self):
        """Delete multiple discovered hosts from 'Select Action'
        drop down

        :id: 556fb306-512f-46a4-8a0f-af8013161efe

        :Setup: Host should already be discovered

        :expectedresults: Selected host should be removed successfully

        :CaseLevel: System
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            with LibvirtGuest() as pxe_1_host:
                host_1_name = pxe_1_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(host_1_name)
                )
                with LibvirtGuest() as pxe_2_host:
                    host_2_name = pxe_2_host.guest_name
                    self.assertTrue(
                        self.discoveredhosts.waitfordiscoveredhost(host_2_name)
                    )
                    hostnames = [host_1_name, host_2_name]
                    for hostname in hostnames:
                        host = self.discoveredhosts.search(hostname)
                        if not host:
                            raise UIError(
                                'Could not find the selected discovered host '
                                '"{0}"'.format(hostname)
                            )
                    self.discoveredhosts.navigate_to_entity()
                    # To delete multiple discovered hosts
                    self.discoveredhosts.multi_delete(hostnames)
                    for hostname in [host_1_name, host_2_name]:
                        self.assertIsNone(
                            self.discoveredhosts.search(hostname)
                        )

    @run_only_on('sat')
    @tier3
    def test_positive_refresh_facts_pxe(self):
        """Refresh the facts of pxe-based discovered host by adding a new NIC.

        :id: cda4103c-6d1a-4f9e-bf57-e516ef1f2a37

        :Setup: Host should already be discovered

        :expectedresults: Facts should be refreshed successfully with new NIC

        :CaseLevel: System
        """
        param_value = 'interfaces'
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            # To show new fact column 'Interfaces' on Discovered Hosts page
            self._edit_discovery_fact_column_param(session, param_value)
            with LibvirtGuest() as pxe_host:
                hostname = pxe_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(hostname)
                )
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
    @tier3
    def test_positive_refresh_facts_pxe_less(self):
        """Refresh the facts of pxe-less discovered host by adding a new NIC.

        :id: 367a5336-a0fa-491b-8153-3e39d68eb978

        :Setup: Host should already be discovered

        :expectedresults: Facts should be refreshed successfully with new NIC

        :CaseLevel: System
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            # To show new fact column 'Interfaces' on Discovered Hosts page
            self._edit_discovery_fact_column_param(session, 'interfaces')
            with LibvirtGuest(boot_iso=True) as pxe_less_host:
                hostname = pxe_less_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(hostname)
                )
                self.assertIsNotNone(self.discoveredhosts.search(hostname))
                # To add a new network interface on discovered host
                pxe_less_host.attach_nic()
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
    def test_positive_auto_provision_host_with_rule(self):
        """Create a new discovery rule and provision a discovered host using
        that discovery rule.

        Set query as (e.g IP=IP_of_discovered_host)

        :id: 00686008-87eb-4b76-9579-ceddb578ef31

        :Setup: Host should already be discovered

        :expectedresults: Host should reboot and provision

        :CaseLevel: System

        :CaseAutomation: notautomated
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_multi_host_with_rule(self):
        """Create a new discovery rule with (host_limit = 0)
        that applies to multi hosts.
        Set query as cpu_count = 1 OR mem > 500

        :id: d25c088f-ee7a-4a3a-9b51-8f65f545e680

        :Setup: Multiple hosts should already be discovered in same subnet.

        :expectedresults: All Hosts of same subnet should reboot and provision

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_with_rule_priority(self):
        """Create multiple discovery rules with different priority and check
        rule with highest priority executed first

        :id: 8daf0b35-912b-441d-97d3-45f48799f4ba

        :Setup: Multiple hosts should already be discovered

        :expectedresults: Host with lower count have higher priority and that
            rule should be executed first.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @tier3
    def test_positive_provision_without_auto_provision(self):
        """Create a discovery rule and execute it when
        "auto_provisioning" flag set to 'false'

        :id: 25f5112b-7bbd-4bda-8d75-c43bd6390aa8

        :Setup: Host should already be discovered

        :expectedresults: Host should not be rebooted automatically

        :CaseLevel: System
        """
        try:
            # Disable flag to auto provision
            discovery_auto = entities.Setting().search(
                query={'search': 'name="discovery_auto"'})[0]
            default_discovery_auto = discovery_auto.value
            discovery_auto.value = 'False'
            discovery_auto.update(['value'])
            rule_name = gen_string('alpha')
            with Session(self) as session:
                session.nav.go_to_select_org(self.org_name)
                # Define a discovery rule
                make_discoveryrule(
                    session,
                    name=rule_name,
                    host_limit=1,
                    hostgroup=self.config_env['host_group'],
                    search_rule='cpu_count = 1',
                    locations=[self.loc.name],
                )
                self.assertIsNotNone(self.discoveryrules.search(rule_name))
                with LibvirtGuest() as pxe_host:
                    host_name = pxe_host.guest_name
                    self.assertTrue(
                        self.discoveredhosts.waitfordiscoveredhost(host_name)
                    )
                    self.assertIsNotNone(
                        self.discoveredhosts.search(host_name))
                    # Check that host shouldn't list under all hosts
                    self.assertIsNone(self.hosts.search(
                        u'{0}.{1}'.format(host_name, self.config_env['domain'])
                    ))
                    # Check that host still listed under discovered hosts
                    self.assertIsNotNone(
                        self.discoveredhosts.search(host_name))
        finally:
            # Revert the discovery_auto flag to default value
            discovery_auto.value = default_discovery_auto
            discovery_auto.update(['value'])

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_create_discovery_rule(self):
        """Create a discovery rule with invalid query
        e.g. BIOS = xyz

        :id: 89014adf-6346-4681-9107-6d92e14b6a3e

        :Setup: Host should already be discovered

        :expectedresults: Rule should automatically be skipped on clicking
            'Auto provision'. UI Should raise 'No matching rule found'

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_multi_provision_with_rule_limit(self):
        """Create a discovery rule (CPU_COUNT = 2) with host limit 1 and
        provision more than one host with same rule

        :id: ab14c56d-331f-466b-aeb0-41fb19f7b3aa

        :Setup: Host with two CPUs should already be discovered

        :expectedresults: Rule should only be applied to one discovered host
            and for other rule should already be skipped.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_discovery_rule(self):
        """Update an existing rule and execute it

        :id: 0969cf6f-215d-44c5-96b5-91cb1d865ad0

        :Setup: Host should already be discovered

        :expectedresults: User should be able to update the rule and it should
            be executed on discovered host

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @tier3
    def test_positive_auto_provision_all(self):
        """Discover a bunch of hosts and auto-provision all

        :id: e26129b5-16fa-418c-b768-21670e9f0b74

        :expectedresults: All host should be successfully rebooted and
            provisioned

        :CaseLevel: System
        """
        rule_name = gen_string('alpha')
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            with LibvirtGuest() as pxe_1_host, LibvirtGuest() as pxe_2_host:
                host_1_name = pxe_1_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(host_1_name)
                )
                host_2_name = pxe_2_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(host_2_name)
                )
                # Define a discovery rule
                make_discoveryrule(
                    session,
                    name=rule_name,
                    host_limit=2,
                    hostgroup=self.config_env['host_group'],
                    search_rule='cpu_count = 1',
                    locations=[self.loc.name],
                )
                self.assertIsNotNone(self.discoveryrules.search(rule_name))
                self.discoveredhosts.auto_provision_all()
                hostnames = [host_1_name, host_2_name]
                for hostname in hostnames:
                    self.assertIsNotNone(self.hosts.search(
                        u'{0}.{1}'.format(
                            hostname, self.config_env['domain'])))
                    # Check that provisioned host is not in the list of
                    # discovered hosts anymore
                    self.assertIsNotNone(
                        self.discoveredhosts.search(
                            hostname, expecting_results=False))

    @run_only_on('sat')
    @tier3
    def test_positive_add_fact_column(self):
        """Add a new fact column to display on discovered host page

        :id: 914bd47f-b2a6-459e-b166-70dbc9ce1bc6

        :Steps:
            1. Goto settings -> Discovered tab -> discovery_fact_coloumn
            2. Edit discovery_fact_coloumn
            3. Add bios_vendor

        :expectedresults: The added fact should be displayed on
            'discovered_host' page after successful discovery


        :CaseLevel: System
        """
        param_value = 'bios_vendor'
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            # To show new fact column 'Interfaces' on Discovered Hosts page
            self._edit_discovery_fact_column_param(session, param_value)
            with LibvirtGuest() as pxe_host:
                hostname = pxe_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(hostname)
                )
                element = locators['discoveredhosts.fetch_bios']
                host_bios = self.discoveredhosts.fetch_fact_value(
                    hostname, element)
                self.assertEqual(u'Seabios', host_bios)

    @run_only_on('sat')
    @tier3
    def test_negative_add_fact(self):
        """Add a new fact column with invalid fact to display on
        discovered host page

        :id: 4e9bc843-4ba2-40d4-a1b3-2d7be117664f

        :Steps:

            1. Goto settings -> Discovered tab -> discovery_fact_coloumn
            2. Edit discovery_fact_coloumn
            3. Add 'test'

        :expectedresults: The added fact should be displayed on
            'discovered_host' page after successful discovery and shows 'N/A'

        :CaseLevel: System
        """
        param_value = 'test'
        expected_value = u'N/A'
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            # To show new fact column 'Interfaces' on Discovered Hosts page
            self._edit_discovery_fact_column_param(session, param_value)
            with LibvirtGuest() as pxe_host:
                hostname = pxe_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(hostname)
                )
                element = (
                    locators['discoveredhosts.fetch_fact'] % expected_value
                )
                fact_value = self.discoveredhosts.fetch_fact_value(
                    hostname, element)
                self.assertEqual(expected_value, fact_value)

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_discovery_manager_role(self):
        """Assign 'Discovery_Manager' role to a normal user

        :id: c219c877-e785-41a3-9abe-803a9b26bcad

        :expectedresults: User should be able to view, provision, edit and
            destroy one or more discovered host as well view, create_new, edit,
            execute and delete discovery rules.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_discovery_reader_role(self):
        """Assign 'Discovery Reader" role to a normal user

        :id: 075bd559-a3bb-42ca-86a4-60581c650a1d

        :expectedresults: User should be able to view existing discovered host
            and rule

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_validate_pxe_less_discovery_status_screen(self):
        """Validate all the buttons from "Discovery Status" TUI screen of a
        pxe-less discovered host

        :id: a18694ad-7642-472f-8e7c-c911c892a763

        :expectedresults: All buttons should work

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_validate_network_config_screen(self):
        """Validate network configuration screen by specifying invalid
        IP/gateway/DNS address notation.

        :id: b1d24367-9a7e-4d8e-85b6-989d8c520498

        :expectedresults: User should get an error message

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_pxe_less_discovery_without_dhcp(self):
        """Discover a host via pxe-less and select "Discover using DHCP"
        interactively when no dhcp is available.

        :id: adef940c-8948-4cd9-88b3-f0b307134536

        :expectedresults: User should get an error message "Unable to bring
            network via DHCP" and click on 'OK' should open the ''Network
            configuration screen" to manually specify the IP/GW/DNS.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_with_org_loc_from_new_model_window(self):
        """Provision a discovered host manually by associating org & loc from
        host properties model window and select create host button.

        :id: 8c6a7d3f-e34e-4888-9b1c-58e71ee584a3

        :expectedresults: Provisioned host is associated with selected org &
            location

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @tier3
    def test_positive_provision_with_hostgroup_from_new_model_window(self):
        """Provision a discovered host manually by associating hostgroup from
        host properties model window and select create host button.

        :id: f17fb8c9-f9cb-4547-80bc-3b40c6691bb1

        :expectedresults: Provisioned host is created with selected host-group
            and entry from discovered host should be auto removed.

        :CaseLevel: System
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            with LibvirtGuest() as pxe_host:
                host_name = pxe_host.guest_name
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(host_name)
                )
                self.discoveredhosts.provision_discoveredhost(
                    hostname=host_name,
                    hostgroup=self.config_env['host_group'],
                    org=self.org_name,
                    loc=self.loc.name)
                self.assertIsNotNone(self.hosts.search(
                    u'{0}.{1}'.format(host_name, self.config_env['domain'])))
                # Check that provisioned host is not in the list of discovered
                # hosts anymore
                self.assertIsNone(self.discoveredhosts.search(host_name))

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_with_facts_set_by_user(self):
        """Provision a discovered host with clear_all_facts setting's default
        value 'No'

        :id: 5dbb9a9f-117d-41aa-8f15-d4da6163b244

        :Setup:

            1. Host should already be discovered
            2. Go to setting -> clear_all_facts -> No

        :expectedresults: After successful provisioning, all facts set by user
            should be visible, including the one started with discovery
            keyword.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_provision_with_clear_facts_set_by_user(self):
        """Provision a discovered host by setting clear_all_facts
        value to 'Yes'

        :id: 9f153b3a-4c21-41a2-b2a0-a0b1bee262d3

        :Setup:
            1. Host should already be discovered
            2. Go to setting -> clear_all_facts -> Yes

        :expectedresults: After successful provisioning, all facts set by user
            should be deleted execpt the one started with discovery keyword.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_lock_discovered_host_into_discovery(self):
        """Lock host into discovery via PXE configuration

        :id: 4ba9f923-0b8f-40ee-8bcb-90ff496587c4

        :Steps:

            1. Go to setting -> discovery_lock -> true
            2. Go to setting -> discovery_lock_template -> template to be
                locked with

        :expectedresults: Host should boot into discovery mode and should be
            discovered.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_populate_puppet_params_using_hostgroup(self):
        """On provisioning a host associate hostgroup and see if PuppetCA
        and Puppetmaster are being populated.

        :id: 21e55ffa-02bc-4f96-b463-887da30fb1c4

        :Steps:

            1. Discover a host
            2. Create a hostgroup with puppetCA and puppetmaster

        :expectedresults: Parameters like PuppetCA/Puppetmaster should be
            populated on associating hostgroup to discovered host

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_default_org_from_settings(self):
        """Update the default 'Discovery Organization' settings to place the
        discovered hosts in.

        :id: 596a98ad-90f6-42ff-b8ef-47f02dc5d595

        :Steps:

            1. Go to setting -> Discovered -> Discovery organization
            2. Update default org from dropdown

        :expectedresults: Discovered host should automatically be placed in
            selected default org

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_default_location_from_settings(self):
        """Update the default 'Discovery Location' settings to place the
        discovered hosts in.

        :id: 4bba9899-a53e-4521-b212-aee893f7a726

        :Steps:

            1. Go to setting -> Discovered -> Discovery Location
            2. Update default location from dropdown

        :expectedresults: Discovered host should automatically be placed in
            selected default location

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_check_network_facts(self):
        """Check if network facts ending with _eth0 are correctly displayed
        under discovered host page

        :id: 5a06236c-05dc-4a98-b1b5-9586c95203f9

        :expectedresults: Network facts like below should be displayed on
            discovered host page:

            1. facts ending with _eth0
            2. auto_negotiation_XXX
            3. LLDAP facts like lldp_neighbor_portid_XXX

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_rebuild_dns_on_provisioning(self):
        """Force DNS rebuild when provisioning discovered host

        :id: 87aa3279-7c29-40e8-a4d2-0aab43f0972f

        :Setup: Make sure 'discovery_always_rebuild_dns' setting set to true

        :expectedresults: DNS record should be recreated on provisioning
            discovered host

        :CaseAutomation: notautomated

        :CaseLevel: System
        """


class DiscoveryPrefixTestCase(UITestCase):
    """Test around updating Discovery Prefix"""

    @classmethod
    def setUpClass(cls):
        """Update discovery prefix with some string than default 'mac'"""
        super(DiscoveryPrefixTestCase, cls).setUpClass()
        cls.org = entities.Organization(name=gen_string('alpha')).create()
        cls.org_name = cls.org.name
        # Update hostname_prefix with some string other than default 'mac'
        cls.prefix = 'dhost'
        cls.discovery_prefix = entities.Setting().search(
            query={'search': 'name="discovery_prefix"'})[0]
        cls.default_prefix = str(cls.discovery_prefix.value)
        cls.discovery_prefix.value = cls.prefix
        cls.discovery_prefix.update(['value'])
        cls.discovery_org = entities.Setting().search(
            query={'search': 'name="discovery_organization"'})[0]
        cls.discovery_org.value = cls.org.name
        cls.discovery_org.update(['value'])

    @classmethod
    def tearDownClass(cls):
        """Restore default 'hostname_prefix' global setting's value"""
        cls.discovery_prefix.value = cls.default_prefix
        cls.discovery_prefix.update(['value'])

        super(DiscoveryPrefixTestCase, cls).tearDownClass()

    @run_only_on('sat')
    @tier3
    def test_positive_update_discovery_prefix(self):
        """Update the discovery_prefix parameter other than mac

        :id: 08f1d852-e9a0-430e-b73a-e2a7a144ac10

        :Steps:

            1. Goto settings -> Discovered tab -> discovery_prefix
            2. Edit discovery_prefix using any text that must start with a
               letter

        :Setup: Host should already be discovered

        :expectedresults: Host should be discovered with updated prefix.

        :CaseLevel: System
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.org_name)
            with LibvirtGuest() as pxe_host:
                host_mac = pxe_host.mac
                host_name = '{0}{1}'.format(
                    self.prefix, host_mac.replace(':', "")
                )
                self.assertTrue(
                    self.discoveredhosts.waitfordiscoveredhost(host_name)
                )
                self.assertIsNotNone(self.discoveredhosts.search(host_name))

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_hostname_settings(self):
        """Update the hostname_prefix and Hostname_facts settings
        and discover a host

        :id: e53fa8a9-baf9-4019-83f3-64949461b892

        :Steps:

            1. Goto settings -> Discovered tab -> Hostname_prefix
            2. Edit hostname_prefix using any text that must start with a
               letter e.g. 'discover'
            3. Goto settings ->Discovered tab -> Hostname_facts
            4. Edit hostname_facts using 'discovery_bootif'

        :expectedresults: Host should be discovered with name as
            'Hostname_prefix + hostname_facts'.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_hostname_with_empty_prefix(self):
        """Update the hostname_prefix to empty and Hostname_facts settings
        with 'UUID'

        :id: 537a616f-3b29-4fae-98a2-e27114bea14a

        :Steps:

            1. Goto settings -> Discovered tab -> Hostname_prefix
            2. Set empty hostname_prefix
            3. Goto settings ->Discovered tab -> Hostname_facts
            4. Edit hostname_facts using 'UUID'

        :expectedresults: Host should be discovered with UUID in name

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_hostname_with_facts_list(self):
        """Update the Hostname_facts settings with list of hostname_facts

        :id: e0d2791d-d106-491a-a8fd-bf42c8f411d4

        :Steps:

            1. Goto settings ->Discovered tab -> Hostname_facts
            2. Edit hostname_facts using 'bios_vendor', uuid'

        :expectedresults: Host should be discovered with first available fact
            bios_vendor

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_update_hostname_with_unknown_fact(self):
        """Update the Hostname_facts settings with list of hostname_facts
        where the first available fact doesn't exist

        :id: a7f64c8a-42dc-459d-8de0-f4d6b878c731

        :Steps:

            1. Goto settings ->Discovered tab -> Hostname_facts
            2. Edit hostname_facts using 'bios', uuid'

        :expectedresults: Host should be discovered with second fact uuid as
            bios fact doesn't exist

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_negative_discover_host_with_existing_hostname(self):
        """Discover a host with similar to hostname which already exists

        :id: ea9a9a11-a02a-408e-86fe-ab5d0b0a94fe

        :Steps:

            1. Goto settings -> Discovered tab -> Hostname_prefix
            2. Set empty hostname_prefix (without any value)
            3. Goto settings ->Discovered tab -> Hostname_facts
            4. update hostname_facts with 'bios_vendor'
            5. Discover two host

        :expectedresults: Error should be raised on discovering second host
            like: Name has already been taken

        :CaseAutomation: notautomated

        :CaseLevel: System
        """
