# -*- encoding: utf-8 -*-
"""Test class for Subnet UI"""

from ddt import ddt, data
from fauxfactory import gen_ipaddr, gen_netmask, gen_string
from nailgun import entities
from robottelo.decorators import bz_bug_is_open, run_only_on
from robottelo.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_subnet
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@ddt
class Subnet(UITestCase):
    """Implements Subnet tests in UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(Subnet, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @data(*generate_strings_list(len1=8))
    @run_only_on('sat')
    def test_create_subnet_with_different_names(self, name):
        """@Test: Create new subnet

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created

        """
        with Session(self.browser) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
            )
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name=name))

    @data(
        {'name': gen_string('alphanumeric', 255)},
        {'name': gen_string('alpha', 255)},
        {'name': gen_string('numeric', 255)},
        {'name': gen_string('latin1', 255)},
        {'name': gen_string('utf8', 255),
         u'bz-bug': 1180066}
    )
    @run_only_on('sat')
    def test_create_subnet_with_long_strings(self, test_data):
        """@Test: Create new subnet with 255 characters in name

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created with 255 chars

        """
        bug_id = test_data.pop('bz-bug', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))

        with Session(self.browser) as session:
            make_subnet(
                session,
                subnet_name=test_data['name'],
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
            )
            self.assertIsNotNone(
                self.subnet.search_subnet(subnet_name=test_data['name']))

    @run_only_on('sat')
    def test_create_subnet_with_domain(self):
        """@Test: Create new subnet and associate domain with it

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created with domain associated

        """
        strategy1, value1 = common_locators['entity_deselect']
        strategy2, value2 = common_locators['entity_checkbox']
        name = gen_string('alpha', 4)
        domain = entities.Domain(
            organization=[self.organization]
        ).create()
        with Session(self.browser) as session:
            make_subnet(
                session,
                org=self.organization.name,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
                domains=[domain.name],
            )
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name=name))
            session.nav.search_entity(
                name, locators['subnet.display_name']).click()
            session.nav.click(tab_locators['subnet.tab_domain'])
            element = session.nav.wait_until_element(
                (strategy1, value1 % domain.name))
            checkbox_element = session.nav.wait_until_element(
                (strategy2, value2 % domain.name))
            # Depending upon the number of domains either, checkbox or
            # selection list appears.
            if element:
                self.assertIsNotNone(element)
            elif checkbox_element:
                self.assertTrue(checkbox_element.is_selected())
            else:
                self.assertIsNotNone()

    @data(*generate_strings_list(len1=256))
    @run_only_on('sat')
    def test_create_subnet_negative_with_too_long_name(self, name):
        """@Test: Create new subnet with 256 characters in name

        @Feature: Subnet - Negative Create

        @Assert: Subnet is not created with 256 chars

        """
        with Session(self.browser) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
            )
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators['haserror']))

    @data('', ' ')
    @run_only_on('sat')
    def test_create_subnet_negative_with_blank_name(self, name):
        """@Test: Create new subnet with whitespace and blank in name.

        @Feature: Subnet - Negative Create.

        @Assert: Subnet is not created.

        """
        with Session(self.browser) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
            )
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators['haserror']))

    @run_only_on('sat')
    def test_create_subnet_negative_values(self):
        """@Test: Create new subnet with negative values

        @Feature: Subnet - Negative Create.

        @Assert: Subnet is not created with negative values

        """
        with Session(self.browser) as session:
            make_subnet(
                session,
                subnet_name=gen_string('alpha'),
                subnet_network='292.256.256.0',
                subnet_mask='292.292.292.0',
                subnet_gateway='292.256.256.254',
                subnet_primarydns='292.256.256.2',
                subnet_secondarydns='292.256.256.3',
            )
            network_element = session.nav.wait_until_element(
                locators['subnet.network_haserror'])
            mask_element = session.nav.wait_until_element(
                locators['subnet.mask_haserror'])
            gateway_element = session.nav.wait_until_element(
                locators['subnet.gateway_haserror'])
            primarydns_element = session.nav.wait_until_element(
                locators['subnet.dnsprimary_haserror'])
            secondarydns_element = session.nav.wait_until_element(
                locators['subnet.dnssecondary_haserror'])
            self.assertIsNotNone(network_element)
            self.assertIsNotNone(mask_element)
            self.assertIsNotNone(gateway_element)
            self.assertIsNotNone(primarydns_element)
            self.assertIsNotNone(secondarydns_element)

    @data(*generate_strings_list(len1=8))
    @run_only_on('sat')
    def test_remove_subnet(self, name):
        """@Test: Delete a subnet

        @Feature: Subnet - Positive Delete

        @Assert: Subnet is deleted

        """
        with Session(self.browser) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
            )
            self.subnet.delete(name)

    @run_only_on('sat')
    def test_remove_subnet_and_cancel(self):
        """@Test: Delete subnet.

        Attempt to delete subnet but cancel in the confirmation dialog box.

        @Feature: Subnet - Negative Delete

        @Assert: Subnet is not deleted

        """
        name = gen_string('utf8')
        with Session(self.browser) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
            )
            self.subnet.delete(name, False)

    @data(*generate_strings_list(len1=8))
    @run_only_on('sat')
    def test_update_subnet_with_name(self, new_name):
        """@Test: Update Subnet name

        @Feature: Subnet - Positive Update

        @Assert: Subnet name is updated

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
            )
            self.subnet.update(name, new_subnet_name=new_name)
            result_object = self.subnet.search_subnet(new_name)
            self.assertEqual(new_name, result_object['name'])

    @run_only_on('sat')
    def test_update_subnet_with_network(self):
        """@Test: Update Subnet network

        @Feature: Subnet - Positive Update

        @Assert: Subnet network is updated

        """
        name = gen_string('alpha')
        new_network = gen_ipaddr(ip3=True)
        with Session(self.browser) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(),
            )
            self.subnet.update(name, new_subnet_network=new_network)
            result_object = self.subnet.search_subnet(name)
            self.assertEqual(new_network, result_object['network'])

    @run_only_on('sat')
    def test_update_subnet_with_mask(self):
        """@Test: Update Subnet mask

        @Feature: Subnet - Positive Update

        @Assert: Subnet mask is updated

        """
        name = gen_string('alpha')
        new_mask = gen_netmask(16, 31)
        with Session(self.browser) as session:
            make_subnet(
                session,
                subnet_name=name,
                subnet_network=gen_ipaddr(ip3=True),
                subnet_mask=gen_netmask(1, 15),
            )
            self.subnet.update(name, new_subnet_mask=new_mask)
            result_object = self.subnet.search_subnet(name)
            self.assertEqual(new_mask, result_object['mask'])
