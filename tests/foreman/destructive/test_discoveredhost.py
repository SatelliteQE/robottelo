"""API Tests for foreman discovery feature

:Requirement: DiscoveredHost

:CaseComponent: DiscoveryImage

:Assignee: gsulliva

:CaseAutomation: Automated

:CaseLevel: System

:TestType: Functional

:Upstream: No
"""
import re
from copy import copy

import pytest
from fauxfactory import gen_string
from nailgun import entity_mixins
from wait_for import TimedOutError
from wait_for import wait_for

from robottelo.config import get_credentials
from robottelo.config import user_nailgun_config
from robottelo.libvirt_discovery import LibvirtGuest
from robottelo.logging import logger

pytestmark = pytest.mark.destructive


def _read_log(ch, pattern):
    """Read a first line from the given channel buffer and return the matching line"""
    # read lines until the buffer is empty
    for log_line in ch.stdout().splitlines():
        logger.debug(f'foreman-tail: {log_line}')
        if re.search(pattern, log_line):
            return log_line
    else:
        return None


def _wait_for_log(channel, pattern, timeout=5, delay=0.2):
    """_read_log method enclosed in wait_for method"""
    matching_log = wait_for(
        _read_log,
        func_args=(
            channel,
            pattern,
        ),
        fail_condition=None,
        timeout=timeout,
        delay=delay,
        logger=logger,
    )
    return matching_log


def _assert_discovered_host(host, channel=None, user_config=None, sat=None):
    """Check if host is discovered and information about it can be
    retrieved back

    Introduced a delay of 300secs by polling every 10 secs to get expected
    host
    """
    # assert that server receives DHCP discover from hosts PXELinux
    for pattern in [
        (
            f"DHCPDISCOVER from {host.mac}",
            "DHCPDISCOVER",
        ),
        (f"DHCPACK on [0-9.]+ to {host.mac}", "DHCPACK"),
    ]:
        try:
            dhcp_pxe = _wait_for_log(channel, pattern[0], timeout=10)
        except TimedOutError:
            # raise assertion error
            raise AssertionError(f'Timed out waiting for {pattern[1]} from VM')

    groups = re.search('DHCPACK on (\\d.+) to', dhcp_pxe.out)
    assert len(groups.groups()) == 1, 'Unable to parse bootloader ip address'
    pxe_ip = groups.groups()[0]

    # assert that server retrieves pxelinux config over TFTP
    for pattern in [
        (f'Client {pxe_ip} finished pxelinux.0', 'pxelinux.0'),
        (f'Client {pxe_ip} finished pxelinux.cfg/default', 'pxelinux.cfg/default'),
        (f'Client {pxe_ip} finished boot/fdi-image/vmlinuz0', 'fdi-image/vmlinuz0'),
        (f'Client {pxe_ip} finished boot/fdi-image/initrd0.img', 'fdi-image/initrd0.img'),
    ]:
        try:
            _wait_for_log(channel, pattern[0], timeout=20)
        except TimedOutError:
            # raise assertion error
            raise AssertionError(f'Timed out waiting for VM (tftp) to fetch {pattern[1]}')

    # assert that server receives DHCP discover from FDI
    for pattern in [
        (
            f"DHCPDISCOVER from {host.mac}",
            "DHCPDISCOVER",
        ),
        (f"DHCPACK on [0-9.]+ to {host.mac}", "DHCPACK"),
    ]:
        try:
            dhcp_fdi = _wait_for_log(channel, pattern[0], timeout=30)
        except TimedOutError:
            # raise assertion error
            raise AssertionError(f'Timed out waiting for {pattern[1]} from VM')
    groups = re.search('DHCPACK on (\\d.+) to', dhcp_fdi.out)
    assert len(groups.groups()) == 1, 'Unable to parse FDI ip address'
    fdi_ip = groups.groups()[0]

    # finally, assert that the FDI successfully uploaded its facts to the server
    try:
        facts_fdi = _wait_for_log(
            channel,
            f'\\[I\\|app\\|[a-z0-9]+\\] Started POST '
            f'"/api/v2/discovered_hosts/facts" for {fdi_ip}',
            timeout=60,
        )
    except TimedOutError:
        # raise assertion error
        raise AssertionError('Timed out waiting for /facts POST request')
    groups = re.search('\\[I\\|app\\|([a-z0-9]+)\\]', facts_fdi.out)
    assert len(groups.groups()) == 1, 'Unable to parse POST request UUID'
    req_id = groups.groups()[0]

    try:
        _wait_for_log(channel, f'\\[I\\|app\\|{req_id}\\] Completed 201 Created')
    except TimedOutError:
        # raise assertion error
        raise AssertionError('Timed out waiting for "/facts" 201 response')

    default_config = entity_mixins.DEFAULT_SERVER_CONFIG

    try:
        wait_for(
            lambda: len(
                sat.api.DiscoveredHost(user_config or default_config).search(
                    query={'search': f'name={host.guest_name}'}
                )
            )
            > 0,
            timeout=20,
            delay=2,
            logger=logger,
        )
    except TimedOutError:
        raise AssertionError('Timed out waiting for discovered_host to appear on satellite')
    discovered_host = sat.api.DiscoveredHost(user_config or default_config).search(
        query={'search': f'name={host.guest_name}'}
    )
    return discovered_host[0]


@pytest.fixture(scope='module')
def discovery_settings(module_org, module_location, target_sat):
    """Steps to Configure foreman discovery

    1. Build PXE default template
    2. Create Organization/Location
    3. Update Global parameters to set default org and location for
       discovered hosts.
    4. Enable auto_provision flag to perform discovery via discovery
       rules.
    """
    # Build PXE default template to get default PXE file
    target_sat.api.ProvisioningTemplate().build_pxe_default()
    # let's just modify the timeouts to speed things up
    target_sat.execute(
        "sed -ie 's/TIMEOUT [[:digit:]]\\+/TIMEOUT 1/g' " "/var/lib/tftpboot/pxelinux.cfg/default"
    )
    target_sat.execute(
        "sed -ie '/APPEND initrd/s/$/ fdi.countdown=1 fdi.ssh=1 fdi.rootpw=changeme/' "
        "/var/lib/tftpboot/pxelinux.cfg/default"
    )
    # Get default settings values
    default_disco_settings = {
        i.name: i for i in target_sat.api.Setting().search(query={'search': 'name~discovery'})
    }

    # Update discovery taxonomies settings
    discovery_loc = copy(default_disco_settings['discovery_location'])
    discovery_loc.value = module_location.name
    discovery_loc.update(['value'])
    discovery_org = copy(default_disco_settings['discovery_organization'])
    discovery_org.value = module_org.name
    discovery_org.update(['value'])

    # Enable flag to auto provision discovered hosts via discovery rules
    discovery_auto = copy(default_disco_settings['discovery_auto'])
    discovery_auto.value = 'true'
    discovery_auto.update(['value'])

    yield
    # Restore default global setting's values
    default_disco_settings['discovery_location'].update(['value'])
    default_disco_settings['discovery_organization'].update(['value'])
    default_disco_settings['discovery_auto'].update(['value'])


@pytest.fixture(scope='module')
def provisioning_env(module_org, module_location, module_target_sat):
    env = module_target_sat.cli_factory.configure_env_for_provision(
        org={'id': module_org.id, 'name': module_org.name},
        loc={'id': module_location.id, 'name': module_location.name},
    )
    yield env


@pytest.mark.skip_if_not_set('vlan_networking')
def test_positive_provision_pxe_host_dhcp_change(discovery_settings, provisioning_env, target_sat):
    """Discovered host is provisioned in dhcp range defined in subnet entity

    :id: 7ab654de-16dd-4a8b-946d-f6adde310340

    :bz: 1367549

    :customerscenario: true

    :Setup: Provisioning should be configured and a host should be
        discovered

    :Steps:
        1. Set some dhcp range in dhcpd.conf in satellite.
        2. Create subnet entity in satellite with a range different from whats defined
            in `dhcpd.conf`.
        3. Create Hostgroup with the step 2 subnet.
        4. Discover a new host in satellite.
        5. Provision a host with the hostgroup created in step 3.

    :expectedresults:
        1. The discovered host should be discovered with range defined in dhcpd.conf
        2. But provisoning the discovered host should acquire an IP from dhcp range
            defined in subnet entity.

    :CaseImportance: Critical
    """
    subnet = target_sat.api.Subnet(id=provisioning_env['subnet']['id']).read()
    # Updating satellite subnet component and dhcp conf ranges
    # Storing now for restoring later
    old_sub_from = subnet.from_
    old_sub_to = subnet.to
    old_sub_to_4o = old_sub_to.split('.')[-1]
    # Calculating Subnet's new `from` range in Satellite Subnet Component
    new_subnet_from = subnet.from_[: subnet.from_.rfind('.') + 1] + str(int(old_sub_to_4o) - 9)
    # Same time, calculating dhcp confs new `to` range
    new_dhcp_conf_to = subnet.to[: subnet.to.rfind('.') + 1] + str(int(old_sub_to_4o) - 10)

    cfg = user_nailgun_config()
    cfg.auth = get_credentials()
    with target_sat.session.shell() as shell:
        shell.send('foreman-tail')
        try:
            # updating the ranges in component and in dhcp.conf
            subnet.from_ = new_subnet_from
            subnet.update(['from_'])
            target_sat.execute(
                f'cp /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd_backup.conf && '
                f'sed -ie \'s/{subnet.to}/{new_dhcp_conf_to}/\' /etc/dhcp/dhcpd.conf && '
                f'systemctl restart dhcpd'
            )
            with LibvirtGuest() as pxe_host:
                discovered_host = _assert_discovered_host(pxe_host, shell, cfg, sat=target_sat)
                # Assert Discovered host discovered within dhcp.conf range before provisioning
                assert int(discovered_host.ip.split('.')[-1]) <= int(
                    new_dhcp_conf_to.split('.')[-1]
                )
                # Provision just discovered host
                discovered_host.hostgroup = target_sat.api.HostGroup(
                    id=provisioning_env['hostgroup']['id']
                ).read()
                discovered_host.root_pass = gen_string('alphanumeric')
                discovered_host.update(['hostgroup', 'root_pass'])
                # Assertions
                provisioned_host = target_sat.api.Host().search(
                    query={
                        'search': 'name={}.{}'.format(
                            discovered_host.name, provisioning_env['domain']['name']
                        )
                    }
                )[0]
                assert int(provisioned_host.ip.split('.')[-1]) >= int(
                    new_subnet_from.split('.')[-1]
                )
                assert int(provisioned_host.ip.split('.')[-1]) <= int(old_sub_to_4o)
                assert not target_sat.api.DiscoveredHost().search(
                    query={'search': f'name={discovered_host.name}'}
                )
        finally:
            subnet.from_ = old_sub_from
            subnet.update(['from_'])
            target_sat.execute(
                'mv /etc/dhcp/dhcpd_backup.conf /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf'
            )
