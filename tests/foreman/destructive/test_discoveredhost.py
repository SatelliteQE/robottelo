"""API Tests for foreman discovery feature

:Requirement: DiscoveredHost

:CaseComponent: DiscoveryImage

:Team: Rocket

:CaseAutomation: Automated

"""

from copy import copy
import re

import pytest
from wait_for import TimedOutError, wait_for

from robottelo.config import admin_nailgun_config
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
    return wait_for(
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
        except TimedOutError as err:
            # raise assertion error
            raise AssertionError(f'Timed out waiting for {pattern[1]} from VM') from err

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
        except TimedOutError as err:
            # raise assertion error
            raise AssertionError(f'Timed out waiting for VM (tftp) to fetch {pattern[1]}') from err

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
        except TimedOutError as err:
            # raise assertion error
            raise AssertionError(f'Timed out waiting for {pattern[1]} from VM') from err
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
    except TimedOutError as err:
        # raise assertion error
        raise AssertionError('Timed out waiting for /facts POST request') from err
    groups = re.search('\\[I\\|app\\|([a-z0-9]+)\\]', facts_fdi.out)
    assert len(groups.groups()) == 1, 'Unable to parse POST request UUID'
    req_id = groups.groups()[0]

    try:
        _wait_for_log(channel, f'\\[I\\|app\\|{req_id}\\] Completed 201 Created')
    except TimedOutError as err:
        # raise assertion error
        raise AssertionError('Timed out waiting for "/facts" 201 response') from err

    default_config = admin_nailgun_config()

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
    except TimedOutError as err:
        raise AssertionError(
            'Timed out waiting for discovered_host to appear on satellite'
        ) from err
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


@pytest.mark.stubbed
def test_positive_provision_pxe_host_dhcp_change():
    """Discovered host is provisioned in dhcp range defined in subnet entity

    :id: 7ab654de-16dd-4a8b-946d-f6adde310340

    :bz: 1367549

    :customerscenario: true

    :Setup: Provisioning should be configured and a host should be
        discovered

    :steps:
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
