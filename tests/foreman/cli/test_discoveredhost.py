"""Test class for CLI Foreman Discovery

:Requirement: Discoveredhost

:CaseAutomation: Automated

:CaseComponent: DiscoveryImage

:Team: Rocket

"""

import pytest
from wait_for import wait_for

pytestmark = [pytest.mark.run_in_one_thread]


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('module_provisioning_sat', ['discovery'], indirect=True)
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.rhel_ver_match('7')
def test_rhel_pxe_discovery_provisioning(
    module_provisioning_rhel_content,
    module_discovery_sat,
    provisioning_host,
    provisioning_hostgroup,
    request,
):
    """Provision a PXE-based discovered host

    :id: b32a3b05-86bc-4ba6-ab6c-22b2f81e4315

    :parametrized: yes

    :Setup: Satellite with Provisioning and Discovery features configured

    :steps:
        1. Boot up the host to discover
        2. Provision the host

    :expectedresults: Host should be successfully discovered and provisioned

    :CaseImportance: Critical

    :BZ: 1731112
    """
    sat = module_discovery_sat.sat
    provisioning_host.power_control(ensure=False)
    mac = provisioning_host._broker_args['provisioning_nic_mac_addr']

    wait_for(
        lambda: sat.api.DiscoveredHost().search(query={'mac': mac}) != [],
        timeout=1500,
        delay=40,
    )
    discovered_host = sat.api.DiscoveredHost().search(query={'mac': mac})[0]
    discovered_host.hostgroup = provisioning_hostgroup
    discovered_host.location = provisioning_hostgroup.location[0]
    discovered_host.organization = provisioning_hostgroup.organization[0]
    discovered_host.build = True
    result = sat.cli.DiscoveredHost.provision(
        {
            'id': discovered_host.id,
            'hostgroup-id': discovered_host.hostgroup.id,
            'organization-id': discovered_host.organization.id,
            'location-id': discovered_host.location.id,
        }
    )

    assert 'Host created' in result[0]['message']
    host = sat.api.Host().search(query={"search": f'id={discovered_host.id}'})[0]
    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))
    assert host

    wait_for(
        lambda: host.read().build_status_label != 'Pending installation',
        timeout=1500,
        delay=10,
    )
    assert host.read().build_status_label == 'Installed'
    assert not sat.api.DiscoveredHost().search(query={'mac': mac})


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('module_provisioning_sat', ['discovery'], indirect=True)
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.rhel_ver_match('7')
def test_rhel_pxeless_discovery_provisioning(
    module_discovery_sat,
    pxeless_discovery_host,
    module_provisioning_rhel_content,
    provisioning_hostgroup,
    request,
):
    """Provision a PXE-less discovered host

    :id: e75ee13a-9edc-4182-b02a-6b106a459751

    :Setup: Provisioning should be configured and a host should be
        discovered via cli

    :expectedresults: Host should be provisioned successfully

    :CaseImportance: Critical
    """
    sat = module_discovery_sat.sat
    pxeless_discovery_host.power_control(ensure=False)
    mac = pxeless_discovery_host._broker_args['provisioning_nic_mac_addr']

    wait_for(
        lambda: sat.api.DiscoveredHost().search(query={'mac': mac}) != [],
        timeout=1500,
        delay=40,
    )
    discovered_host = sat.api.DiscoveredHost().search(query={'mac': mac})[0]
    discovered_host.hostgroup = provisioning_hostgroup
    discovered_host.location = provisioning_hostgroup.location[0]
    discovered_host.organization = provisioning_hostgroup.organization[0]
    discovered_host.build = True
    result = sat.cli.DiscoveredHost.provision(
        {
            'id': discovered_host.id,
            'hostgroup-id': discovered_host.hostgroup.id,
            'organization-id': discovered_host.organization.id,
            'location-id': discovered_host.location.id,
        }
    )
    assert 'Host created' in result[0]['message']
    host = sat.api.Host().search(query={"search": f'id={discovered_host.id}'})[0]
    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))
    assert host

    wait_for(
        lambda: host.read().build_status_label != 'Pending installation',
        timeout=1500,
        delay=10,
    )
    assert host.read().build_status_label == 'Installed'
    assert not sat.api.DiscoveredHost().search(query={'mac': mac})


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_provision_pxeless_bios_syslinux():
    """Provision and discover the pxe-less BIOS host from cli using SYSLINUX
    loader

    :id: ae7f3ce2-e66e-44dc-85cb-0c3c4782cbb1

    :Setup:
        1. Craft the FDI with remaster the image to have ssh enabled

    :steps:
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


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_provision_pxe_host_with_bios_syslinux():
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


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_delete():
    """Delete the selected discovered host

    :id: c4103de8-145c-4a7d-b837-a1dec97231a2

    :Setup: Host should already be discovered

    :expectedresults: Selected host should be removed successfully

    :CaseImportance: High
    """


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

    :steps: Validate specified builtin and custom facts

    :expectedresults: All checked facts should be displayed correctly

    :CaseAutomation: NotAutomated

    :CaseImportance: High
    """
