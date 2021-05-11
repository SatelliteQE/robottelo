"""Test class for Foreman Discovery

:Requirement: Discoveredhost

:CaseAutomation: Automated

:CaseComponent: DiscoveryPlugin

:Assignee: rplevka

:TestType: Functional

:CaseLevel: System

:Upstream: No
"""
import pytest
from fauxfactory import gen_ipaddr
from fauxfactory import gen_string
from nailgun import entities

from robottelo import ssh
from robottelo.api.utils import configure_provisioning
from robottelo.api.utils import create_discovered_host
from robottelo.libvirt_discovery import LibvirtGuest
from robottelo.products import RHELRepository

pytestmark = [pytest.mark.run_in_one_thread]


@pytest.fixture(scope='module')
def module_org():
    org = entities.Organization().create()
    # Update default discovered host organization
    discovery_org = entities.Setting().search(query={'search': 'name="discovery_organization"'})[0]
    default_discovery_org = discovery_org.value
    discovery_org.value = org.name
    discovery_org.update(['value'])
    yield org
    discovery_org.value = default_discovery_org
    discovery_org.update(['value'])


@pytest.fixture(scope='module')
def module_loc(module_org):
    loc = entities.Location(name=gen_string('alpha'), organization=[module_org]).create()
    # Update default discovered host location
    discovery_loc = entities.Setting().search(query={'search': 'name="discovery_location"'})[0]
    default_discovery_loc = discovery_loc.value
    discovery_loc.value = loc.name
    discovery_loc.update(['value'])
    yield loc
    discovery_loc.value = default_discovery_loc
    discovery_loc.update(['value'])


@pytest.fixture(scope='module')
def provisioning_env(module_org, module_loc):
    # Build PXE default template to get default PXE file
    entities.ProvisioningTemplate().build_pxe_default()
    return configure_provisioning(
        org=module_org,
        loc=module_loc,
        os='Redhat {}'.format(RHELRepository().repo_data['version']),
    )


@pytest.fixture
def discovered_host():
    return create_discovered_host()


@pytest.fixture(scope='module')
def module_host_group(module_org, module_loc):
    host = entities.Host(organization=module_org, location=module_loc)
    host.create_missing()
    return entities.HostGroup(
        organization=[module_org],
        location=[module_loc],
        medium=host.medium,
        root_pass=gen_string('alpha'),
        operatingsystem=host.operatingsystem,
        ptable=host.ptable,
        domain=host.domain,
        architecture=host.architecture,
    ).create()


def _is_host_reachable(host, retries=12, iteration_sleep=5, expect_reachable=True):
    """Helper to ensure given IP/hostname is reachable or not. The return value
    returned depend from expect reachable value.

    :param str host: The IP or hostname of host.
    :param int retries: The polling retries.
    :param int iteration_sleep: time to wait after each retry iteration.
    :param bool expect_reachable: Whether we expect the host to be reachable.
    :return: bool
    """
    operator = '&&'
    if not expect_reachable:
        operator = '||'
    cmd = 'for i in {{1..{0}}}; do ping -c1 {1} {2} exit 0; sleep {3}; done; exit 1'
    result = ssh.command(
        cmd.format(retries, host, operator, iteration_sleep), connection_timeout=30
    )
    if expect_reachable:
        return not result.return_code
    else:
        return bool(result.return_code)


@pytest.mark.skip_if_not_set('compute_resources', 'vlan_networking')
@pytest.mark.tier3
@pytest.mark.vlan_networking
@pytest.mark.libvirt_discovery
@pytest.mark.upgrade
def test_positive_pxe_based_discovery(session, provisioning_env):
    """Discover a host via PXE boot by setting "proxy.type=proxy" in
    PXE default

    :id: 43a8857d-2f08-436e-97fb-ffec6a0c84dd

    :Setup: Provisioning should be configured

    :Steps: PXE boot a host/VM

    :expectedresults: Host should be successfully discovered

    :BZ: 1731112

    :CaseImportance: Critical
    """
    with LibvirtGuest() as pxe_host:
        host_name = pxe_host.guest_name
        with session:
            discovered_host_values = session.discoveredhosts.wait_for_entity(host_name)
            assert discovered_host_values['Name'] == host_name


@pytest.mark.skip_if_not_set('compute_resources', 'discovery', 'vlan_networking')
@pytest.mark.tier3
@pytest.mark.vlan_networking
@pytest.mark.libvirt_discovery
@pytest.mark.upgrade
def test_positive_pxe_less_with_dhcp_unattended(session, provisioning_env):
    """Discover a host with dhcp via bootable discovery ISO by setting
    "proxy.type=proxy" in PXE default in unattended mode.

    :id: fc13167f-6fa0-4fe5-8584-7716292866ce

    :Setup: Provisioning should be configured

    :Steps: Boot a host/VM using modified discovery ISO.

    :expectedresults: Host should be successfully discovered

    :BZ: 1731112

    :CaseImportance: Critical
    """
    with LibvirtGuest(boot_iso=True) as pxe_less_host:
        host_name = pxe_less_host.guest_name
        with session:
            discovered_host_values = session.discoveredhosts.wait_for_entity(host_name)
            assert discovered_host_values['Name'] == host_name


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_provision_using_quick_host_button(
    session, module_org, module_loc, discovered_host, module_host_group
):
    """Associate hostgroup while provisioning a discovered host from
    host properties model window and select quick host.

    :id: 34c1e9ea-f210-4a1e-aead-421eb962643b

    :Setup:

        1. Host should already be discovered
        2. Hostgroup should already be created with all required entities.

    :expectedresults: Host should be quickly provisioned and entry from
        discovered host should be auto removed.

    :BZ: 1728306, 1731112

    :CaseImportance: High
    """
    discovered_host_name = discovered_host['name']
    domain_name = module_host_group.domain.read().name
    host_name = f'{discovered_host_name}.{domain_name}'
    with session:
        session.discoveredhosts.provision(
            discovered_host_name, module_host_group.name, module_org.name, module_loc.name
        )
        values = session.host.get_details(host_name)
        assert values['properties']['properties_table']['Status'] == 'OK'
        assert not session.discoveredhosts.search(f'name = {discovered_host_name}')


@pytest.mark.tier3
def test_positive_update_name(session, module_org, module_loc, module_host_group, discovered_host):
    """Update the discovered host name and provision it

    :id: 3770b007-5006-4815-ae03-fbd330aad304

    :Setup: Host should already be discovered

    :expectedresults: The hostname should be updated and host should be
        provisioned

    :BZ: 1728306, 1731112

    :CaseImportance: High
    """
    discovered_host_name = discovered_host['name']
    domain_name = module_host_group.domain.read().name
    new_name = gen_string('alpha').lower()
    new_host_name = f'{new_name}.{domain_name}'
    with session:
        discovered_host_values = session.discoveredhosts.wait_for_entity(discovered_host_name)
        assert discovered_host_values['Name'] == discovered_host_name
        session.discoveredhosts.provision(
            discovered_host_name,
            module_host_group.name,
            module_org.name,
            module_loc.name,
            quick=False,
            host_values={'host.name': new_name},
        )
        assert session.host.search(new_host_name)[0]['Name'] == new_host_name
        values = session.host.get_details(new_host_name)
        assert values['properties']['properties_table']['Status'] == 'OK'
        assert not session.discoveredhosts.search(f'name = {discovered_host_name}')


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_auto_provision_host_with_rule(
    session, module_org, module_loc, module_host_group
):
    """Create a new discovery rule and automatically create host from discovered host using that
    discovery rule.

    Set query as (e.g IP=IP_of_discovered_host)

    :id: 4488ab9a-d462-4a62-a1a1-e5656c8a8b99

    :Setup: Host should already be discovered

    :expectedresults: Host should reboot and provision

    :BZ: 1665471, 1731112

    :CaseImportance: High
    """
    host_ip = gen_ipaddr()
    discovered_host_name = create_discovered_host(ip_address=host_ip)['name']
    domain = module_host_group.domain.read()
    discovery_rule = entities.DiscoveryRule(
        max_count=1,
        hostgroup=module_host_group,
        search_=f'ip = {host_ip}',
        location=[module_loc],
        organization=[module_org],
    ).create()
    with session:
        session.discoveredhosts.apply_action('Auto Provision', [discovered_host_name])
        host_name = f'{discovered_host_name}.{domain.name}'
        assert session.host.search(host_name)[0]['Name'] == host_name
        host_values = session.host.get_details(host_name)
        assert host_values['properties']['properties_table']['Status'] == 'OK'
        assert host_values['properties']['properties_table']['IP Address'] == host_ip
        assert (
            host_values['properties']['properties_table']['Comment']
            == f"Auto-discovered and provisioned via rule '{discovery_rule.name}'"
        )
        assert not session.discoveredhosts.search(f'name = {discovered_host_name}')


@pytest.mark.tier3
def test_positive_delete(session, discovered_host):
    """Delete the selected discovered host

    :id: 25a2a3ea-9659-4bdb-8631-c4dd19766014

    :Setup: Host should already be discovered

    :expectedresults: Selected host should be removed successfully

    :BZ: 1731112

    :CaseImportance: High
    """
    discovered_host_name = discovered_host['name']
    with session:
        session.discoveredhosts.delete(discovered_host_name)
        assert not session.discoveredhosts.search(f'name = {discovered_host_name}')


@pytest.mark.tier3
def test_positive_update_default_taxonomies(session, module_org, module_loc):
    """Change the default organization and location of more than one
    discovered hosts from 'Select Action' drop down

    :id: 4b491121-f6ee-4a8c-bb0b-daa3d0a75add

    :Setup: Host should already be discovered

    :expectedresults: Default Organization and Location should be successfully
        changed for multiple hosts. Changes are also reflected in dashboard

    :BZ: 1634728, 1731112, 1741454

    :CaseImportance: High
    """
    host_names = [create_discovered_host()['name'] for _ in range(2)]
    new_org = entities.Organization().create()
    module_loc.organization.append(new_org)
    module_loc.update(['organization'])
    new_loc = entities.Location(organization=[module_org]).create()
    with session:
        values = session.discoveredhosts.search('name = "{}" or name = "{}"'.format(*host_names))
        assert set(host_names) == {value['Name'] for value in values}
        session.discoveredhosts.apply_action(
            'Assign Organization', host_names, values=dict(organization=new_org.name)
        )
        assert not session.discoveredhosts.search('name = "{}" or name = "{}"'.format(*host_names))
        session.organization.select(org_name=new_org.name)
        values = session.discoveredhosts.search('name = "{}" or name = "{}"'.format(*host_names))
        assert set(host_names) == {value['Name'] for value in values}
        session.discoveredhosts.apply_action(
            'Assign Location', host_names, values=dict(location=new_loc.name)
        )
        assert not session.discoveredhosts.search('name = "{}" or name = "{}"'.format(*host_names))
        session.location.select(loc_name=new_loc.name)
        values = session.discoveredhosts.search('name = "{}" or name = "{}"'.format(*host_names))
        assert set(host_names) == {value['Name'] for value in values}
        values = session.dashboard.read('DiscoveredHosts')
        assert len(values['hosts']) == 2


@pytest.mark.skip_if_not_set('compute_resources', 'vlan_networking')
@pytest.mark.libvirt_discovery
@pytest.mark.vlan_networking
@pytest.mark.tier3
def test_positive_reboot(session, provisioning_env):
    """Reboot a discovered host.

    :id: 5edc6831-bfc8-4e69-9029-b4c0caa3ee32

    :Setup: Host should already be discovered

    :expectedresults: Discovered host without provision is going to shutdown after reboot command
        is passed.

    :BZ: 1731112

    :CaseImportance: Medium
    """
    with LibvirtGuest() as pxe_host:
        host_name = pxe_host.guest_name
        with session:
            discovered_host_values = session.discoveredhosts.wait_for_entity(host_name)
            assert discovered_host_values['Name'] == host_name
            host_ip = discovered_host_values['IP Address']
            assert host_ip
            # Ensure that the host is reachable
            assert _is_host_reachable(host_ip)
            session.discoveredhosts.apply_action('Reboot', host_name)
            # Ensure that the host is not reachable
            assert not _is_host_reachable(host_ip, expect_reachable=False)
