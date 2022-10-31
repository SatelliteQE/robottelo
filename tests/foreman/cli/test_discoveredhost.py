"""Test class for CLI Foreman Discovery

:Requirement: Discoveredhost

:CaseAutomation: Automated

:CaseComponent: DiscoveryImage

:Assignee: gsulliva

:TestType: Functional

:CaseLevel: System

:Upstream: No
"""
from time import sleep

import pytest

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.discoveredhost import DiscoveredHost
from robottelo.cli.factory import configure_env_for_provision
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.host import Host
from robottelo.cli.settings import Settings
from robottelo.cli.template import Template
from robottelo.libvirt_discovery import LibvirtGuest
from robottelo.utils.datafactory import gen_string

pytestmark = [pytest.mark.run_in_one_thread]


def _assertdiscoveredhost(hostname):
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


@pytest.mark.skip_if_not_set('vlan_networking')
@pytest.fixture(scope='class')
def foreman_discovery(target_sat):
    """Steps to Configure foreman discovery

    1. Build PXE default template
    2. Create Organization/Location
    3. Update Global parameters to set default org and location for
        discovered hosts.
    4. Enable auto_provision flag to perform discovery via discovery
        rules.
    """
    # Build PXE default template to get default PXE file
    Template.build_pxe_default()
    # let's just modify the timeouts to speed things up
    target_sat.execute(
        "sed -ie 's/TIMEOUT [[:digit:]]\\+/TIMEOUT 1/g' /var/lib/tftpboot/pxelinux.cfg/default"
    )
    target_sat.execute(
        "sed -ie '/APPEND initrd/s/$/ fdi.countdown=1/' /var/lib/tftpboot/pxelinux.cfg/default"
    )

    # Create Org and location
    org = make_org()
    loc = make_location()

    # Get default settings values
    default_discovery_loc = Settings.list({'search': 'name=discovery_location'})[0]
    default_discovery_org = Settings.list({'search': 'name=discovery_organization'})[0]
    default_discovery_auto = Settings.list({'search': 'name=discovery_auto'})[0]

    # Update default org and location params to place discovered host
    Settings.set({'name': 'discovery_location', 'value': loc['name']})
    Settings.set({'name': 'discovery_organization', 'value': org['name']})

    # Enable flag to auto provision discovered hosts via discovery rules
    Settings.set({'name': 'discovery_auto', 'value': 'true'})

    # Flag which shows whether environment is fully configured for
    # discovered host provisioning.
    configured_env = configure_env_for_provision(org=org, loc=loc)
    yield {
        'default_discovery_auto': default_discovery_auto,
        'default_discovery_loc': default_discovery_loc,
        'default_discovery_org': default_discovery_org,
        'configured_env': configured_env,
    }
    # Restore default global setting's values
    Settings.set({'name': 'discovery_location', 'value': default_discovery_loc['value']})
    Settings.set({'name': 'discovery_organization', 'value': default_discovery_org['value']})
    Settings.set({'name': 'discovery_auto', 'value': default_discovery_auto['value']})


@pytest.mark.libvirt_discovery
@pytest.mark.tier3
def test_positive_pxe_based_discovery():
    """Discover a host via PXE boot by setting "proxy.type=proxy" in
    PXE default

    :id: 25e935fe-18f4-477e-b791-7ea5a395b4f6

    :Setup: Provisioning should be configured

    :Steps: PXE boot a host/VM

    :expectedresults: Host should be successfully discovered

    :CaseImportance: Critical

    :BZ: 1731112
    """
    with LibvirtGuest() as pxe_host:
        hostname = pxe_host.guest_name
        host = _assertdiscoveredhost(hostname)
        assert host is not None


@pytest.mark.tier3
@pytest.mark.libvirt_discovery
@pytest.mark.upgrade
def test_positive_provision_pxeless_bios_syslinux(foreman_discovery):
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

    :BZ: 1731112
    """
    with LibvirtGuest(boot_iso=True) as pxe_host:
        hostname = pxe_host.guest_name
        # fixme: assertion #1
        discovered_host = _assertdiscoveredhost(hostname)
        assert discovered_host is not None
        # Provision just discovered host
        DiscoveredHost.provision(
            {
                'name': discovered_host['name'],
                'hostgroup': foreman_discovery['configured_env']['hostgroup']['name'],
                'root-password': gen_string('alphanumeric'),
            }
        )
        # fixme: assertion #2-5
        provisioned_host = Host.info(
            {
                'name': '{}.{}'.format(
                    discovered_host['name'],
                    foreman_discovery['configured_env']['domain']['name'],
                )
            }
        )
        assert (
            provisioned_host['network']['subnet-ipv4']
            == foreman_discovery['configured_env']['subnet']['name']
        )
        assert (
            provisioned_host['operating-system']['partition-table']
            == foreman_discovery['configured_env']['ptable']['name']
        )
        assert (
            provisioned_host['operating-system']['operating-system']
            == foreman_discovery['configured_env']['os']['title']
        )
        # Check that provisioned host is not in the list of discovered
        # hosts anymore
        with pytest.raises(CLIReturnCodeError):
            DiscoveredHost.info({'id': discovered_host['id']})


@pytest.mark.tier3
@pytest.mark.libvirt_discovery
@pytest.mark.upgrade
def test_positive_provision_pxe_host_with_bios_syslinux(foreman_discovery):
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

    :BZ: 1731112
    """
    # fixme: assertion #1
    with LibvirtGuest() as pxe_host:
        hostname = pxe_host.guest_name
        # fixme: assertion #2-3
        # assertion #4
        discovered_host = _assertdiscoveredhost(hostname)
        assert discovered_host is not None
        # Provision just discovered host
        DiscoveredHost.provision(
            {
                'name': discovered_host['name'],
                'hostgroup': foreman_discovery['configured_env']['hostgroup']['name'],
                'root-password': gen_string('alphanumeric'),
            }
        )
        # fixme: assertion #5-8
        provisioned_host = Host.info(
            {
                'name': '{}.{}'.format(
                    discovered_host['name'],
                    foreman_discovery['configured_env']['domain']['name'],
                )
            }
        )
        # assertion #8
        assert (
            provisioned_host['network']['subnet-ipv4']
            == foreman_discovery['configured_env']['subnet']['name']
        )
        assert (
            provisioned_host['operating-system']['partition-table']
            == foreman_discovery['configured_env']['ptable']['name']
        )
        assert (
            provisioned_host['operating-system']['operating-system']
            == foreman_discovery['configured_env']['os']['title']
        )
        # assertion #9
        with pytest.raises(CLIReturnCodeError):
            DiscoveredHost.info({'id': discovered_host['id']})


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_provision_pxe_host_with_uefi_grub2():
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

    :CaseAutomation: NotAutomated

    :CaseImportance: High
    """


@pytest.mark.tier3
@pytest.mark.libvirt_discovery
def test_positive_delete():
    """Delete the selected discovered host

    :id: c4103de8-145c-4a7d-b837-a1dec97231a2

    :Setup: Host should already be discovered

    :expectedresults: Selected host should be removed successfully

    :CaseImportance: High
    """
    with LibvirtGuest() as pxe_host:
        hostname = pxe_host.guest_name
        host = _assertdiscoveredhost(hostname)
        assert host is not None
    DiscoveredHost.delete({'id': host['id']})
    with pytest.raises(CLIReturnCodeError):
        DiscoveredHost.info({'id': host['id']})


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_refresh_facts_pxe_host():
    """Refresh the facts of pxe based discovered hosts by adding a new NIC

    :id: 410eaa5d-cc6a-44f7-8c6f-e8cfa81610f0

    :Setup: Host should already be discovered

    :expectedresults: Facts should be refreshed successfully with a new NIC

    :CaseAutomation: NotAutomated

    :CaseImportance: Medium
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_refresh_facts_of_pxeless_host():
    """Refresh the facts of pxeless discovered hosts by adding a new NIC

    :id: 2e199eaa-9651-47b1-a2fd-622778dfe68e

    :Setup: Host should already be discovered

    :expectedresults: Facts should be refreshed successfully with a new NIC

    :CaseAutomation: NotAutomated

    :CaseImportance: Medium
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_reboot_pxe_host():
    """Reboot pxe based discovered hosts

    :id: 9cc17742-f810-4be7-b410-a6c68e6cc64a

    :Setup: Host should already be discovered

    :expectedresults: Host is rebooted

    :CaseAutomation: NotAutomated

    :CaseImportance: High
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_reboot_pxeless_host():
    """Reboot pxe-less discovered hosts

    :id: e72e1607-8778-45b6-b8b9-8215514546f0

    :Setup: PXELess host should already be discovered

    :expectedresults: Host is rebooted

    :CaseAutomation: NotAutomated

    :CaseImportance: High
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_auto_provision_pxe_host():
    """Discover a pxe based host and auto-provision it with
    discovery rule and by enabling auto-provision flag

    :id: 701a1892-1c6a-4ba1-bbd8-a37b7fb02fa0

    :expectedresults: Host should be successfully rebooted and provisioned

    :CaseAutomation: NotAutomated

    :CaseImportance: Critical
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_auto_provision_pxeless_host():
    """Discover a pxe-less host and auto-provision it with
    discovery rule and by enabling auto-provision flag

    :id: 298417b3-d242-4999-89f9-198095704c0e

    :expectedresults: Host should be successfully rebooted and provisioned

    :CaseAutomation: NotAutomated

    :CaseImportance: Critical
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_assign_discovery_manager_role():
    """Assign 'Discovery_Manager' role to a normal user

    :id: f694c361-5fbb-4c3a-b2ff-6dfe6ea14820

    :expectedresults: User should be able to view, provision, edit and destroy one or more
        discovered host as well as view, create_new, edit, execute and delete discovery rules

    :CaseAutomation: NotAutomated

    :CaseImportance: Medium
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_assign_discovery_role():
    """Assign 'Discovery" role to a normal user

    :id: 873e8411-563d-4bf9-84ce-62e522410cfe

    :expectedresults: User should be able to list, provision, and destroy
        one or more discovered hosts

    :CaseAutomation: NotAutomated

    :CaseImportance: Medium
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_update_discover_hostname_settings():
    """Update the hostname_prefix and Hostname_facts settings and
    discover a host.

    :id: 10071eb1-ec2a-4061-b798-480643d8f4ed

    :expectedresults: Host should be discovered with name as 'hostname_prefix + hostname_facts'

    :CaseAutomation: NotAutomated

    :CaseImportance: Medium
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_list_facts():
    """Check if defined facts of a discovered host are
    correctly displayed under host's facts

    :id: 2c65925c-05d9-4f6d-b1b7-1fa1492c95a8

    :Setup: 1. Provisioning is configured and Host is already discovered

    :Steps: Validate specified builtin and custom facts

    :expectedresults: All checked facts should be displayed correctly

    :CaseAutomation: NotAutomated

    :CaseImportance: High
    """
