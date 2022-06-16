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
import simplejson
from fauxfactory import gen_choice
from fauxfactory import gen_ipaddr
from fauxfactory import gen_mac
from fauxfactory import gen_string
from nailgun import entities
from nailgun import entity_mixins
from wait_for import TimedOutError
from wait_for import wait_for

from robottelo.cli.factory import configure_env_for_provision
from robottelo.datafactory import valid_data_list
from robottelo.helpers import get_nailgun_config
from robottelo.libvirt_discovery import LibvirtGuest
from robottelo.logging import logger
from robottelo.utils.issue_handlers import is_open


class HostNotDiscoveredException(Exception):
    """Raised when host is not discovered"""


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


def _assert_discovered_host(host, channel=None, user_config=None):
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
                entities.DiscoveredHost(user_config or default_config).search(
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
    discovered_host = entities.DiscoveredHost(user_config or default_config).search(
        query={'search': f'name={host.guest_name}'}
    )
    return discovered_host[0]


@pytest.fixture(scope="module", params=['non-admin', 'admin'])
def _module_user(request, module_org, module_location):
    if request.param == 'admin':
        yield None
    else:
        # setup a clone of DiscoveryManager role
        discoman_role = entities.Role().search(query={'search': 'name="Discovery Manager"'})[0]
        passwd = gen_string('alpha')
        user = entities.User(
            organization=[module_org],
            location=[module_location],
            password=passwd,
            role=[discoman_role],
        ).create()
        yield (user, passwd)


@pytest.fixture(scope="module")
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
    entities.ProvisioningTemplate().build_pxe_default()
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
        i.name: i for i in entities.Setting().search(query={'search': 'name~discovery'})
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
def provisioning_env(module_org, module_location):
    env = configure_env_for_provision(
        org={'id': module_org.id, 'name': module_org.name},
        loc={'id': module_location.id, 'name': module_location.name},
    )
    yield env


@pytest.fixture()
def discovered_host_cleanup():
    hosts = entities.DiscoveredHost().search()
    for host in hosts:
        host.delete()


class TestFakeDiscoveryTests:
    """Tests that uses fake discovered host."""

    def _create_discovered_host(self, name=None, ipaddress=None, macaddress=None):
        """Creates discovered host by uploading few fake facts.

        :param str name: Name of discovered host. If ``None`` then a random
            value will be generated.
        :param str ipaddress: A valid ip address.
            If ``None`` then then a random value will be generated.
        :param str macaddress: A valid mac address.
            If ``None`` then then a random value will be generated.
        :return: A ``dict`` of ``DiscoveredHost`` facts.
        """
        if name is None:
            name = gen_string('alpha')
        if ipaddress is None:
            ipaddress = gen_ipaddr()
        if macaddress is None:
            macaddress = gen_mac(multicast=False)
        return entities.DiscoveredHost().facts(
            json={
                'facts': {
                    'name': name,
                    'discovery_bootip': ipaddress,
                    'discovery_bootif': macaddress,
                    'interfaces': 'eth0',
                    'ipaddress': ipaddress,
                    'macaddress': macaddress,
                    'macaddress_eth0': macaddress,
                    'ipaddress_eth0': ipaddress,
                }
            }
        )

    @pytest.mark.tier2
    def test_positive_upload_facts(self):
        """Upload fake facts to create a discovered host

        :id: c1f40204-bbb0-46d0-9b60-e42f00ad1649

        :BZ: 1349364, 1392919

        :Steps:

            1. POST /api/v2/discovered_hosts/facts
            2. Read the created discovered host

        :expectedresults: Host should be created successfully

        :CaseImportance: High

        :CaseLevel: Integration

        :BZ: 1731112
        """
        name = gen_choice(list(valid_data_list().values()))
        result = self._create_discovered_host(name)
        discovered_host = entities.DiscoveredHost(id=result['id']).read_json()
        host_name = 'mac{}'.format(discovered_host['mac'].replace(':', ''))
        assert discovered_host['name'] == host_name

    @pytest.mark.tier3
    def test_positive_delete_pxe_host(self):
        """Delete a pxe-based discovered hosts

        :id: 2ab2ad88-4470-4d4c-8e0b-5892ad8d675e

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: DELETE /api/v2/discovered_hosts/:id

        :expectedresults: Discovered Host should be deleted successfully

        :CaseAutomation: Automated

        :CaseImportance: High
        """
        name = gen_choice(list(valid_data_list().values()))
        result = self._create_discovered_host(name)

        entities.DiscoveredHost(id=result['id']).delete()
        search = entities.DiscoveredHost().search(
            query={'search': 'name == {}'.format(result['name'])}
        )
        assert len(search) == 0


@pytest.mark.libvirt_discovery
class TestLibvirtHostDiscovery:
    """Tests that uses discovered hosts from LibVirt Provider"""

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_provision_pxe_less_host(self):
        """Provision a pxe-less discovered hosts

        :id: 91bb254b-3c30-4608-b1ba-e18bcc22efb5

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: PUT /api/v2/discovered_hosts/:id

        :expectedresults: Host should be provisioned successfully

        :CaseAutomation: NotAutomated

        :CaseImportance: Critical
        """

    @pytest.mark.run_in_one_thread
    @pytest.mark.skip_if_not_set('vlan_networking')
    @pytest.mark.tier3
    def test_positive_provision_pxe_host(
        self, _module_user, discovery_settings, provisioning_env, target_sat
    ):
        """Provision a pxe-based discovered hosts

        :id: e805b9c5-e8f6-4129-a0e6-ab54e5671ddb

        :parametrized: yes

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: PUT /api/v2/discovered_hosts/:id

        :expectedresults: Host should be provisioned successfully

        :CaseImportance: Critical
        """
        cfg = get_nailgun_config()
        if _module_user:
            cfg.auth = (_module_user[0].login, _module_user[1])

        # open a ssh channel and attach it to foreman-tail output
        with target_sat.session.shell() as shell:
            shell.send('foreman-tail')

            with LibvirtGuest() as pxe_host:
                discovered_host = _assert_discovered_host(pxe_host, shell, user_config=cfg)
                # Provision just discovered host
                discovered_host.hostgroup = entities.HostGroup(
                    cfg, id=provisioning_env['hostgroup']['id']
                ).read()
                discovered_host.root_pass = gen_string('alphanumeric')
                discovered_host.update(['hostgroup', 'root_pass'])
                # Assertions
                provisioned_host = entities.Host(cfg).search(
                    query={
                        'search': 'name={}.{}'.format(
                            discovered_host.name, provisioning_env['domain']['name']
                        )
                    }
                )[0]
                assert provisioned_host.subnet.read().name == provisioning_env['subnet']['name']
                assert (
                    provisioned_host.operatingsystem.read().ptable[0].read().name
                    == provisioning_env['ptable']['name']
                )
                assert (
                    provisioned_host.operatingsystem.read().title == provisioning_env['os']['title']
                )
                assert not entities.DiscoveredHost(cfg).search(
                    query={'search': f'name={discovered_host.name}'}
                )

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier3
    @pytest.mark.skip_if_not_set('vlan_networking')
    def test_positive_auto_provision_pxe_host(
        self,
        _module_user,
        module_org,
        module_location,
        discovery_settings,
        provisioning_env,
        target_sat,
    ):
        """Auto provision a pxe-based host by executing discovery rules

        :id: c93fd7c9-41ef-4eb5-8042-f72e87e67e10

        :parametrized: yes

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: POST /api/v2/discovered_hosts/:id/auto_provision

        :expectedresults: Selected Host should be auto-provisioned successfully

        :CaseAutomation: Automated

        :CaseImportance: Critical
        """
        cfg = get_nailgun_config()
        if _module_user:
            cfg.auth = (_module_user[0].login, _module_user[1])

        # open a ssh channel and attach it to foreman-tail output
        with target_sat.session.shell() as shell:
            shell.send('foreman-tail')

            with LibvirtGuest() as pxe_host:
                discovered_host = _assert_discovered_host(pxe_host, shell, user_config=cfg)
                # Provision just discovered host
                discovered_host.hostgroup = entities.HostGroup(
                    cfg, id=provisioning_env['hostgroup']['id']
                ).read()

                # create a discovery rule that will match hosts MAC address
                entities.DiscoveryRule(
                    name=gen_string('alphanumeric'),
                    search_=f"mac = {discovered_host.mac}",
                    organization=[module_org],
                    location=[module_location],
                    hostgroup=entities.HostGroup(
                        cfg, id=provisioning_env['hostgroup']['id']
                    ).read(),
                ).create()
                # Auto-provision the host
                discovered_host.auto_provision()

                # Assertions
                provisioned_host = entities.Host(cfg).search(
                    query={
                        'search': 'name={}.{}'.format(
                            discovered_host.name, provisioning_env['domain']['name']
                        )
                    }
                )[0]
                assert provisioned_host.subnet.read().name == provisioning_env['subnet']['name']
                assert (
                    provisioned_host.operatingsystem.read().ptable[0].read().name
                    == provisioning_env['ptable']['name']
                )
                assert (
                    provisioned_host.operatingsystem.read().title == provisioning_env['os']['title']
                )
                assert not entities.DiscoveredHost(cfg).search(
                    query={'search': f'name={discovered_host.name}'}
                )

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_auto_provision_all(self):
        """Auto provision all host by executing discovery rules

        :id: 954d3688-62d9-47f7-9106-a4fff8825ffa

        :Setup: Provisioning should be configured and more than one host should
            be discovered

        :Steps: POST /api/v2/discovered_hosts/auto_provision_all

        :expectedresults: All discovered hosts should be auto-provisioned
            successfully

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_refresh_facts_pxe_host(self):
        """Refresh the facts of pxe based discovered hosts by adding a new NIC

        :id: 413fb608-cd5c-441d-af86-fd2d40346d96

        :Setup:
            1. Provisioning should be configured and more than one host should
            be discovered
            2. Add a NIC on discovered host

        :Steps: PUT /api/v2/discovered_hosts/:id/refresh_facts

        :expectedresults: Added Fact should be displayed on refreshing the
            facts

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.run_in_one_thread
    @pytest.mark.skip_if_not_set('vlan_networking')
    @pytest.mark.tier3
    def test_positive_reboot_pxe_host(
        self, _module_user, discovery_settings, provisioning_env, target_sat
    ):
        """Rebooting a pxe based discovered host

        :id: 69c807f8-5646-4aa6-8b3c-5ecab69560fc

        :parametrized: yes

        :Setup: Provisioning should be configured and a host should be discovered via PXE boot.

        :Steps: PUT /api/v2/discovered_hosts/:id/reboot

        :expectedresults: Selected host should be rebooted successfully

        :CaseAutomation: Automated

        :CaseImportance: Medium
        """
        cfg = get_nailgun_config()
        if _module_user:
            cfg.auth = (_module_user[0].login, _module_user[1])

        # open a ssh channel and attach it to foreman-tail output
        with target_sat.session.shell() as shell:
            shell.send('foreman-tail')

            with LibvirtGuest() as pxe_host:
                discovered_host = _assert_discovered_host(pxe_host, shell, user_config=cfg)
                discovered_host.reboot()

                # assert that server receives DHCP discover from hosts PXELinux
                # this means that the host got rebooted
                for pattern in [
                    (
                        f"DHCPDISCOVER from {pxe_host.mac}",
                        "DHCPDISCOVER",
                    ),
                    (f"DHCPACK on [0-9.]+ to {pxe_host.mac}", "DHCPACK"),
                ]:
                    try:
                        _wait_for_log(shell, pattern[0], timeout=30)
                    except TimedOutError:
                        # raise assertion error
                        raise AssertionError(f'Timed out waiting for {pattern[1]} from VM')

    @pytest.mark.run_in_one_thread
    @pytest.mark.skip_if_not_set('vlan_networking')
    @pytest.mark.tier3
    def test_positive_reboot_all_pxe_hosts(
        self,
        _module_user,
        discovered_host_cleanup,
        discovery_settings,
        provisioning_env,
        target_sat,
    ):
        """Rebooting all pxe-based discovered hosts

        :id: 69c807f8-5646-4aa6-8b3c-5ecdb69560ed

        :parametrized: yes

        :Setup: Provisioning should be configured and a hosts should be discovered via PXE boot.

        :Steps: PUT /api/v2/discovered_hosts/reboot_all

        :expectedresults: All disdcovered host should be rebooted successfully

        :CaseAutomation: Automated

        :CaseImportance: Medium
        """
        cfg = get_nailgun_config()
        if _module_user:
            cfg.auth = (_module_user[0].login, _module_user[1])

        # open ssh channels and attach them to foreman-tail output
        shell_1, shell_2 = target_sat.session.shell(), target_sat.session.shell()
        shell_1.send('foreman-tail')
        shell_2.send('foreman-tail')

        with LibvirtGuest() as pxe_host_1:
            _assert_discovered_host(pxe_host_1, shell_1, user_config=cfg)
            with LibvirtGuest() as pxe_host_2:
                _assert_discovered_host(pxe_host_2, shell_2, user_config=cfg)
                # reboot_all method leads to general /discovered_hosts/ path, so it doesn't matter
                # what DiscoveredHost object we execute this on
                try:
                    entities.DiscoveredHost().reboot_all()
                except simplejson.errors.JSONDecodeError as e:
                    if is_open('BZ:1893349'):
                        pass
                    else:
                        raise e
                # assert that server receives DHCP discover from hosts PXELinux
                # this means that the hosts got rebooted
                for pxe_host in [(pxe_host_1, shell_1), (pxe_host_2, shell_2)]:
                    for pattern in [
                        (
                            f"DHCPDISCOVER from {pxe_host[0].mac}",
                            "DHCPDISCOVER",
                        ),
                        (f"DHCPACK on [0-9.]+ to {pxe_host[0].mac}", "DHCPACK"),
                    ]:
                        try:
                            _wait_for_log(pxe_host[1], pattern[0], timeout=30)
                        except TimedOutError:
                            # raise assertion error
                            raise AssertionError(
                                f'Timed out waiting for {pattern[1]} from ' f'{pxe_host[0].mac}'
                            )

    @pytest.mark.destructive
    @pytest.mark.skip_if_not_set('vlan_networking')
    def test_positive_provision_pxe_host_dhcp_change(
        self, discovery_settings, provisioning_env, target_sat
    ):
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

        cfg = get_nailgun_config()
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
                    discovered_host = _assert_discovered_host(pxe_host, shell, cfg)
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
