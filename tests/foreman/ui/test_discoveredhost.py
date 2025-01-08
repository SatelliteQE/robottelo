"""Test class for Foreman Discovery

:Requirement: Discoveredhost

:CaseAutomation: Automated

:CaseComponent: DiscoveryImage

:Team: Rocket

"""

from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.utils import ssh

pytestmark = [pytest.mark.run_in_one_thread]


@pytest.fixture
def discovered_host(target_sat):
    return target_sat.api_factory.create_discovered_host()


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
    result = ssh.command(cmd.format(retries, host, operator, iteration_sleep))
    if expect_reachable:
        return not result.status
    return bool(result.status)


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('module_provisioning_sat', ['discovery'], indirect=True)
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.rhel_ver_match('9')
def test_positive_provision_pxe_host(
    request,
    session,
    module_location,
    module_org,
    module_provisioning_rhel_content,
    module_discovery_sat,
    provisioning_host,
    provisioning_hostgroup,
    pxe_loader,
):
    """Provision a PXE-based discoveredhost

    :id: 34c1e9ea-f210-4a1e-aead-421eb962643b

    :Setup:

        1. Host should already be discovered
        2. Hostgroup should already be created with all required entities.

    :expectedresults: Host should be provisioned and entry from
        discovered host should be auto removed.

    :BZ: 1728306, 1731112

    :CaseImportance: High
    """
    sat = module_discovery_sat.sat
    provisioning_host.power_control(ensure=False)
    mac = provisioning_host._broker_args['provisioning_nic_mac_addr']
    wait_for(
        lambda: sat.api.DiscoveredHost().search(query={'mac': mac}) != [],
        timeout=1500,
        delay=20,
    )
    discovered_host = sat.api.DiscoveredHost().search(query={'mac': mac})[0]
    discovered_host.hostgroup = provisioning_hostgroup
    discovered_host.location = provisioning_hostgroup.location[0]
    discovered_host.organization = provisioning_hostgroup.organization[0]
    discovered_host.build = True

    discovered_host_name = discovered_host.name
    domain_name = provisioning_hostgroup.domain.read().name
    host_name = f'{discovered_host_name}.{domain_name}'

    # Teardown
    request.addfinalizer(lambda: sat.provisioning_cleanup(host_name))

    with session:
        session.discoveredhosts.provision(
            discovered_host_name,
            provisioning_hostgroup.name,
            module_org.name,
            module_location.name,
        )
        values = session.host.get_details(host_name)
        assert values['properties']['properties_table']['Status'] == 'OK'
        assert not session.discoveredhosts.search(f'name = {discovered_host_name}')


@pytest.mark.tier3
def test_positive_update_name(
    session, discovery_org, discovery_location, module_discovery_hostgroup, discovered_host
):
    """Update the discovered host name and provision it

    :id: 3770b007-5006-4815-ae03-fbd330aad304

    :Setup: Host should already be discovered

    :expectedresults: The hostname should be updated and host should be
        provisioned

    :BZ: 1728306, 1731112

    :CaseImportance: High
    """
    discovered_host_name = discovered_host['name']
    domain_name = module_discovery_hostgroup.domain.read().name
    new_name = gen_string('alpha').lower()
    new_host_name = f'{new_name}.{domain_name}'
    with session:
        discovered_host_values = session.discoveredhosts.wait_for_entity(discovered_host_name)
        assert discovered_host_values['Name'] == discovered_host_name
        session.discoveredhosts.provision(
            discovered_host_name,
            module_discovery_hostgroup.name,
            discovery_org.name,
            discovery_location.name,
            quick=False,
            host_values={'host.name': new_name},
        )
        assert session.host.search(new_host_name)[0]['Name'] == new_host_name
        values = session.host.get_details(new_host_name)
        assert values['properties']['properties_table']['Status'] == 'OK'
        assert not session.discoveredhosts.search(f'name = {discovered_host_name}')


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('module_provisioning_sat', ['discovery'], indirect=True)
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.rhel_ver_match('9')
def test_positive_auto_provision_host_with_rule(
    request,
    session,
    module_org,
    module_location,
    module_provisioning_rhel_content,
    module_discovery_sat,
    pxeless_discovery_host,
    provisioning_hostgroup,
    pxe_loader,
):
    """Create a new discovery rule and automatically provision host from discovered host using that
    discovery rule.

    Set query as (e.g IP=IP_of_discovered_host)

    :id: 4488ab9a-d462-4a62-a1a1-e5656c8a8b99

    :Setup: Host should already be discovered

    :expectedresults: Host should be successfully provisioned

    :BZ: 1665471, 1731112

    :CaseImportance: High
    """
    sat = module_discovery_sat.sat
    pxeless_discovery_host.power_control(ensure=False)
    mac = pxeless_discovery_host._broker_args['provisioning_nic_mac_addr']
    wait_for(
        lambda: sat.api.DiscoveredHost().search(query={'mac': mac}) != [],
        timeout=1500,
        delay=20,
    )
    discovered_host = sat.api.DiscoveredHost().search(query={'mac': mac})[0]
    discovered_host.hostgroup = provisioning_hostgroup
    discovered_host.location = provisioning_hostgroup.location[0]
    discovered_host.organization = provisioning_hostgroup.organization[0]
    discovered_host.build = True

    discovered_host_name = discovered_host.name
    domain_name = provisioning_hostgroup.domain.read().name
    host_name = f'{discovered_host_name}.{domain_name}'

    # Teardown
    request.addfinalizer(lambda: sat.provisioning_cleanup(host_name))

    discovery_rule = sat.api.DiscoveryRule(
        max_count=10,
        hostgroup=provisioning_hostgroup,
        search_=f'name = {discovered_host_name}',
        location=[module_location],
        organization=[module_org],
    ).create()
    with session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        session.discoveredhosts.apply_action('Auto Provision', [discovered_host_name])
        assert session.host.search(host_name)[0]['Name'] == host_name
        host_values = session.host.get_details(host_name)
        assert host_values['properties']['properties_table']['Status'] == 'OK'
        assert (
            host_values['properties']['properties_table']['Comment']
            == f"Auto-discovered and provisioned via rule '{discovery_rule.name}'"
        )
        assert not session.discoveredhosts.search(f'name = {discovered_host_name}')


@pytest.mark.tier3
def test_positive_delete(session, discovery_org, discovery_location, discovered_host):
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
def test_positive_update_default_taxonomies(session, discovery_org, discovery_location, target_sat):
    """Change the default organization and location of more than one
    discovered hosts from 'Select Action' drop down

    :id: 4b491121-f6ee-4a8c-bb0b-daa3d0a75add

    :Setup: Host should already be discovered

    :expectedresults: Default Organization and Location should be successfully
        changed for multiple hosts. Changes are also reflected in dashboard

    :BZ: 1634728, 1731112, 1741454

    :CaseImportance: High
    """
    host_names = [target_sat.api_factory.create_discovered_host()['name'] for _ in range(2)]
    new_org = target_sat.api.Organization().create()
    discovery_location.organization.append(new_org)
    discovery_location.update(['organization'])
    new_loc = target_sat.api.Location(organization=[discovery_org]).create()
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
