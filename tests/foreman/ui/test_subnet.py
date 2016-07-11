# -*- encoding: utf-8 -*-
"""Test class for Subnet UI

@Requirement: Subnet

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_ipaddr, gen_netmask, gen_string
from nailgun import entities
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.decorators import bz_bug_is_open, run_only_on, tier1, tier2
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_subnet
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@filtered_datapoint
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

        @id: 2318f13c-db38-4919-831f-667fc6e2e7bf

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

        @id: b86772ad-a8ff-4c2b-93f4-4a715e4da59b

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

        @id: adbc7189-b451-49df-aa10-2ae732832dfe

        @Assert: Subnet is created with domain associated

        @CaseLevel: Integration
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

        @id: d53056ad-a219-40d5-b20e-95ad343c9d38

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

        @id: 5caa6aed-2bba-43d8-bb40-2d80b9d42b69

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

        @id: cb1265de-a0ed-40b7-ba25-fe92251b9001

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

        @id: 9eed9020-8d13-4ba0-909a-db44ad0aecb6

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

        @id: ec9f11e3-27a7-45d8-91fe-f04c20b595bc

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

        @id: f79d3b1b-6101-4009-88ad-b259d4794e6c

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

        @id: 6cc5de06-5463-4919-abe4-92cef4506a54

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
