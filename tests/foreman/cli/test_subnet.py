# -*- encoding: utf-8 -*-
"""Test class for Subnet CLI"""

import random
import re

from ddt import ddt
from fauxfactory import gen_string, gen_integer, gen_ipaddr
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_domain, make_subnet, CLIFactoryError
from robottelo.cli.subnet import Subnet
from robottelo.constants import SUBNET_IPAM_TYPES
from robottelo.decorators import (
    data,
    run_only_on,
    skip_if_bug_open,
)
from robottelo.test import CLITestCase


@run_only_on('sat')
@ddt
class TestSubnet(CLITestCase):
    """Subnet CLI tests."""

    @data(
        gen_string(str_type='alpha'),
        gen_string(str_type='alphanumeric'),
        gen_string(str_type='numeric'),
        gen_string(str_type='latin1'),
        gen_string(str_type='utf8'),
    )
    def test_positive_create_1(self, test_data):
        """@Test: Check if Subnet can be created with random names

        @Feature: Subnet - Create

        @Assert: Subnet is created and has random name

        """
        subnet = make_subnet({'name': test_data})
        self.assertEqual(subnet['name'], test_data)

    @data(
        [gen_integer(min_value=1, max_value=255),
         gen_integer(min_value=1, max_value=255)],
        [gen_integer(min_value=1, max_value=255)] * 2,
        [1, 255],
    )
    def test_positive_create_2(self, pool):
        """@Test: Create subnet with valid address pool

        @Feature: Subnet positive create

        @Assert: Subnet is created and address pool is set

        """
        pool.sort()
        mask = '255.255.255.0'
        network = gen_ipaddr()       # generate pool range from network address
        from_ip = re.sub('\d+$', str(pool[0]), network)
        to_ip = re.sub('\d+$', str(pool[1]), network)
        subnet = make_subnet({
            u'from': from_ip,
            u'mask': mask,
            u'network': network,
            u'to': to_ip,
        })
        self.assertEqual(subnet['from'], from_ip)
        self.assertEqual(subnet['to'], to_ip)

    def test_create_subnet_with_domain(self):
        """@Test: Check if subnet with domain can be created

        @Feature: Subnet - Positive create

        @Assert: Subnet is created and has new domain assigned

        """
        domain = make_domain()
        subnet = make_subnet({'domain-ids': domain['id']})
        self.assertIn(domain['name'], subnet['domains'])

    def test_create_subnet_with_multiple_domains(self):
        """@Test: Check if subnet with different amount of domains can be
        created in the system

        @Feature: Subnet - Positive create

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

    def test_create_subnet_with_gateway(self):
        """@Test: Check if subnet with gateway can be created

        @Feature: Subnet - Positive create

        @Assert: Subnet is created and has gateway assigned

        """
        gateway = gen_ipaddr(ip3=True)
        subnet = make_subnet({'gateway': gateway})
        self.assertIn(gateway, subnet['gateway'])

    @skip_if_bug_open('bugzilla', 1213437)
    @data(
        SUBNET_IPAM_TYPES['dhcp'],
        SUBNET_IPAM_TYPES['internal'],
        SUBNET_IPAM_TYPES['none'],
    )
    def test_create_subnet_with_ipam(self, ipam_type):
        """@Test: Check if subnet with different ipam types can be created

        @Feature: Subnet - Positive create

        @Assert: Subnet is created and correct ipam type is assigned

        @BZ: 1213437

        """
        subnet = make_subnet({'ipam': ipam_type})
        self.assertIn(ipam_type, subnet['ipam'])

    @data(
        {u'name': ''},
        {u'network': '256.0.0.0'},
        {u'network': ''},
        {u'mask': '256.0.0.0'},
        {u'mask': ''},
        {u'mask': '255.0.255.0'}
    )
    def test_negative_create_1(self, options):
        """@Test: Create subnet with invalid or missing required attributes

        @Feature: Subnet create

        @Assert: Subnet is not created

        """
        with self.assertRaises(CLIFactoryError):
            make_subnet(options)

    @data(
        {u'from': gen_integer(min_value=1, max_value=255)},
        {u'to': gen_integer(min_value=1, max_value=255)},
        {u'from': gen_integer(min_value=128, max_value=255),
         u'to': gen_integer(min_value=1, max_value=127)},
        {u'from': 256, u'to': 257},
    )
    def test_negative_create_2(self, pool):
        """@Test: Create subnet with invalid address pool range

        @Feature: Create subnet negative

        @Assert: Subnet is not created

        """
        mask = '255.255.255.0'
        network = gen_ipaddr()
        opts = {u'mask': mask, u'network': network}
        # generate pool range from network address
        for key, val in pool.iteritems():
            opts[key] = re.sub('\d+$', str(val), network)
        with self.assertRaises(CLIFactoryError):
            make_subnet(opts)

    def test_list(self):
        """@Test: Check if Subnet can be listed

        @Feature: Subnet - List

        @Assert: Subnet is listed

        """
        # Fetch current total
        subnets_before = Subnet.list()
        # Make a new subnet
        make_subnet()
        # Fetch total again
        subnets_after = Subnet.list()
        self.assertGreater(len(subnets_after), len(subnets_before))

    @data(
        gen_string(str_type='alpha'),
        gen_string(str_type='alphanumeric'),
        gen_string(str_type='numeric'),
        gen_string(str_type='latin1'),
        gen_string(str_type='utf8'),
    )
    def test_positive_update_1(self, test_name):
        """@Test: Check if Subnet name can be updated

        @Feature: Subnet - Update

        @Assert: Subnet name is updated

        """
        new_subnet = make_subnet()
        # Update the name
        Subnet.update({'id': new_subnet['id'], 'new-name': test_name})
        # Fetch it again
        result = Subnet.info({'id': new_subnet['id']})
        self.assertEqual(result['name'], test_name)
        self.assertNotEqual(result['name'], new_subnet['name'])

    def test_positive_update_2(self):
        """@Test: Check if Subnet network and mask can be updated

        @Feature: Subnet - Update

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

    @data(
        [gen_integer(min_value=1, max_value=255),
         gen_integer(min_value=1, max_value=255)],
        [gen_integer(min_value=1, max_value=255)] * 2,
        [1, 255],
    )
    def test_positive_update_3(self, pool):
        """@Test: Check if Subnet address pool can be updated

        @Feature: Subnet - Update

        @Assert: Subnet address pool is updated

        """
        pool.sort()
        subnet = make_subnet({u'mask': '255.255.255.0'})
        # generate pool range from network address
        ip_from = re.sub('\d+$', str(pool[0]), subnet['network'])
        ip_to = re.sub('\d+$', str(pool[1]), subnet['network'])
        Subnet.update({
            u'from': ip_from,
            u'id': subnet['id'],
            u'to': ip_to,
        })
        # check - subnet is updated
        subnet = Subnet.info({u'id': subnet['id']})
        self.assertEqual(subnet['from'], ip_from)
        self.assertEqual(subnet['to'], ip_to)

    @data(
        {u'name': ''},
        {u'network': '256.0.0.0'},
        {u'network': ''},
        {u'mask': '256.0.0.0'},
        {u'mask': ''},
        {u'mask': '255.0.255.0'}
    )
    def test_negative_update_1(self, options):
        """@Test: Update subnet with invalid or missing required attributes

        @Feature: Subnet - Update

        @Assert: Subnet is not updated

        """
        subnet = make_subnet()
        options['id'] = subnet['id']
        with self.assertRaises(CLIReturnCodeError):
            Subnet.update(options)
        # check - subnet is not updated
        result = Subnet.info({u'id': subnet['id']})
        for key in options.keys():
            self.assertEqual(subnet[key], result[key])

    @data(
        {u'from': gen_integer(min_value=1, max_value=255)},
        {u'to': gen_integer(min_value=1, max_value=255)},
        {u'from': gen_integer(min_value=128, max_value=255),
         u'to': gen_integer(min_value=1, max_value=127)},
        {u'from': 256, u'to': 257},
    )
    def test_negative_update_2(self, options):
        """@Test: Update subnet with invalid address pool

        @Feature: Subnet - Update

        @Assert: Subnet is not updated

        """
        subnet = make_subnet()
        opts = {u'id': subnet['id']}
        # generate pool range from network address
        for key, val in options.iteritems():
            opts[key] = re.sub('\d+$', str(val), subnet['network'])
        with self.assertRaises(CLIReturnCodeError):
            Subnet.update(opts)
        # check - subnet is not updated
        result = Subnet.info({u'id': subnet['id']})
        for key in options.keys():
            self.assertEqual(result[key], subnet[key])

    @data(
        gen_string(str_type='alpha'),
        gen_string(str_type='alphanumeric'),
        gen_string(str_type='numeric'),
        gen_string(str_type='latin1'),
        gen_string(str_type='utf8'),
    )
    def test_positive_delete_1(self, test_name):
        """@Test: Check if Subnet can be deleted

        @Feature: Subnet - Delete

        @Assert: Subnet is deleted

        """
        subnet = make_subnet({'name': test_name})
        # Delete it
        Subnet.delete({'id': subnet['id']})
        # Fetch it again
        with self.assertRaises(CLIReturnCodeError):
            Subnet.info({'id': subnet['id']})
