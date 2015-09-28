# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery"""
from fauxfactory import gen_string, gen_mac
from nailgun import entities
from robottelo.config import conf
from robottelo.decorators import stubbed
from robottelo import ssh
from robottelo.test import UITestCase
from robottelo.ui.session import Session
from time import sleep


class Discovery(UITestCase):
    """Implements Foreman discovery tests in UI."""

    name = gen_string("alpha")
    image_path = '/var/lib/libvirt/images/{0}.img'.format(name)

    def _pxe_boot_host(self, mac):
        """PXE boot a unknown host"""
        libvirt_server = 'qemu+tcp://{0}:16509/system'.format(
            conf.properties['main.server.hostname'])
        ssh.command('virt-install --hvm --network=bridge:virbr1, --mac={0} '
                    '--pxe --name {1} --ram=1024 --vcpus=1 --os-type=linux '
                    '--os-variant=rhel7 --disk path={2},size=10 --connect {3} '
                    '--noautoconsole'
                    .format(mac, self.name, self.image_path, libvirt_server))
        sleep(30)

    @classmethod
    def setUpClass(cls):
        """Steps to Configure foreman discovery

        1. Build PXE default template
        2. Create Organization/Location
        3. Update Global parameters to set default org and location for
        discovered hosts.
        4. Enable auto_provision flag to perform discovery via discovery rules.

        """
        # Build PXE default template to get default PXE file
        entities.ConfigTemplate().build_pxe_default()

        # Create Org and location
        cls.org = entities.Organization(name=gen_string("alpha")).create()
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

        super(Discovery, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """Restore default 'discovery_auto' global setting's value"""
        cls.discovery_auto.value = cls.default_discovery_auto
        cls.discovery_auto.update({'value'})

        super(Discovery, cls).tearDownClass()

    def tearDown(self):
        """Delete the pxe host to free the resources"""
        ssh.command('virsh destroy {0}'.format(self.name))
        ssh.command('virsh undefine {0}'.format(self.name))
        ssh.command('virsh vol-delete --pool default {0}'
                    .format(self.image_path))
        super(Discovery, self).tearDown()

    def test_host_discovery(self):
        """@Test: Discover a host via proxy by setting "proxy.type=proxy" in
        PXE default

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured

        @Steps: PXE boot a host/VM

        @Assert: Host should be successfully discovered

        """
        mac = gen_mac(multicast=True, locally=True)
        hostname = 'mac{0}'.format(mac.replace(':', ""))
        self._pxe_boot_host(mac)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            self.assertIsNotNone(self.discoveredhosts.search(hostname))

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

    def test_delete_discovered_host_1(self):
        """@Test: Delete the selected discovered host

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Selected host should be removed successfully

        """
        mac = gen_mac(multicast=True, locally=True)
        hostname = 'mac{0}'.format(mac.replace(':', ""))
        self._pxe_boot_host(mac)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            self.discoveredhosts.delete(hostname)

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
