# -*- encoding: utf-8 -*-
"""Test class for Subnet CLI"""

import random
import re

from ddt import ddt
from fauxfactory import gen_string, gen_integer, gen_ipaddr
from robottelo.cli.factory import make_domain, make_subnet, CLIFactoryError
from robottelo.cli.subnet import Subnet
from robottelo.constants import SUBNET_IPAM_TYPES
from robottelo.decorators import (
    bz_bug_is_open,
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
        try:
            subnet = make_subnet({'name': test_data})
        except CLIFactoryError as err:
            self.fail(err)

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
        try:
            subnet = make_subnet({
                u'mask': mask,
                u'network': network,
                u'from': from_ip,
                u'to': to_ip,
            })
        except CLIFactoryError as err:
            self.fail(err)
        self.assertEqual(subnet['from'], from_ip)
        self.assertEqual(subnet['to'], to_ip)

    def test_create_subnet_with_domain(self):
        """@Test: Check if subnet with domain can be created

        @Feature: Subnet - Positive create

        @Assert: Subnet is created and has new domain assigned

        """
        try:
            domain = make_domain()
            subnet = make_subnet({'domain-ids': domain['id']})
        except CLIFactoryError as err:
            self.fail(err)
        self.assertIn(domain['name'], subnet['domains'])

    def test_create_subnet_with_multiple_domains(self):
        """@Test: Check if subnet with different amount of domains can be
        created in the system

        @Feature: Subnet - Positive create

        @Assert: Subnet is created and has new domains assigned

        """
        try:
            domains_amount = random.randint(3, 5)
            domains = [make_domain() for _ in range(domains_amount)]
            subnet = make_subnet({
                'domain-ids': [domain['id'] for domain in domains],
            })
        except CLIFactoryError as err:
            self.fail(err)
        self.assertEqual(len(subnet['domains']), domains_amount)
        for domain in domains:
            self.assertIn(domain['name'], subnet['domains'])

    def test_create_subnet_with_gateway(self):
        """@Test: Check if subnet with gateway can be created

        @Feature: Subnet - Positive create

        @Assert: Subnet is created and has gateway assigned

        """
        try:
            gateway = gen_ipaddr(ip3=True)
            subnet = make_subnet({'gateway': gateway})
        except CLIFactoryError as err:
            self.fail(err)
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
        try:
            subnet = make_subnet({'ipam': ipam_type})
        except CLIFactoryError as err:
            self.fail(err)
        self.assertIn(ipam_type, subnet['ipam'])

    @data(
        {u'name': ''},
        {u'network': '256.0.0.0'},
        {u'network': ''},
        {u'mask': '256.0.0.0'},
        {u'mask': ''},
        {u'mask': '255.0.255.0', u'bz-bug': 1136088}
    )
    def test_negative_create_1(self, options):
        """@Test: Create subnet with invalid or missing required attributes

        @Feature: Subnet create

        @Assert: Subnet is not created

        """
        bug_id = options.pop('bz-bug', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))

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
        result = Subnet.list()
        total_subnet = len(result.stdout)

        # Make a new subnet
        try:
            make_subnet()
        except CLIFactoryError as err:
            self.fail(err)

        # Fetch total again
        result = Subnet.list()
        self.assertGreater(len(result.stdout), total_subnet)

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
        try:
            new_subnet = make_subnet()
        except CLIFactoryError as err:
            self.fail(err)

        # Update the name
        result = Subnet.update({'id': new_subnet['id'], 'new-name': test_name})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch it again
        result = Subnet.info({'id': new_subnet['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(result.stdout['name'], test_name)
        self.assertNotEqual(result.stdout['name'], new_subnet['name'])

    def test_positive_update_2(self):
        """@Test: Check if Subnet network and mask can be updated

        @Feature: Subnet - Update

        @Assert: Subnet network and mask are updated

        """

        network = gen_ipaddr()
        mask = '255.255.255.0'
        try:
            subnet = make_subnet({
                u'network': network,
                u'mask': mask,
            })
        except CLIFactoryError as err:
            self.fail(err)
        new_network = gen_ipaddr()
        new_mask = '255.255.192.0'
        result = Subnet.update({
            u'id': subnet['id'],
            u'network': new_network,
            u'mask': new_mask,
        })
        self.assertEqual(result.return_code, 0)

        # check - subnet is updated
        result = Subnet.info({u'id': subnet['id']})
        self.assertEqual(result.stdout['network'], new_network)
        self.assertEqual(result.stdout['mask'], new_mask)

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
        try:
            subnet = make_subnet({u'mask': '255.255.255.0'})
        except CLIFactoryError as err:
            self.fail(err)
        # generate pool range from network address
        ip_from = re.sub('\d+$', str(pool[0]), subnet['network'])
        ip_to = re.sub('\d+$', str(pool[1]), subnet['network'])
        result = Subnet.update({
            u'id': subnet['id'],
            u'from': ip_from,
            u'to': ip_to,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # check - subnet is updated
        result = Subnet.info({u'id': subnet['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['from'], ip_from)
        self.assertEqual(result.stdout['to'], ip_to)

    @data(
        {u'name': ''},
        {u'network': '256.0.0.0'},
        {u'network': ''},
        {u'mask': '256.0.0.0'},
        {u'mask': ''},
        {u'mask': '255.0.255.0', u'bz-bug': 1136088}
    )
    def test_negative_update_1(self, options):
        """@Test: Update subnet with invalid or missing required attributes

        @Feature: Subnet - Update

        @Assert: Subnet is not updated

        """

        bug_id = options.pop('bz-bug', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))

        try:
            subnet = make_subnet()
        except CLIFactoryError as err:
            self.fail(err)
        options['id'] = subnet['id']
        result = Subnet.update(options)
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

        # check - subnet is not updated
        result = Subnet.info({u'id': subnet['id']})
        for key in options.keys():
            self.assertEqual(subnet[key], result.stdout[key])

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
        try:
            subnet = make_subnet()
        except CLIFactoryError as err:
            self.fail(err)

        opts = {u'id': subnet['id']}
        # generate pool range from network address
        for key, val in options.iteritems():
            opts[key] = re.sub('\d+$', str(val), subnet['network'])
        result = Subnet.update(opts)
        self.assertNotEqual(result.return_code, 0)

        # check - subnet is not updated
        result = Subnet.info({u'id': subnet['id']})
        for key in options.keys():
            self.assertEqual(result.stdout[key], subnet[key])

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
        try:
            subnet = make_subnet({'name': test_name})
        except CLIFactoryError as err:
            self.fail(err)

        # Delete it
        result = Subnet.delete({'id': subnet['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch it again
        result = Subnet.info({'id': subnet['id']})
        self.assertGreater(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)
