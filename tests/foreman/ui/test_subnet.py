# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Subnet UI"""

from ddt import ddt
from fauxfactory import FauxFactory
from robottelo import entities
from nose.plugins.attrib import attr
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.common.helpers import generate_ipaddr, generate_strings_list
from robottelo.ui.factory import make_subnet
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class Subnet(UITestCase):
    """Implements Subnet tests in UI"""
    org_name = None
    loc_name = None
    org_id = None
    loc_id = None

    def setUp(self):
        super(Subnet, self).setUp()
        # Make sure to use the Class' org_name instance
        if Subnet.org_name is None and Subnet.loc_name is None:
            org_name = FauxFactory.generate_string("alpha", 8)
            loc_name = FauxFactory.generate_string("alpha", 8)
            org_attrs = entities.Organization(name=org_name).create()
            loc_attrs = entities.Location(name=loc_name).create()
            Subnet.org_name = org_attrs['name']
            Subnet.org_id = org_attrs['id']
            Subnet.loc_name = loc_attrs['name']
            Subnet.loc_id = loc_attrs['id']

    @attr('ui', 'subnet', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_create_subnet_1(self, name):
        """@Test: Create new subnet

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created

        """
        network = generate_ipaddr(ip3=True)
        mask = "255.255.255.0"
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name=name))

    @skip_if_bug_open('bugzilla', 1123815)
    @attr('ui', 'subnet', 'implemented')
    @data(
        FauxFactory.generate_string('alphanumeric', 255),
        FauxFactory.generate_string('alpha', 255),
        FauxFactory.generate_string('numeric', 255),
        FauxFactory.generate_string('latin1', 255),
        FauxFactory.generate_string('utf8', 255)
    )
    def test_create_subnet_2(self, name):
        """@Test: Create new subnet with 255 characters in name

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created with 255 chars

        """
        network = generate_ipaddr(ip3=True)
        mask = "255.255.255.0"
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name=name))

    def test_create_subnet_3(self):
        """@Test: Create new subnet and associate domain with it

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created with domain associated

        """
        strategy, value = common_locators["entity_deselect"]
        name = FauxFactory.generate_string("alpha", 4)
        network = generate_ipaddr(ip3=True)
        mask = "255.255.255.0"
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
                (strategy, value % domain_name))
            self.assertIsNotNone(element)

    @skip_if_bug_open('bugzilla', 1123815)
    @attr('ui', 'subnet', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_create_subnet_negative_1(self, name):
        """@Test: Create new subnet with 256 characters in name

        @Feature: Subnet - Negative Create

        @Assert: Subnet is not created with 256 chars

        """
        network = generate_ipaddr(ip3=True)
        mask = "255.255.255.0"
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.assertIsNone(self.subnet.search_subnet(subnet_name=name))

    @data("", " ")
    def test_create_subnet_negative_2(self, name):
        """@Test: Create new subnet with whitespace and blank in name.

        @Feature: Subnet - Negative Create.

        @Assert: Subnet is not created.

        """

        network = generate_ipaddr(ip3=True)
        mask = "255.255.255.0"
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.assertIsNone(self.subnet.search_subnet(subnet_name=name))

    def test_create_subnet_negative_4(self):
        """@Test: Create new subnet with negative values

        @Feature: Subnet - Negative Create.

        @Assert: Subnet is not created with negative values

        """
        name = FauxFactory.generate_string("alpha", 8)
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
            network = session.nav.wait_until_element(
                locators["subnet.network_haserror"])
            mask = session.nav.wait_until_element(
                locators["subnet.mask_haserror"])
            gateway = session.nav.wait_until_element(
                locators["subnet.gateway_haserror"])
            primarydns = session.nav.wait_until_element(
                locators["subnet.dnsprimary_haserror"])
            secondarydns = session.nav.wait_until_element(
                locators["subnet.dnssecondary_haserror"])
            self.assertIsNotNone(network)
            self.assertIsNotNone(mask)
            self.assertIsNotNone(gateway)
            self.assertIsNotNone(primarydns)
            self.assertIsNotNone(secondarydns)

    @attr('ui', 'subnet', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_remove_subnet_1(self, name):
        """@Test: Delete a subnet

        @Feature: Subnet - Positive Delete

        @Assert: Subnet is deleted

        """
        network = generate_ipaddr(ip3=True)
        mask = "255.255.255.0"
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.subnet.delete(name, True)
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators["notif.success"]))
            self.assertIsNone(self.subnet.search_subnet(
                subnet_name=name, timeout=5))

    @attr('ui', 'subnet', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_remove_subnet_2(self, name):
        """@Test: Delete subnet.

        Attempt to delete subnet but cancel in the confirmation dialog box.

        @Feature: Subnet - Negative Delete

        @Assert: Subnet is not deleted

        """
        network = generate_ipaddr(ip3=True)
        mask = "255.255.255.0"
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.subnet.delete(name, False)
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name=name,
                                                           timeout=5))

    @attr('ui', 'subnet', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_update_subnet_1(self, name):
        """@Test: Update Subnet name

        @Feature: Subnet - Positive Update

        @Assert: Subnet name is updated

        """
        network = generate_ipaddr(ip3=True)
        mask = "255.255.255.0"
        new_name = FauxFactory.generate_string("alpha", 10)
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.subnet.update(name, new_subnet_name=new_name)
            result_object = self.subnet.search_subnet(new_name)
            self.assertEqual(new_name, result_object['name'])

    @attr('ui', 'subnet', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_update_subnet_2(self, name):
        """@Test: Update Subnet network

        @Feature: Subnet - Positive Update

        @Assert: Subnet network is updated

        """
        network = generate_ipaddr(ip3=True)
        mask = "255.255.255.0"
        new_network = generate_ipaddr(ip3=True)
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.subnet.update(name, new_subnet_network=new_network)
            result_object = self.subnet.search_subnet(name)
            self.assertEqual(new_network, result_object['network'])

    @attr('ui', 'subnet', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_update_subnet_3(self, name):
        """@Test: Update Subnet mask

        @Feature: Subnet - Positive Update

        @Assert: Subnet mask is updated

        """
        network = generate_ipaddr(ip3=True)
        mask = "255.255.255.0"
        new_mask = "128.128.128.0"
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            self.subnet.update(name, new_subnet_mask=new_mask)
            result_object = self.subnet.search_subnet(name)
            self.assertEqual(new_mask, result_object['mask'])

    @attr('ui', 'subnet', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_search_subnet_1(self, name):
        """@Test: Search Subnet with Subnet name

        @Feature: Subnet - Positive Search

        @Assert: Subnet is found

        """
        network = generate_ipaddr(ip3=True)
        mask = "255.255.255.0"
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=name, subnet_network=network,
                        subnet_mask=mask)
            result_object = self.subnet.search_subnet(name)
            self.assertEqual(name, result_object['name'])
            self.assertEqual(network, result_object['network'])
            self.assertEqual(mask, result_object['mask'])

    def test_search_subnet_2(self):
        """@Test: Search for a non-existent subnet name

        @Feature: Subnet - Negative Search

        @Assert: Subnet name is not found

        """
        subnet_name = FauxFactory.generate_string("alpha", 8)
        with Session(self.browser) as session:
            session.nav.go_to_subnets()  # go to subnet page
            self.assertIsNone(self.subnet.search_subnet(subnet_name))
