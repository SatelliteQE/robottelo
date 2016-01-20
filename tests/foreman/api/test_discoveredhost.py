# -*- encoding: utf-8 -*-
"""API Tests for foreman discovery feature"""
from fauxfactory import gen_string, gen_ipaddr, gen_mac
from nailgun import entities
from robottelo.datafactory import valid_data_list
from robottelo.decorators import run_only_on, stubbed, tier2, tier3
from robottelo.test import APITestCase


def _create_discovered_host(name=None, ipaddress=None, discovery_bootif=None):
    """Creates discovered host by uploading few fake facts.

    :param str name: Name of discovered host. If ``None`` then a random
        value will be generated.
    :param str ipaddress: A valid ip address.
        If ``None`` then then a random value will be generated.
    :return: A ``dict`` of ``DiscoveredHost`` facts.
    """
    if name is None:
        name = gen_string('alpha')
    if ipaddress is None:
        ipaddress = gen_ipaddr()
    if discovery_bootif is None:
        discovery_bootif = gen_mac()
    return entities.DiscoveredHost().facts(json={
        u'facts': {
            u'name': name,
            u'ipaddress': ipaddress,
            u'discovery_bootif': discovery_bootif,
        }
    })


class DiscoveryTestCase(APITestCase):
    """Implements tests for foreman discovery feature"""

    @stubbed()
    @tier3
    def test_positive_list_all(self):
        """List all discovered hosts

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured and a host should be
        discovered

        @Steps:

        1. GET /api/v2/discovered_hosts

        @Assert: List of all discovered hosts are retrieved

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_show(self):
        """Show a specific discovered hosts

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured and a host should be
        discovered

        @Steps:

        1. GET /api/v2/discovered_hosts/:id

        @Assert: Selected host is retrieved

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_create(self):
        """Create a discovered hosts

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured and a host should be
        discovered

        @Steps:

        1. POST /api/v2/discovered_hosts

        @Assert: Host should be created successfully

        @Status: Manual
        """

    @tier2
    @run_only_on('sat')
    def test_positive_upload_facts(self):
        """Upload fake facts to create a discovered host

        @Feature: Foreman Discovery

        @Steps:

        1. POST /api/v2/discovered_hosts/facts

        @Assert: Host should be created successfully
        """
        for name in valid_data_list():
            with self.subTest(name):
                host = _create_discovered_host(name)
                host_name = 'mac{0}'.format(host['mac'].replace(':', ''))
                self.assertEqual(host['name'], host_name)

    @stubbed()
    @tier3
    def test_positive_provision(self):
        """Provision a discovered hosts

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured and a host should be
        discovered

        @Steps:

        1. PUT /api/v2/discovered_hosts/:id

        @Assert: Host should be provisioned successfully

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_delete(self):
        """Delete a discovered hosts

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured and a host should be
        discovered

        @Steps:

        1. DELETE /api/v2/discovered_hosts/:id

        @Assert: Discovered Host should be deleted successfully

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_auto_provision(self):
        """Auto provision a host by executing discovery rules

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured and a host should be
        discovered

        @Steps:

        1. POST /api/v2/discovered_hosts/:id/auto_provision

        @Assert: Selected Host should be auto-provisioned successfully

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_auto_provision_all(self):
        """Auto provision all host by executing discovery rules

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured and more than one host should
        be discovered

        @Steps:

        1. POST /api/v2/discovered_hosts/auto_provision_all

        @Assert: All discovered hosts should be auto-provisioned successfully

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_refresh_facts(self):
        """Refreshing the facts of discovered host

        @Feature: Foreman Discovery

        @Setup:

        1. Provisioning should be configured and more than one host should
        be discovered

        2. Add a NIC on discovered host

        @Steps:

        1. PUT /api/v2/discovered_hosts/:id/refresh_facts

        @Assert: Added Fact should be displayed on refreshing the facts

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_reboot(self):
        """Rebooting a discovered host

        @Feature: Foreman Discovery

        @Setup: Provisioning should be configured and more than one host should
        be discovered

        @Steps:

        1. PUT /api/v2/discovered_hosts/:id/reboot

        @Assert: Selected host should be rebooted successfully

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_create_discovery_rule_with_simple_query(self):
        """Create a new discovery rule

        Set query as (e.g IP=IP_of_discovered_host)

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: Host should reboot and provision

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_create_discovery_rule_with_complex_query(self):
        """Create a new discovery rule with (host_limit = 0)
        that applies to multi hosts.
        Set query as cpu_count = 1 OR mem > 500

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: All Hosts of same subnet should reboot and provision

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_create_discovery_rule_with_priority(self):
        """Create multiple discovery rules with different priority

        @Feature: Foreman Discovery

        @Setup: Multiple hosts should already be discovered

        @Assert: Host with lower count have higher priority
        and that rule should be executed first

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_create_discovery_rule_with_host_limit(self):
        """Create a discovery rule (CPU_COUNT = 2) with host limit 1 and
        provision more than one host with same rule

        @Feature: Foreman Discovery

        @Setup: Host with two CPUs should already be discovered

        @Assert: Rule should only be applied to one discovered host and for
        other rule should already be skipped.

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_update_discovery_rule_execute(self):
        """Update an existing rule and execute it

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: User should be able to update the rule and it should be
        executed on discovered host

        @Status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_update_discovery_rule_provision(self):
        """Update the discovered host name and provision it

        @Feature: Foreman Discovery

        @Setup: Host should already be discovered

        @Assert: The host name should be updated and host should be provisioned

        @Status: Manual
        """
