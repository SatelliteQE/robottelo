# -*- encoding: utf-8 -*-
"""Test class for Subnet UI"""

from ddt import ddt
from fauxfactory import gen_ipaddr, gen_netmask, gen_string
from robottelo import entities
from robottelo.common.decorators import (
    data, run_only_on, skip_if_bug_open, bz_bug_is_open)
from robottelo.common.helpers import generate_strings_list
from robottelo.ui.factory import make_subnet
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class Subnet(UITestCase):
    """Implements Subnet tests in UI"""

    @data(*generate_strings_list(len1=8))
    def test_create_subnet_1(self, name):
        """@Test: Create new subnet

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created

        """
        network = gen_ipaddr(ip3=True)
        mask = gen_netmask()
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name=name))

    @skip_if_bug_open('bugzilla', 1123815)
    @data(
        {'name': gen_string('alphanumeric', 255)},
        {'name': gen_string('alpha', 255)},
        {'name': gen_string('numeric', 255)},
        {'name': gen_string('latin1', 255)},
        {'name': gen_string('utf8', 255),
         u'bz-bug': 1180066}
    )
    def test_create_subnet_2(self, test_data):
        """@Test: Create new subnet with 255 characters in name

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created with 255 chars

        """
        bug_id = test_data.pop('bz-bug', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))

        network = gen_ipaddr(ip3=True)
        mask = gen_netmask()
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=test_data['name'],
                        subnet_network=network, subnet_mask=mask)
            self.assertIsNotNone(
                self.subnet.search_subnet(subnet_name=test_data['name']))

    def test_create_subnet_3(self):
        """@Test: Create new subnet and associate domain with it

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created with domain associated

        """
        strategy1, value1 = common_locators["entity_deselect"]
        strategy2, value2 = common_locators["entity_checkbox"]
        name = gen_string("alpha", 4)
        network = gen_ipaddr(ip3=True)
        mask = gen_netmask()
        domain_name = entities.Domain().create()['name']
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask, domains=[domain_name])
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name=name))
            session.nav.search_entity(
                name, locators['subnet.display_name']).click()
            session.nav.wait_until_element(
                tab_locators["subnet.tab_domain"]).click()
            element = session.nav.wait_until_element(
                (strategy1, value1 % domain_name))
            checkbox_element = session.nav.wait_until_element(
                (strategy2, value2 % domain_name))
            # Depending upon the number of domains either, checkbox or
            # selection list appears.
            if element:
                self.assertIsNotNone(element)
            elif checkbox_element:
                self.assertTrue(checkbox_element.is_selected())
            else:
                self.assertIsNotNone()

    @skip_if_bug_open('bugzilla', 1123815)
    @data(*generate_strings_list(len1=256))
    def test_create_subnet_negative_1(self, name):
        """@Test: Create new subnet with 256 characters in name

        @Feature: Subnet - Negative Create

        @Assert: Subnet is not created with 256 chars

        """
        locator = common_locators["haserror"]
        network = gen_ipaddr(ip3=True)
        mask = gen_netmask()
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            error_element = session.nav.wait_until_element(locator)
            self.assertIsNotNone(error_element)

    @data("", " ")
    def test_create_subnet_negative_2(self, name):
        """@Test: Create new subnet with whitespace and blank in name.

        @Feature: Subnet - Negative Create.

        @Assert: Subnet is not created.

        """
        locator = common_locators["haserror"]
        network = gen_ipaddr(ip3=True)
        mask = gen_netmask()
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            error_element = session.nav.wait_until_element(locator)
            self.assertIsNotNone(error_element)

    def test_create_subnet_negative_4(self):
        """@Test: Create new subnet with negative values

        @Feature: Subnet - Negative Create.

        @Assert: Subnet is not created with negative values

        """
        name = gen_string("alpha", 8)
        network = "292.256.256.0"
        mask = "292.292.292.0"
        gateway = "292.256.256.254"
        primarydns = "292.256.256.2"
        secondarydns = "292.256.256.3"
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask, subnet_gateway=gateway,
                        subnet_primarydns=primarydns,
                        subnet_secondarydns=secondarydns)
            network_element = session.nav.wait_until_element(
                locators["subnet.network_haserror"])
            mask_element = session.nav.wait_until_element(
                locators["subnet.mask_haserror"])
            gateway_element = session.nav.wait_until_element(
                locators["subnet.gateway_haserror"])
            primarydns_element = session.nav.wait_until_element(
                locators["subnet.dnsprimary_haserror"])
            secondarydns_element = session.nav.wait_until_element(
                locators["subnet.dnssecondary_haserror"])
            self.assertIsNotNone(network_element)
            self.assertIsNotNone(mask_element)
            self.assertIsNotNone(gateway_element)
            self.assertIsNotNone(primarydns_element)
            self.assertIsNotNone(secondarydns_element)

    @data(*generate_strings_list(len1=8))
    def test_remove_subnet_1(self, name):
        """@Test: Delete a subnet

        @Feature: Subnet - Positive Delete

        @Assert: Subnet is deleted

        """
        network = gen_ipaddr(ip3=True)
        mask = gen_netmask()
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.subnet.delete(name, True)
            self.assertIsNone(self.subnet.search_subnet(
                subnet_name=name, timeout=5))

    @data(*generate_strings_list(len1=8))
    def test_remove_subnet_2(self, name):
        """@Test: Delete subnet.

        Attempt to delete subnet but cancel in the confirmation dialog box.

        @Feature: Subnet - Negative Delete

        @Assert: Subnet is not deleted

        """
        network = gen_ipaddr(ip3=True)
        mask = gen_netmask()
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.subnet.delete(name, False)
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name=name,
                                                           timeout=5))

    @data(*generate_strings_list(len1=8))
    def test_update_subnet_1(self, name):
        """@Test: Update Subnet name

        @Feature: Subnet - Positive Update

        @Assert: Subnet name is updated

        """
        network = gen_ipaddr(ip3=True)
        mask = gen_netmask()
        new_name = gen_string("alpha", 10)
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.subnet.update(name, new_subnet_name=new_name)
            result_object = self.subnet.search_subnet(new_name)
            self.assertEqual(new_name, result_object['name'])

    @data(*generate_strings_list(len1=8))
    def test_update_subnet_2(self, name):
        """@Test: Update Subnet network

        @Feature: Subnet - Positive Update

        @Assert: Subnet network is updated

        """
        network = gen_ipaddr(ip3=True)
        mask = gen_netmask()
        new_network = gen_ipaddr(ip3=True)
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.subnet.update(name, new_subnet_network=new_network)
            result_object = self.subnet.search_subnet(name)
            self.assertEqual(new_network, result_object['network'])

    @data(*generate_strings_list(len1=8))
    def test_update_subnet_3(self, name):
        """@Test: Update Subnet mask

        @Feature: Subnet - Positive Update

        @Assert: Subnet mask is updated

        """
        network = gen_ipaddr(ip3=True)
        mask = gen_netmask(1, 15)
        new_mask = gen_netmask(16, 31)
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.subnet.update(name, new_subnet_mask=new_mask)
            result_object = self.subnet.search_subnet(name)
            self.assertEqual(new_mask, result_object['mask'])

    @data(*generate_strings_list(len1=8))
    def test_search_subnet_1(self, name):
        """@Test: Search Subnet with Subnet name

        @Feature: Subnet - Positive Search

        @Assert: Subnet is found

        """
        network = gen_ipaddr(ip3=True)
        mask = gen_netmask()
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            result_object = self.subnet.search_subnet(name)
            self.assertEqual(name, result_object['name'])
            self.assertEqual(network, result_object['network'])
            self.assertEqual(mask, result_object['mask'])
