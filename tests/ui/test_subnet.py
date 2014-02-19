# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Subnet UI
"""

from tests.ui.baseui import BaseUI
from robottelo.common.helpers import generate_name
from robottelo.common.helpers import generate_ipaddr


class Subnet(BaseUI):
    """
    Implements subnet tests from UI
    """
    def create_org(self, org_name=None):
        """Creates Org"""
        org_name = org_name or generate_name(8, 8)
        self.navigator.go_to_org()  # go to org page
        self.org.create(org_name)

    def create_subnet(self, subnet_name=None, subnet_network=None,
                      subnet_mask=None,):
        """
        Create Subnet with navigation steps
        """

        subnet_name = subnet_name or generate_name(8, 8)
        subnet_network = subnet_network or generate_ipaddr(ip3=True)
        org_name = generate_name(8, 8)
        self.create_org(org_name)
        self.navigator.go_to_subnets()  # go to subnet page
        self.subnet.create([org_name], subnet_name, subnet_network,
                           subnet_mask)
        #TODO: Unable to capture the success message for now

    def test_create_subnet(self):
        """
        @Feature: Subnet - Positive Create
        @Test: Create new subnet - given subnet name, subnet network,
        subnet mask
        @Assert: Subnet is created
        """

        subnet_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_subnet(subnet_name, subnet_network, subnet_mask)
        self.assertIsNotNone(self.subnet.search_subnet(subnet_name))

    def test_remove_subnet_1(self):
        """
        @Feature: Subnet - Positive Delete
        @Test: Delete a subnet
        @Assert: Subnet is deleted
        """

        subnet_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_subnet(subnet_name, subnet_network, subnet_mask)
        self.subnet.delete(subnet_name, True)
        #TODO: Unable to capture the success message for now
        self.assertFalse(self.subnet.search_subnet(subnet_name))

    def test_remove_subnet_2(self):
        """
        @Feature: Subnet - Negative Delete
        @Test: Create subnet. Attempt to delete subnet but cancel
        in the confirmation dialog box
        @Assert: Subnet is not deleted
        """

        subnet_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_subnet(subnet_name, subnet_network, subnet_mask)
        self.subnet.delete(subnet_name, False)
        self.assertTrue(self.subnet.search_subnet(subnet_name))

    def test_update_subnet_1(self):
        """
        @Feature: Subnet - Positive Update
        @Test: Update Subnet name
        @Assert: Subnet name is updated
        """

        subnet_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_subnet(subnet_name, subnet_network, subnet_mask)
        new_subnet_name = generate_name(8, 8)
        self.subnet.update(subnet_name, new_subnet_name=new_subnet_name)
        result_object = self.subnet.search_subnet(new_subnet_name)
        self.assertEqual(new_subnet_name, result_object['name'])

    def test_update_subnet_2(self):
        """
        @Feature: Subnet - Positive Update
        @Test: Update Subnet network
        @Assert: Subnet network is updated
        """

        subnet_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_subnet(subnet_name, subnet_network, subnet_mask)
        new_subnet_network = generate_ipaddr(ip3=True)
        self.subnet.update(subnet_name, new_subnet_network=new_subnet_network)
        result_object = self.subnet.search_subnet(subnet_name)
        self.assertEqual(new_subnet_network, result_object['network'])

    def test_update_subnet_3(self):
        """
        @Feature: Subnet - Positive Update
        @Test: Update Subnet mask
        @Assert: Subnet mask is updated
        """

        subnet_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_subnet(subnet_name, subnet_network, subnet_mask)
        new_subnet_mask = "128.128.128.0"
        self.subnet.update(subnet_name, new_subnet_mask=new_subnet_mask)
        result_object = self.subnet.search_subnet(subnet_name)
        self.assertEqual(new_subnet_mask, result_object['mask'])

    def test_search_subnet_1(self):
        """
        @Feature: Subnet - Positive Search
        @Test: Search Subnet with Subnet name
        @Assert: Subnet is found
        """

        subnet_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_subnet(subnet_name, subnet_network, subnet_mask)
        result_object = self.subnet.search_subnet(subnet_name)
        self.assertEqual(subnet_name, result_object['name'])
        self.assertEqual(subnet_network, result_object['network'])
        self.assertEqual(subnet_mask, result_object['mask'])

    def test_search_subnet_2(self):
        """
        @Feature: Subnet - Negative Search
        @Test: Search for a non-existent subnet name
        @Assert: Subnet name is not found
        """

        subnet_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.assertFalse(self.subnet.search_subnet(subnet_name))
