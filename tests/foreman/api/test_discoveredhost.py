# -*- encoding: utf-8 -*-
"""API Tests for foreman discovery feature

:Requirement: Discoveredhost

:CaseComponent: DiscoveryPlugin

:CaseAutomation: Automated

:CaseLevel: System

:TestType: Functional

:Upstream: No
"""
import time
from copy import copy

import pytest
from fauxfactory import gen_ipaddr
from fauxfactory import gen_mac
from fauxfactory import gen_string
from nailgun import entities
from nailgun import entity_mixins

from robottelo import ssh
from robottelo.api.utils import create_org_admin_user
from robottelo.cli.factory import configure_env_for_provision
from robottelo.datafactory import valid_data_list
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.helpers import get_nailgun_config
from robottelo.libvirt_discovery import LibvirtGuest
from robottelo.test import APITestCase


def _create_discovered_host(name=None, ipaddress=None, macaddress=None):
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


class HostNotDiscoveredException(Exception):
    """Raised when host is not discovered"""


class DiscoveryTestCase(APITestCase):
    """Implements tests for foreman discovery feature"""

    def _assertdiscoveredhost(self, hostname, user_config=None):
        """Check if host is discovered and information about it can be
        retrieved back

        Introduced a delay of 300secs by polling every 10 secs to get expected
        host
        """
        default_config = entity_mixins.DEFAULT_SERVER_CONFIG
        for _ in range(30):
            discovered_host = entities.DiscoveredHost(user_config or default_config).search(
                query={'search': 'name={}'.format(hostname)}
            )
            if discovered_host:
                break
            time.sleep(10)
        else:
            raise HostNotDiscoveredException(
                "The host {} is not discovered within 300 seconds".format(hostname)
            )
        return discovered_host[0]

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

        # Build PXE default template to get default PXE file
        entities.ProvisioningTemplate().build_pxe_default()
        # let's just modify the timeouts to speed things up
        ssh.command(
            "sed -ie 's/TIMEOUT [[:digit:]]\\+/TIMEOUT 1/g' "
            "/var/lib/tftpboot/pxelinux.cfg/default"
        )
        ssh.command(
            "sed -ie '/APPEND initrd/s/$/ fdi.countdown=1 fdi.ssh=1 fdi.rootpw=changeme/' "
            "/var/lib/tftpboot/pxelinux.cfg/default"
        )
        # Create Org and location
        cls.org = entities.Organization().create()
        cls.loc = entities.Location().create()
        # Get default settings values
        cls.default_disco_settings = {
            i.name: i for i in entities.Setting().search(query={'search': 'name~discovery'})
        }

        # Update discovery taxonomies settings
        cls.discovery_loc = copy(cls.default_disco_settings['discovery_location'])
        cls.discovery_loc.value = cls.loc.name
        cls.discovery_loc.update(['value'])
        cls.discovery_org = copy(cls.default_disco_settings['discovery_organization'])
        cls.discovery_org.value = cls.org.name
        cls.discovery_org.update(['value'])

        # Enable flag to auto provision discovered hosts via discovery rules
        cls.discovery_auto = copy(cls.default_disco_settings['discovery_auto'])
        cls.discovery_auto.value = 'true'
        cls.discovery_auto.update(['value'])

        # Flag which shows whether environment is fully configured for
        # discovered host provisioning.
        cls.configured_env = False

    @classmethod
    def tearDownClass(cls):
        """Restore default global setting's values"""
        cls.default_disco_settings['discovery_location'].update(['value'])
        cls.default_disco_settings['discovery_organization'].update(['value'])
        cls.default_disco_settings['discovery_auto'].update(['value'])
        super(DiscoveryTestCase, cls).tearDownClass()

    @pytest.mark.stubbed
    @tier3
    def test_positive_show(self):
        """Show a specific discovered hosts

        :id: f607838d-bbbb-40d6-b58e-e8eea6ef3d1d

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: GET /api/v2/discovered_hosts/:id

        :expectedresults: Selected host is retrieved

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    @tier3
    def test_positive_create(self):
        """Create a discovered hosts

        :id: b8f68ff0-6fda-46a0-aaea-ca2e714e3bec

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: POST /api/v2/discovered_hosts

        :expectedresults: Host should be created successfully

        :CaseAutomation: NotAutomated

        :CaseImportance: Critical
        """

    @tier2
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
        for name in valid_data_list():
            with self.subTest(name):
                result = _create_discovered_host(name)
                discovered_host = entities.DiscoveredHost(id=result['id']).read_json()
                host_name = 'mac{0}'.format(discovered_host['mac'].replace(':', ''))
                self.assertEqual(discovered_host['name'], host_name)

    @pytest.mark.stubbed
    @tier3
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

    @tier3
    def test_positive_provision_pxe_host(self):
        """Provision a pxe-based discovered hosts

        :id: e805b9c5-e8f6-4129-a0e6-ab54e5671ddb

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: PUT /api/v2/discovered_hosts/:id

        :expectedresults: Host should be provisioned successfully

        :CaseImportance: Critical
        """
        if not self.configured_env:
            self.__class__.configured_env = configure_env_for_provision(
                org={'id': self.org.id, 'name': self.org.name},
                loc={'id': self.loc.id, 'name': self.loc.name},
            )
        with LibvirtGuest() as pxe_host:
            hostname = pxe_host.guest_name
            discovered_host = self._assertdiscoveredhost(hostname)
            # Provision just discovered host
            discovered_host.hostgroup = entities.HostGroup(
                id=self.configured_env['hostgroup']['id']
            ).read()
            discovered_host.root_pass = gen_string('alphanumeric')
            discovered_host.update(['hostgroup', 'root_pass'])
            # Assertions
            provisioned_host = entities.Host().search(
                query={
                    'search': 'name={}.{}'.format(
                        discovered_host.name, self.configured_env['domain']['name']
                    )
                }
            )[0]
            assert provisioned_host.subnet.read().name == self.configured_env['subnet']['name']
            assert (
                provisioned_host.operatingsystem.read().ptable[0].read().name
                == self.configured_env['ptable']['name']
            )
            assert (
                provisioned_host.operatingsystem.read().title == self.configured_env['os']['title']
            )
            assert not entities.DiscoveredHost().search(
                query={'search': 'name={}'.format(discovered_host.name)}
            )

    @tier3
    def test_positive_provision_pxe_host_non_admin(self):
        """Provision a pxe-based discovered hosts by non-admin user

        :id: 02144040-6cf6-4251-abaf-b0fad2c83109

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: PUT /api/v2/discovered_hosts/:id

        :expectedresults: Host should be provisioned successfully by non admin user

        :CaseImportance: Critical

        :bz: 1638403
        """
        non_admin = create_org_admin_user(orgs=[self.org.id], locs=[self.loc.id])
        nonadmin_config = get_nailgun_config(non_admin)
        if not self.configured_env:
            self.__class__.configured_env = configure_env_for_provision(
                org={'id': self.org.id, 'name': self.org.name},
                loc={'id': self.loc.id, 'name': self.loc.name},
            )
        with LibvirtGuest() as pxe_host:
            hostname = pxe_host.guest_name
            discovered_host = self._assertdiscoveredhost(hostname, nonadmin_config)
            # Provision just discovered host
            discovered_host.hostgroup = entities.HostGroup(
                nonadmin_config, id=self.configured_env['hostgroup']['id']
            ).read()
            discovered_host.root_pass = gen_string('alphanumeric')
            discovered_host.update(['hostgroup', 'root_pass'])
            # Assertions
            provisioned_host = entities.Host(nonadmin_config).search(
                query={
                    'search': 'name={}.{}'.format(
                        discovered_host.name, self.configured_env['domain']['name']
                    )
                }
            )[0]
            assert provisioned_host.subnet.read().name == self.configured_env['subnet']['name']
            assert (
                provisioned_host.operatingsystem.read().ptable[0].read().name
                == self.configured_env['ptable']['name']
            )
            assert (
                provisioned_host.operatingsystem.read().title == self.configured_env['os']['title']
            )
            assert not entities.DiscoveredHost(nonadmin_config).search(
                query={'search': 'name={}'.format(discovered_host.name)}
            )

    @pytest.mark.stubbed
    @tier3
    def test_positive_delete_pxe_less_host(self):
        """Delete a pxe-less discovered hosts

        :id: e8604ee4-04e9-4bb5-9487-18ab37ea271d

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: DELETE /api/v2/discovered_hosts/:id

        :expectedresults: Discovered Host should be deleted successfully

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    @tier3
    def test_positive_delete_pxe_host(self):
        """Delete a pxe-based discovered hosts

        :id: 2ab2ad88-4470-4d4c-8e0b-5892ad8d675e

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: DELETE /api/v2/discovered_hosts/:id

        :expectedresults: Discovered Host should be deleted successfully

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    @tier3
    def test_positive_auto_provision_pxe_less_host(self):
        """Auto provision a pxe-less host by executing discovery rules

        :id: 80a4be02-517a-4d41-bacc-a3f9dce47bdf

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: POST /api/v2/discovered_hosts/:id/auto_provision

        :expectedresults: Selected Host should be auto-provisioned successfully

        :CaseAutomation: NotAutomated

        :CaseImportance: Critical
        """

    @pytest.mark.stubbed
    @tier3
    def test_positive_auto_provision_pxe_host(self):
        """Auto provision a pxe-based host by executing discovery rules

        :id: c93fd7c9-41ef-4eb5-8042-f72e87e67e10

        :Setup: Provisioning should be configured and a host should be
            discovered

        :Steps: POST /api/v2/discovered_hosts/:id/auto_provision

        :expectedresults: Selected Host should be auto-provisioned successfully

        :CaseAutomation: NotAutomated

        :CaseImportance: Critical
        """

    @pytest.mark.stubbed
    @tier3
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
    @tier3
    def test_positive_refresh_facts_pxe_less_host(self):
        """Refreshing the facts of pxe-less discovered host by adding a new NIC.

        :id: c6ef642e-5eb1-4297-bad1-48f88a1660c6

        :Setup:

            1. Provisioning should be configured and more than one host should
               be discovered via discovery ISO
            2. Add a NIC on discovered host

        :Steps: PUT /api/v2/discovered_hosts/:id/refresh_facts

        :expectedresults: Added Fact should be displayed on refreshing the
            facts

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    @tier3
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

    @pytest.mark.stubbed
    @tier3
    def test_positive_reboot_pxe_host(self):
        """Rebooting a pxe based discovered host

        :id: 69c807f8-5646-4aa6-8b3c-5ecab69560fc

        :Setup: Provisioning should be configured and more than one host should
            be discovered via PXE boot.

        :Steps: PUT /api/v2/discovered_hosts/:id/reboot

        :expectedresults: Selected host should be rebooted successfully

        :CaseAutomation: NotAutomated

        :CaseImportance: Medium
        """

    @pytest.mark.stubbed
    @tier3
    def test_positive_reboot_pxe_less_host(self):
        """Rebooting a pxe-less discovered host

        :id: 2e7bdf3c-fb5d-44da-981d-d4ba9ffaba60

        :Setup: Provisioning should be configured and more than one host should
            be discovered using discovery ISO.

        :Steps: PUT /api/v2/discovered_hosts/:id/reboot

        :expectedresults: Selected host should be rebooted successfully

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    @tier3
    def test_positive_provision_host_with_rule(self):
        """Create a new discovery rule that applies on host to provision

        Set query as (e.g IP=IP_of_discovered_host)

        :id: a5531225-0b5f-4999-925f-4f40f77e20f8

        :Setup: Host should already be discovered

        :expectedresults: Host should reboot and provision

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    @tier3
    def test_positive_provision_multihost_with_rule(self):
        """Create a new discovery rule with (host_limit = 0)
        that applies to multi hosts.
        Set query as cpu_count = 1 OR mem > 500

        :id: 19ce9ac0-e915-41b3-8c2d-2b17e5fbe42a

        :Setup: Multiple hosts should already be discovered in same subnet

        :expectedresults: All Hosts of same subnet should reboot and provision

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    @tier3
    def test_positive_provision_with_rule_priority(self):
        """Create multiple discovery rules with different priority and check
        rule with highest priority executed first

        :id: b91c4979-f8ce-4f6e-9474-9ccd4c3bc793

        :Setup: Multiple hosts should already be discovered

        :expectedresults: Host with lower count have higher priority and that
            rule should be executed first

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    @tier3
    def test_positive_multi_provision_with_rule_limit(self):
        """Create a discovery rule (CPU_COUNT = 2) with host limit 1 and
        provision more than one host with same rule

        :id: 553c8ebf-d1c1-4ac2-9948-d3664a5b450b

        :Setup: Host with two CPUs should already be discovered

        :expectedresults: Rule should only be applied to one discovered host
            and for other rule should already be skipped.

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    @tier3
    def test_positive_provision_with_updated_discovery_rule(self):
        """Update an existing rule and provision a host with it.

        :id: 3fb20e0f-02e9-4158-9744-f583308c4e89

        :Setup: Host should already be discovered

        :expectedresults: User should be able to update the rule and it should
            be applied on discovered host

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    @tier3
    def test_positive_provision_with_updated_hostname_in_rule(self):
        """Update the discovered hostname in existing rule and provision a host
        with it

        :id: aaa1d6ac-0f52-4b1f-9bfe-853169985621

        :Setup: Host should already be discovered

        :expectedresults: The host name should be updated and host should be
            provisioned

        :CaseAutomation: NotAutomated

        :CaseImportance: High
        """
