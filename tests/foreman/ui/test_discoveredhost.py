# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery"""
from fauxfactory import gen_string, gen_mac
from nailgun import entities
from robottelo.config import settings
from robottelo.decorators import skip_if_not_set, stubbed, tier3
from robottelo import ssh
from robottelo.test import UITestCase
from robottelo.ui.session import Session
from time import sleep


class DiscoveryTestCase(UITestCase):
    """Implements Foreman discovery tests in UI."""

    name = gen_string('alpha')

    def _pxe_boot_host(self, mac):
        """PXE boot a unknown host"""
        ssh.command(
            u'virt-install --hvm --network=bridge:{0}, --mac={1} '
            '--pxe --name {2} --ram=1024 --vcpus=1 --os-type=linux '
            '--os-variant=rhel7 --disk path={3},size=10 --noautoconsole'
            .format(settings.vlan_networking.bridge, mac, self.name,
                    self.image_path),
            hostname=self.libvirt_host
        )

    def assertdiscoveredhost(self, hostname):
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

        cls.image_path = u'{0}/{1}.img'.format(
            settings.compute_resources.libvirt_image_dir, cls.name)
        cls.libvirt_host = settings.compute_resources.libvirt_hostname
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

    def tearDown(self):
        """Delete the pxe host to free the resources"""
        ssh.command(
            'virsh destroy {0}'.format(self.name),
            hostname=self.libvirt_host
        )
        ssh.command(
            'virsh undefine {0}'.format(self.name),
            hostname=self.libvirt_host
        )
        ssh.command(
            'virsh vol-delete --pool default {0}'
            .format(self.image_path),
            hostname=self.libvirt_host
        )
        super(DiscoveryTestCase, self).tearDown()

    @tier3
    def test_positive_discovery(self):
        """@Test: Discover a host via proxy by setting "proxy.type=proxy" in
        PXE default

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured

        @Steps: PXE boot a host/VM

        @Assert: Host should be successfully discovered

        """
        mac = gen_mac(multicast=False, locally=True)
        hostname = 'mac{0}'.format(mac.replace(':', ""))
        self._pxe_boot_host(mac)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            self.assertdiscoveredhost(hostname)
            self.assertIsNotNone(self.discoveredhosts.search(hostname))

    @stubbed()
    @tier3
    def test_positive_discovery_facts(self):
        """@Test: Check all facts of discovered hosts are correctly displayed

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured

        @Steps: Validate IP, memory, mac etc of discovered host

        @Assert: All facts should be displayed correctly

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_provision(self):
        """@Test: Provision the selected discovered host by selecting
        'provision' button

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should be provisioned successfully and entry from
        discovered host should be auto removed

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_provision_from_facts(self):
        """@Test: Provision the selected discovered host from facts page by
        clicking 'provision'

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should be provisioned successfully and entry from
        discovered host should be auto removed

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_delete(self):
        """@Test: Delete the selected discovered host

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        """
        mac = gen_mac(multicast=False, locally=True)
        hostname = 'mac{0}'.format(mac.replace(':', ""))
        self._pxe_boot_host(mac)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            self.assertdiscoveredhost(hostname)
            self.discoveredhosts.delete(hostname)

    @stubbed()
    @tier3
    def test_positive_delete_from_facts(self):
        """@Test: Delete the selected discovered host from facts page

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_delete_multiple(self):
        """@Test: Delete multiple discovered hosts from 'Select Action'
        drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_refresh_facts(self):
        """@Test: Refresh the facts of discovered hosts

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Facts should be refreshed successfully
        ToDo: Need to check what we change on host that its updated with
        refresh facts

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_update_default_org(self):
        """@Test: Change the default org of more than one discovered hosts
        from 'Select Action' drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Default org should be successfully changed for multiple hosts

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_update_default_location(self):
        """@Test: Change the default location of more than one discovered hosts
        from 'Select Action' drop down

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Default Location should be successfully changed for multiple
        hosts

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_create_discovery_rule_with_IP(self):
        """@Test: Create a new discovery rule

        Set query as (e.g IP=IP_of_discovered_host)

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should reboot and provision

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_create_discovery_rule_with_cpu_count(self):
        """@Test: Create a new discovery rule with (host_limit = 0)
        that applies to multi hosts.
        Set query as cpu_count = 1 OR mem > 500

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: All Hosts of same subnet should reboot and provision

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_create_discovery_rule_with_priorities(self):
        """@Test: Create multiple discovery rules with different priority

        @Feature: Foreman Discovery

        @Setup: Multiple hosts should already be discovered

        @Assert: Host with lower count have higher priority
        and that rule should be executed first

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_create_discovery_rule_without_auto_provision(self):
        """@Test: Create a discovery rule and execute it when
        "auto_provisioning" flag set to 'false'

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should not be rebooted automatically

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_negative_create_discovery_rule(self):
        """@Test: Create a discovery rule with invalid query
        e.g. BIOS = xyz

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Rule should automatically be skipped on clicking
        'Auto provision'. UI Should raise 'No matching rule found'

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_apply_discovery_rule_multiple(self):
        """@Test: Create a discovery rule (CPU_COUNT = 2) with host limit 1 and
        provision more than one host with same rule

        @Feature: Foreman Discovery

        @Setup: Host with two CPUs should already be discovered

        @Assert: Rule should only be applied to one discovered host and for
        other rule should already be skipped.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_update_discovery_rule(self):
        """@Test: Update an existing rule and execute it

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: User should be able to update the rule and it should be
        executed on discovered host

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_update_name(self):
        """@Test: Update the discovered host name and provision it

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: The hostname should be updated and host should be provisioned

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_update_discovery_prefix(self):
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
    @tier3
    def test_positive_auto_provision_all(self):
        """@Test: Discover a bunch of hosts and auto-provision all

        @Feature: Foreman Discovery

        @Assert: All host should be successfully rebooted and provisioned

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_add_fact_column(self):
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
    @tier3
    def test_negative_add_fact(self):
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
    @tier3
    def test_positive_discovery_manager_role(self):
        """@Test: Assign 'Discovery_Manager' role to a normal user

        @Feature: Foreman Discovery

        @Assert: User should be able to view, provision, edit and destroy one
        or more discovered host as well view, create_new, edit, execute and
        delete discovery rules.

        @Status: Manual

        """

    @stubbed()
    @tier3
    def test_positive_discovery_role(self):
        """@Test: Assign 'Discovery" role to a normal user

        @Feature: Foreman Discovery

        @Assert: User should be able to view, provision, edit and destroy one
        or more discovered host

        @Status: Manual

        """
