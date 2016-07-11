# -*- encoding: utf-8 -*-
"""Test class for Subnet CLI

@Requirement: Subnet

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

import random
import re

from fauxfactory import gen_integer, gen_ipaddr
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_domain, make_subnet, CLIFactoryError
from robottelo.cli.subnet import Subnet
from robottelo.constants import SUBNET_IPAM_TYPES
from robottelo.datafactory import filtered_datapoint, valid_data_list
from robottelo.decorators import run_only_on, tier1
from robottelo.test import CLITestCase


@filtered_datapoint
def valid_addr_pools():
    """Returns a list of valid address pools"""
    return [
        [gen_integer(min_value=1, max_value=255),
         gen_integer(min_value=1, max_value=255)],
        [gen_integer(min_value=1, max_value=255)] * 2,
        [1, 255],
    ]


@filtered_datapoint
def invalid_addr_pools():
    """Returns a list of invalid address pools"""
    return [
        {u'from': gen_integer(min_value=1, max_value=255)},
        {u'to': gen_integer(min_value=1, max_value=255)},
        {u'from': gen_integer(min_value=128, max_value=255),
         u'to': gen_integer(min_value=1, max_value=127)},
        {u'from': 256, u'to': 257},
    ]


@filtered_datapoint
def invalid_missing_attributes():
    """Returns a list of invalid missing attributes"""
    return [
        {u'name': ''},
        {u'network': '256.0.0.0'},
        {u'network': ''},
        {u'mask': '256.0.0.0'},
        {u'mask': ''},
        {u'mask': '255.0.255.0'}
    ]


class SubnetTestCase(CLITestCase):
    """Subnet CLI tests."""

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Check if Subnet can be created with random names

        @id: 99cda3eb-3912-461b-83bd-f906b78eeca0

        @Assert: Subnet is created and has random name
        """
        for name in valid_data_list():
            with self.subTest(name):
                subnet = make_subnet({'name': name})
                self.assertEqual(subnet['name'], name)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_address_pool(self):
        """Create subnet with valid address pool

        @id: d74a52a7-df56-44ef-89a3-081c14e81e43

        @Assert: Subnet is created and address pool is set
        """
        for pool in valid_addr_pools():
            with self.subTest(pool):
                pool.sort()
                mask = '255.255.255.0'
                # generate pool range from network address
                network = gen_ipaddr()
                from_ip = re.sub(r'\d+$', str(pool[0]), network)
                to_ip = re.sub(r'\d+$', str(pool[1]), network)
                subnet = make_subnet({
                    u'from': from_ip,
                    u'mask': mask,
                    u'network': network,
                    u'to': to_ip,
                })
                self.assertEqual(subnet['from'], from_ip)
                self.assertEqual(subnet['to'], to_ip)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_domain(self):
        """Check if subnet with domain can be created

        @id: 7ce7b139-d2b7-44f4-9c1a-1bd591f95334

        @Assert: Subnet is created and has new domain assigned
        """
        domain = make_domain()
        subnet = make_subnet({'domain-ids': domain['id']})
        self.assertIn(domain['name'], subnet['domains'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_domains(self):
        """Check if subnet with different amount of domains can be
        created in the system

        @id: e81ddec5-38b0-4c42-b89b-5cf2af580d39

        @Assert: Subnet is created and has new domains assigned
        """
        domains_amount = random.randint(3, 5)
        domains = [make_domain() for _ in range(domains_amount)]
        subnet = make_subnet({
            'domain-ids': [domain['id'] for domain in domains],
        })
        self.assertEqual(len(subnet['domains']), domains_amount)
        for domain in domains:
            self.assertIn(domain['name'], subnet['domains'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_gateway(self):
        """Check if subnet with gateway can be created

        @id: 483c0d1d-c542-4be5-8c56-27b2a09db54a

        @Assert: Subnet is created and has gateway assigned
        """
        gateway = gen_ipaddr(ip3=True)
        subnet = make_subnet({'gateway': gateway})
        self.assertIn(gateway, subnet['gateway'])

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_ipam(self):
        """Check if subnet with different ipam types can be created

        @id: ba4c66fd-50e6-441d-acc2-6ab39d8439d2

        @Assert: Subnet is created and correct ipam type is assigned
        """
        for ipam_type in (SUBNET_IPAM_TYPES['dhcp'],
                          SUBNET_IPAM_TYPES['internal'],
                          SUBNET_IPAM_TYPES['none']):
            with self.subTest(ipam_type):
                subnet = make_subnet({'ipam': ipam_type})
                self.assertIn(ipam_type, subnet['ipam'])

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_attributes(self):
        """Create subnet with invalid or missing required attributes

        @id: de468dd3-7ba8-463e-881a-fd1cb3cfc7b6

        @Assert: Subnet is not created
        """
        for options in invalid_missing_attributes():
            with self.subTest(options):
                with self.assertRaises(CLIFactoryError):
                    make_subnet(options)

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_address_pool(self):
        """Create subnet with invalid address pool range

        @id: c7824327-b5ef-4f95-bd4b-ba4eff73551c

        @Assert: Subnet is not created
        """
        mask = '255.255.255.0'
        network = gen_ipaddr()
        for pool in invalid_addr_pools():
            with self.subTest(pool):
                opts = {u'mask': mask, u'network': network}
                # generate pool range from network address
                for key, val in pool.iteritems():
                    opts[key] = re.sub(r'\d+$', str(val), network)
                with self.assertRaises(CLIFactoryError):
                    make_subnet(opts)

    @run_only_on('sat')
    @tier1
    def test_positive_list(self):
        """Check if Subnet can be listed

        @id: 2ee376f7-9dd9-4b46-b414-801197d5455c

        @Assert: Subnet is listed
        """
        # Fetch current total
        subnets_before = Subnet.list()
        # Make a new subnet
        make_subnet()
        # Fetch total again
        subnets_after = Subnet.list()
        self.assertGreater(len(subnets_after), len(subnets_before))

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Check if Subnet name can be updated

        @id: 34533e6c-7081-4b13-99bd-bd57533e05c0

        @Assert: Subnet name is updated
        """
        new_subnet = make_subnet()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                Subnet.update({'id': new_subnet['id'], 'new-name': new_name})
                result = Subnet.info({'id': new_subnet['id']})
                self.assertEqual(result['name'], new_name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_network_mask(self):
        """Check if Subnet network and mask can be updated

        @id: 6a8d7750-71f1-4cd8-bf90-f2eac457c3b4

        @Assert: Subnet network and mask are updated
        """
        network = gen_ipaddr()
        mask = '255.255.255.0'
        subnet = make_subnet({
            u'mask': mask,
            u'network': network,
        })
        new_network = gen_ipaddr()
        new_mask = '255.255.192.0'
        Subnet.update({
            u'id': subnet['id'],
            u'mask': new_mask,
            u'network': new_network,
        })
        # check - subnet is updated
        subnet = Subnet.info({u'id': subnet['id']})
        self.assertEqual(subnet['network'], new_network)
        self.assertEqual(subnet['mask'], new_mask)

    @run_only_on('sat')
    @tier1
    def test_positive_update_address_pool(self):
        """Check if Subnet address pool can be updated

        @id: 18ced88f-d62e-4e15-8b7b-0a08c4ef239b

        @Assert: Subnet address pool is updated
        """
        subnet = make_subnet({u'mask': '255.255.255.0'})
        for pool in valid_addr_pools():
            with self.subTest(pool):
                pool.sort()
                # generate pool range from network address
                ip_from = re.sub(r'\d+$', str(pool[0]), subnet['network'])
                ip_to = re.sub(r'\d+$', str(pool[1]), subnet['network'])
                Subnet.update({
                    u'from': ip_from,
                    u'id': subnet['id'],
                    u'to': ip_to,
                })
                subnet = Subnet.info({u'id': subnet['id']})
                self.assertEqual(subnet['from'], ip_from)
                self.assertEqual(subnet['to'], ip_to)

    @run_only_on('sat')
    @tier1
    def test_negative_update_attributes(self):
        """Update subnet with invalid or missing required attributes

        @id: ab60372e-cef7-4495-bd66-68e7dbece475

        @Assert: Subnet is not updated
        """
        subnet = make_subnet()
        for options in invalid_missing_attributes():
            with self.subTest(options):
                options['id'] = subnet['id']
                with self.assertRaises(CLIReturnCodeError):
                    Subnet.update(options)
                    # check - subnet is not updated
                    result = Subnet.info({u'id': subnet['id']})
                    for key in options.keys():
                        self.assertEqual(subnet[key], result[key])

    @run_only_on('sat')
    @tier1
    def test_negative_update_address_pool(self):
        """Update subnet with invalid address pool

        @id: d0a857b4-be10-4b5d-86d4-43cf99c11619

        @Assert: Subnet is not updated
        """
        subnet = make_subnet()
        for options in invalid_addr_pools():
            with self.subTest(options):
                opts = {u'id': subnet['id']}
                # generate pool range from network address
                for key, val in options.iteritems():
                    opts[key] = re.sub(r'\d+$', str(val), subnet['network'])
                with self.assertRaises(CLIReturnCodeError):
                    Subnet.update(opts)
                # check - subnet is not updated
                result = Subnet.info({u'id': subnet['id']})
                for key in options.keys():
                    self.assertEqual(result[key], subnet[key])

    @run_only_on('sat')
    @tier1
    def test_positive_delete_by_id(self):
        """Check if Subnet can be deleted

        @id: ad269df8-4bb2-46a5-9c82-010a80087408

        @Assert: Subnet is deleted
        """
        for name in valid_data_list():
            with self.subTest(name):
                subnet = make_subnet({'name': name})
                Subnet.delete({'id': subnet['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Subnet.info({'id': subnet['id']})
