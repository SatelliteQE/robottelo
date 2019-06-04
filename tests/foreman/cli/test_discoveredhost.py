# -*- encoding: utf-8 -*-
"""Test class for CLI Foreman Discovery

:Requirement: Discoveredhost

:CaseAutomation: Automated

:CaseComponent: DiscoveryPlugin

:TestType: Functional

:CaseLevel: System

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
    skip_if_not_set,
    stubbed,
    tier3,
    upgrade
)
from robozilla.decorators import bz_bug_is_open
from robottelo.libvirt_discovery import LibvirtGuest
from robottelo import ssh
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
        # let's just modify the timeouts to speed things up
        ssh.command("sed -ie 's/TIMEOUT [[:digit:]]\\+/TIMEOUT 1/g' "
                    "/var/lib/tftpboot/pxelinux.cfg/default")
        ssh.command("sed -ie '/APPEND initrd/s/$/ fdi.countdown=1/' "
                    "/var/lib/tftpboot/pxelinux.cfg/default")

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

        if bz_bug_is_open(1578290):
            ssh.command('mkdir /var/lib/tftpboot/boot/fdi-image')
            ssh.command('ln -s /var/lib/tftpboot/boot/'
                        'foreman-discovery-image-3.4.4-1.iso-vmlinuz'
                        ' /var/lib/tftpboot/boot/fdi-image/vmlinuz0')
            ssh.command('ln -s /var/lib/tftpboot/boot/'
                        'foreman-discovery-image-3.4.4-1.iso-img'
                        ' /var/lib/tftpboot/boot/fdi-image/initrd0.img')
            ssh.command('chown -R foreman-proxy /var/lib/tftpboot/boot/')

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

    @tier3
    def test_positive_pxe_based_discovery(self):
        """Discover a host via PXE boot by setting "proxy.type=proxy" in
        PXE default

        :id: 25e935fe-18f4-477e-b791-7ea5a395b4f6

        :Setup: Provisioning should be configured

        :Steps: PXE boot a host/VM

        :expectedresults: Host should be successfully discovered

        :CaseImportance: Critical
        """
        with LibvirtGuest() as pxe_host:
            hostname = pxe_host.guest_name
            host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(host)

    @tier3
    def test_positive_pxe_less_with_dhcp_unattended(self):
        """Discover a host with dhcp via bootable discovery ISO by setting
        "proxy.type=proxy" in PXE default in unattended mode.

        :id: a23bd065-8385-4876-aa45-e38470be79b8

        :Setup: Provisioning should be configured

        :Steps: Boot a host/VM using modified discovery ISO.

        :expectedresults: Host should be successfully discovered

        :CaseImportance: Critical
        """
        with LibvirtGuest(boot_iso=True) as pxe_less_host:
            hostname = pxe_less_host.guest_name
            host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(host)

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

        :expectedresults: All defined custom facts should be displayed
            correctly

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

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

        :expectedresults: All defined custom facts should be displayed
            correctly

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @tier3
    @upgrade
    def test_positive_provision_pxeless_bios_syslinux(self):
        """Provision and discover the pxe-less BIOS host from cli using SYSLINUX
        loader

        :id: ae7f3ce2-e66e-44dc-85cb-0c3c4782cbb1

        :Setup:
            1. Craft the FDI with remaster the image to have ssh enabled

        :Steps:
            1. Create a BIOS VM and set it to boot from the FDI
            2. Run assertion steps #1-2
            3. Provision the discovered host using PXELinux loader
            4. Run assertion steps #3-7

        :expectedresults: Host should be provisioned successfully
            1. [TBD] Ensure FDI loaded and successfully sent out facts

               1.1 ping vm
               1.2 ssh to the VM and read the logs (if ssh enabled)
               1.3 optionally sniff the HTTP traffic coming from the host

            2. Ensure host appeared in Discovered Hosts on satellite
            3. [TBD] Ensure the kexec was successful (e.g. the kexec request
               result in production.log)
            4. [TBD] Ensure anaconda loaded and the installation finished
            5. [TBD] Ensure the host is provisioned with correct attributes
            6. Ensure the host is created in Hosts
            7. Ensure the entry from discovered host list disappeared

        :CaseImportance: High
        """
        if not self.configured_env:
            self.__class__.configured_env = configure_env_for_provision(
                org=self.org, loc=self.loc)
        with LibvirtGuest(boot_iso=True) as pxe_host:
            hostname = pxe_host.guest_name
            # fixme: assertion #1
            discovered_host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(discovered_host)
            # Provision just discovered host
            DiscoveredHost.provision({
                'name': discovered_host['name'],
                'hostgroup': self.configured_env['hostgroup']['name'],
                'root-password': gen_string('alphanumeric'),
            })
            # fixme: assertion #2-5
            provisioned_host = Host.info({
                'name': '{0}.{1}'.format(
                    discovered_host['name'],
                    self.configured_env['domain']['name']
                )
            })
            self.assertEqual(
                provisioned_host['network']['subnet-ipv4'],
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

    @stubbed()
    @tier3
    def test_positive_provision_pxeless_uefi_grub(self):
        """Provision and discover the pxe-less UEFI host from cli using GRUB
        loader

        :id: 0704ec80-dfaf-4f25-ad6b-a4cd3f33a1cb

        :Setup:
            1. Craft the FDI with remaster the image to have ssh enabled
            2. Synchronize RHEL6 repo (needed for GRUB)

        :Steps:
            1. Create a UEFI VM and set it to boot from the FDI
            2. Run assertion steps #1-2
            3. Provision the discovered host using UEFI_GRUB PXE loader
            4. Run assertion steps #3-7

        :expectedresults: Host should be provisioned successfully
            1. [TBD] Ensure FDI loaded and successfully sent out facts

                1.1 ping vm
                1.2 ssh to the VM and read the logs (if ssh enabled)
                1.3 optionally sniff the HTTP traffic coming from the host

            2. Ensure host appeared in Discovered Hosts on satellite
            3. [TBD] Ensure the kexec was successful (e.g. the kexec request
               result in production.log)
            4. [TBD] Ensure anaconda loaded and the installation finished
            5. [TBD] Ensure the host is provisioned with correct attributes
            6. Ensure the host is created in Hosts
            7. Ensure the entry from discovered host list disappeared

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @stubbed()
    @tier3
    def test_positive_provision_pxeless_uefi_grub2(self):
        """Provision and discover the pxe-less UEFI host from cli using GRUB2
        loader

        :id: 81b0b586-617c-4100-80e6-ce924fb26d88

        :Setup:
            1. Craft the FDI with remaster the image to have ssh enabled
            2. Synchronize RHEL7+ repo (needed for GRUB2)

        :Steps:
            1. Create a UEFI VM and set it to boot from the FDI
            2. Run assertion steps #1-2
            3. Provision the discovered host using GRUB2_UEFI PXE loader
            4. Run assertion steps #3-7

        :expectedresults: Host should be provisioned successfully
            1. Ensure FDI loaded and successfully sent out facts

                1.1 ping vm
                1.2 ssh to the VM and read the logs (if ssh enabled)
                1.3 optionally sniff the HTTP traffic coming from the host

            2. Ensure host appeared in Discovered Hosts on satellite
            3. Ensure the kexec was successful (e.g. the kexec request
               result in production.log)
            4. Ensure anaconda loaded and the installation finished
            5. Ensure the host is provisioned with correct attributes
            6. Ensure the host is created in Hosts
            7. Ensure the entry from discovered host list disappeared

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @stubbed()
    @tier3
    def test_positive_provision_pxeless_uefi_grub2_secureboot(self):
        """Provision and discover the pxe-less UEFI SB host from cli using GRUB2
        loader

        :id: b9896977-9f4a-4f3d-85d9-660f62e76448

        :Setup:
            1. Craft the FDI with remaster the image to have ssh enabled
            2. Synchronize RHEL7+ repo (needed for GRUB2)

        :Steps:
            1. Create a UEFI VM with secureboot and set it to boot from the FDI
            2. Run assertion steps #1-2
            3. Provision the discovered host using GRUB2_UEFI_SB PXE loader
            4. Run assertion steps #3-7

        :expectedresults: Host should be provisioned successfully
            1. Ensure FDI loaded and successfully sent out facts

                1.1 ping vm
                1.2 ssh to the VM and read the logs (if ssh enabled)
                1.3 optionally sniff the HTTP traffic coming from the host

            2. Ensure host appeared in Discovered Hosts on satellite
            3. Ensure the kexec was successful (e.g. the kexec request
               result in production.log)
            4. Ensure anaconda loaded and the installation finished
            5. Ensure the host is provisioned with correct attributes
            6. Ensure the host is created in Hosts
            7. Ensure the entry from discovered host list disappeared

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @tier3
    @upgrade
    def test_positive_provision_pxe_host_with_bios_syslinux(self):
        """Provision the pxe-based BIOS discovered host from cli using SYSLINUX
        loader

        :id: b5385fe3-d532-4373-af64-5492275ff8d4

        :Setup:
            1. Create a BIOS VM and set it to boot from a network
            2. for getting more detailed info from FDI, remaster the image to
               have ssh enabled

        :steps:
            1. Build a default PXE template
            2. Run assertion step #1
            3. Boot the VM (from NW)
            4. Run assertion steps #2-4
            5. Provision the discovered host
            6. Run assertion steps #5-9

        :expectedresults: Host should be provisioned successfully
            1. [TBD] Ensure the tftpboot files are updated

              1.1 Ensure fdi-image files have been placed under tftpboot/boot/
              1.2 Ensure the 'default' pxelinux config has been placed under
              tftpboot/pxelinux.cfg/
              1.3 Ensure the discovery section exists inside pxelinux config,
              it leads to the FDI kernel and the ONTIMEOUT is set to discovery

            2. [TBD] Ensure PXE handoff goes as expected (tcpdump -p tftp)
            3. [TBD] Ensure FDI loaded and successfully sent out facts

                3.1 ping vm
                3.2 ssh to the VM and read the logs (if ssh enabled)
                3.3 optionally sniff the HTTP traffic coming from the host

            4. Ensure host appeared in Discovered Hosts on satellite
            5. [TBD] Ensure the tftpboot files are updated for the hosts mac
            6. [TBD] Ensure PXE handoff goes as expected (tcpdump -p tftp)
            7. [TBD] Optionally ensure anaconda loaded and the installation
               finished
            8. [TBD] Ensure the host is provisioned with correct attributes
            9. Ensure the entry from discovered host list disappeared

        :CaseImportance: High
        """
        # fixme: assertion #1
        if not self.configured_env:
            self.__class__.configured_env = configure_env_for_provision(
                org=self.org, loc=self.loc)
        with LibvirtGuest() as pxe_host:
            hostname = pxe_host.guest_name
            # fixme: assertion #2-3
            # assertion #4
            discovered_host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(discovered_host)
            # Provision just discovered host
            DiscoveredHost.provision({
                'name': discovered_host['name'],
                'hostgroup': self.configured_env['hostgroup']['name'],
                'root-password': gen_string('alphanumeric'),
            })
            # fixme: assertion #5-8
            provisioned_host = Host.info({
                'name': '{0}.{1}'.format(
                    discovered_host['name'],
                    self.configured_env['domain']['name']
                )
            })
            # assertion #8
            self.assertEqual(
                provisioned_host['network']['subnet-ipv4'],
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
            # assertion #9
            with self.assertRaises(CLIReturnCodeError):
                DiscoveredHost.info({'id': discovered_host['id']})

    @stubbed()
    @tier3
    def test_positive_provision_pxe_host_with_uefi_grub(self):
        """Provision the pxe-based UEFI discovered host from cli using PXEGRUB
        loader

        :id: fc86e56e-9dc6-48ba-aaa7-8b6611b973c9

        :Setup:
            1. Create an UEFI VM and set it to boot from a network
            2. for getting more detailed info from FDI, remaster the image to
               have ssh enabled

        :steps:
            1. Build a default PXE template
            2. Run assertion step #1
            3. Boot the VM (from NW)
            4. Run assertion steps #2-4
            5. Provision the discovered host
            6. Run assertion steps #5-9

        :expectedresults: Host should be provisioned successfully
            1. Ensure the tftpboot files are updated

              1.1 Ensure fdi-image files have been placed under tftpboot/boot/
              1.2 Ensure the 'default' pxelinux config has been placed under
              tftpboot/pxelinux.cfg/
              1.3 Ensure the discovery section exists inside pxelinux config,
              it leads to the FDI kernel and the ONTIMEOUT is set to discovery

            2. Ensure PXE handoff goes as expected (tcpdump -p tftp)
            3. Ensure FDI loaded and successfully sent out facts

                3.1 ping vm
                3.2 ssh to the VM and read the logs (if ssh enabled)
                3.3 optionally sniff the HTTP traffic coming from the host

            4. Ensure host appeared in Discovered Hosts on satellite
            5. Ensure the tftpboot files are updated for the hosts mac
            6. Ensure PXE handoff goes as expected (tcpdump -p tftp)
            7. Optionally ensure anaconda loaded and the installation finished
            8. Ensure the host is provisioned with correct attributes
            9. Ensure the entry from discovered host list disappeared

        :CaseImportance: High

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier3
    def test_positive_provision_pxe_host_with_uefi_grub2(self):
        """Provision the pxe-based UEFI discovered host from cli using PXEGRUB2
        loader

        :id: 0002af1b-6f4b-40e2-8f2f-343387be6f72

        :Setup:
            1. Create an UEFI VM and set it to boot from a network
            2. Synchronize RHEL7 kickstart repo (rhel6 kernel too old for GRUB)
            3. for getting more detailed info from FDI, remaster the image to
               have ssh enabled

        :steps:
            1. Build a default PXE template
            2. Run assertion step #1
            3. Boot the VM (from NW)
            4. Run assertion steps #2-4
            5. Provision the discovered host
            6. Run assertion steps #5-9

        :expectedresults: Host should be provisioned successfully
            1. Ensure the tftpboot files are updated

              1.1 Ensure fdi-image files have been placed under tftpboot/boot/
              1.2 Ensure the 'default' pxelinux config has been placed under
              tftpboot/pxelinux.cfg/
              1.3 Ensure the discovery section exists inside pxelinux config,
              it leads to the FDI kernel and the ONTIMEOUT is set to discovery

            2. Ensure PXE handoff goes as expected (tcpdump -p tftp)
            3. Ensure FDI loaded and successfully sent out facts

                3.1 ping vm
                3.2 ssh to the VM and read the logs (if ssh enabled)
                3.3 optionally sniff the HTTP traffic coming from the host

            4. Ensure host appeared in Discovered Hosts on satellite
            5. Ensure the tftpboot files are updated for the hosts mac
            6. Ensure PXE handoff goes as expected (tcpdump -p tftp)
            7. Optionally ensure anaconda loaded and the installation finished
            8. Ensure the host is provisioned with correct attributes
            9. Ensure the entry from discovered host list disappeared

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @stubbed()
    @tier3
    def test_positive_provision_pxe_host_with_uefi_grub2_sb(self):
        """Provision the pxe-based UEFI Secureboot discovered host from cli
        using PXEGRUB2 loader

        :id: 285ebbac-934b-45ae-a0ca-0dc450836428

        :Setup:
            1. Create an UEFI SB VM and set it to boot from a network
            2. Synchronize RHEL6 kickstart repo (rhel7 kernel too new for GRUB)
            3. for getting more detailed info from FDI, remaster the image to
               have ssh enabled

        :steps:
            1. Build a default PXE template
            2. Run assertion step #1
            3. Boot the VM (from NW)
            4. Run assertion steps #2-4
            5. Provision the discovered host
            6. Run assertion steps #5-9

        :expectedresults: Host should be provisioned successfully
            1. Ensure the tftpboot files are updated

              1.1 Ensure fdi-image files have been placed under tftpboot/boot/
              1.2 Ensure the 'default' pxelinux config has been placed under
              tftpboot/pxelinux.cfg/
              1.3 Ensure the discovery section exists inside pxelinux config,
              it leads to the FDI kernel and the ONTIMEOUT is set to discovery

            2. Ensure PXE handoff goes as expected (tcpdump -p tftp)
            3. Ensure FDI loaded and successfully sent out facts

                3.1 ping vm
                3.2 ssh to the VM and read the logs (if ssh enabled)
                3.3 optionally sniff the HTTP traffic coming from the host

            4. Ensure host appeared in Discovered Hosts on satellite
            5. Ensure the tftpboot files are updated for the hosts mac
            6. Ensure PXE handoff goes as expected (tcpdump -p tftp)
            7. Optionally ensure anaconda loaded and the installation finished
            8. Ensure the host is provisioned with correct attributes
            9. Ensure the entry from discovered host list disappeared

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @tier3
    def test_positive_delete_pxeless_host(self):
        """Delete the selected pxe-less discovered host

        :id: 3959abd7-a1c0-418f-a75a-dec06b5ea0e2

        :Setup: Host should already be discovered

        :expectedresults: Selected host should be removed successfully

        :CaseImportance: High
        """
        with LibvirtGuest(boot_iso=True) as pxe_less_host:
            hostname = pxe_less_host.guest_name
            host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(host)
        DiscoveredHost.delete({'id': host['id']})
        with self.assertRaises(CLIReturnCodeError):
            DiscoveredHost.info({'id': host['id']})

    @tier3
    def test_positive_delete_pxe_host(self):
        """Delete the selected pxe-based discovered host

        :id: c4103de8-145c-4a7d-b837-a1dec97231a2

        :Setup: Host should already be discovered

        :expectedresults: Selected host should be removed successfully

        :CaseImportance: High
        """
        with LibvirtGuest() as pxe_host:
            hostname = pxe_host.guest_name
            host = self._assertdiscoveredhost(hostname)
            self.assertIsNotNone(host)
        DiscoveredHost.delete({'id': host['id']})
        with self.assertRaises(CLIReturnCodeError):
            DiscoveredHost.info({'id': host['id']})

    @stubbed()
    @tier3
    def test_positive_refresh_facts_pxe_host(self):
        """Refresh the facts of pxe based discovered hosts by adding a new NIC

        :id: 410eaa5d-cc6a-44f7-8c6f-e8cfa81610f0

        :Setup: Host should already be discovered

        :expectedresults: Facts should be refreshed successfully with a new NIC

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @stubbed()
    @tier3
    def test_positive_refresh_facts_of_pxeless_host(self):
        """Refresh the facts of pxeless discovered hosts by adding a new NIC

        :id: 2e199eaa-9651-47b1-a2fd-622778dfe68e

        :Setup: Host should already be discovered

        :expectedresults: Facts should be refreshed successfully with a new NIC

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @stubbed()
    @tier3
    def test_positive_reboot_pxe_host(self):
        """Reboot pxe based discovered hosts

        :id: 9cc17742-f810-4be7-b410-a6c68e6cc64a

        :Setup: Host should already be discovered

        :expectedresults: Host is rebooted

        :CaseAutomation: notautomated

        :CaseImportance: Medium
        """

    @stubbed()
    @tier3
    def test_positive_reboot_pxeless_host(self):
        """Reboot pxe-less discovered hosts

        :id: e72e1607-8778-45b6-b8b9-8215514546f0

        :Setup: PXELess host should already be discovered

        :expectedresults: Host is rebooted

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @stubbed()
    @tier3
    def test_positive_auto_provision_pxe_host(self):
        """Discover a pxe based host and auto-provision it with
        discovery rule and by enabling auto-provision flag

        :id: 701a1892-1c6a-4ba1-bbd8-a37b7fb02fa0

        :expectedresults: Host should be successfully rebooted and provisioned

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_auto_provision_pxeless_host(self):
        """Discover a pxe-less host and auto-provision it with
        discovery rule and by enabling auto-provision flag

        :id: 298417b3-d242-4999-89f9-198095704c0e

        :expectedresults: Host should be successfully rebooted and provisioned

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @stubbed()
    @tier3
    def test_positive_list_discovered_host(self):
        """List pxe-based and pxe-less discovered hosts

        :id: 3a827080-3fab-4f64-a830-1b41841aa2df

        :expectedresults: Host should be discovered and listed with names.

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @stubbed()
    @tier3
    def test_positive_assign_discovery_manager_role(self):
        """Assign 'Discovery_Manager' role to a normal user

        :id: f694c361-5fbb-4c3a-b2ff-6dfe6ea14820

        :expectedresults: User should be able to view, provision, edit and
            destroy one or more discovered host as well view, create_new, edit,
            execute and delete discovery rules.

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @stubbed()
    @tier3
    def test_positive_assign_discovery_role(self):
        """Assign 'Discovery" role to a normal user

        :id: 873e8411-563d-4bf9-84ce-62e522410cfe

        :expectedresults: User should be able to list, provision, and destroy
            one or more discovered host

        :CaseAutomation: notautomated

        :CaseImportance: High
        """

    @stubbed()
    @tier3
    def test_positive_update_discover_hostname_settings(self):
        """Update the hostname_prefix and Hostname_facts settings and
        discover a host.

        :id: 10071eb1-ec2a-4061-b798-480643d8f4ed

        :expectedresults: Host should be discovered with name as
            'Hostname_prefix + hostname_facts'.

        :CaseAutomation: notautomated

        :CaseImportance: High
        """
