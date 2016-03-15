# -*- encoding: utf-8 -*-
"""Test class for Subnet UI"""

from fauxfactory import gen_ipaddr, gen_netmask, gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import bz_bug_is_open, run_only_on, tier1, tier2
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_subnet
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


def valid_long_names():
    """Returns a list of valid long subnet names"""
    return [
        {'name': gen_string('alphanumeric', 255)},
        {'name': gen_string('alpha', 255)},
        {'name': gen_string('numeric', 255)},
        {'name': gen_string('latin1', 255)},
        {'name': gen_string('utf8', 255), u'bz-bug': 1180066}
    ]


class SubnetTestCase(UITestCase):
    """Implements Subnet tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(SubnetTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create new subnet using different names

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=8):
                with self.subTest(name):
                    make_subnet(
                        session,
                        subnet_name=name,
                        subnet_network=gen_ipaddr(ip3=True),
                        subnet_mask=gen_netmask(),
                    )
                    self.assertIsNotNone(self.subnet.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_long_name(self):
        """Create new subnet with 255 characters in name

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created with 255 chars
        """
        with Session(self.browser) as session:
            for test_data in valid_long_names():
                with self.subTest(test_data):
                    bug_id = test_data.pop('bz-bug', None)
                    if bug_id is not None and bz_bug_is_open(bug_id):
                        self.skipTest(
                            'Bugzilla bug {0} is open.'.format(bug_id)
                        )
                    make_subnet(
                        session,
                        subnet_name=test_data['name'],
                        subnet_network=gen_ipaddr(ip3=True),
                        subnet_mask=gen_netmask(),
                    )
                    self.assertIsNotNone(
                        self.subnet.search(test_data['name']))

    @run_only_on('sat')
    @tier2
    def test_positive_add_domain(self):
        """Create new subnet and associate domain with it

        @Feature: Subnet - Positive Create

        @Assert: Subnet is created with domain associated
        """
        strategy1, value1 = common_locators['entity_deselect']
        strategy2, value2 = common_locators['entity_checkbox']
        name = gen_string('alpha')
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
            subnet = self.subnet.search(name)
            session.nav.click(subnet)
            session.nav.click(tab_locators['subnet.tab_domain'])
            element = session.nav.wait_until_element(
                (strategy1, value1 % domain.name))
            checkbox_element = session.nav.wait_until_element(
                (strategy2, value2 % domain.name))
            # Depending upon the number of domains either, checkbox or
            # selection list appears.
            if element is None and checkbox_element is None:
                raise UIError('Neither checkbox or select list is present')
            if checkbox_element:
                self.assertTrue(checkbox_element.is_selected())

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create new subnet with invalid names

        @Feature: Subnet - Negative Create

        @Assert: Subnet is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_subnet(
                        session,
                        subnet_name=name,
                        subnet_network=gen_ipaddr(ip3=True),
                        subnet_mask=gen_netmask(),
                    )
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['haserror']))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_params(self):
        """Create new subnet with negative values

        @Feature: Subnet - Negative Create.

        @Assert: Subnet is not created
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
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['subnet.network_haserror']))
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['subnet.mask_haserror']))
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['subnet.gateway_haserror']))
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['subnet.dnsprimary_haserror']))
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['subnet.dnssecondary_haserror']))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete an existing subnet

        @Feature: Subnet - Positive Delete

        @Assert: Subnet is deleted
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=8):
                with self.subTest(name):
                    make_subnet(
                        session,
                        subnet_name=name,
                        subnet_network=gen_ipaddr(ip3=True),
                        subnet_mask=gen_netmask(),
                    )
                    self.subnet.delete(name)

    @run_only_on('sat')
    @tier1
    def test_negative_delete(self):
        """Delete subnet. Attempt to delete subnet, but cancel in the
        confirmation dialog box.

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
            self.subnet.delete(name, really=False)

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update Subnet name

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
            for new_name in generate_strings_list(length=8):
                with self.subTest(new_name):
                    self.subnet.update(name, new_subnet_name=new_name)
                    result_object = self.subnet.search_and_validate(new_name)
                    self.assertEqual(new_name, result_object['name'])
                    name = new_name  # for next iteration

    @run_only_on('sat')
    @tier1
    def test_positive_update_network(self):
        """Update Subnet network

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
            result_object = self.subnet.search_and_validate(name)
            self.assertEqual(new_network, result_object['network'])

    @run_only_on('sat')
    @tier1
    def test_positive_update_mask(self):
        """Update Subnet mask

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
            result_object = self.subnet.search_and_validate(name)
            self.assertEqual(new_mask, result_object['mask'])
