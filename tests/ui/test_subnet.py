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

    def create_subnet(self, subnet_name=None, subnet_network=None,
                      subnet_mask=None,):
        """
        Create Subnet with navigation steps
        """

        subnet_name = subnet_name or generate_name(8, 8)
        subnet_network = subnet_network or generate_ipaddr(ip3=True)
        self.navigator.go_to_subnets()  # go to subnet page
        self.subnet.create(subnet_name, subnet_network, subnet_mask)
        #TODO: Unable to capture the success message for now

    def test_create_subnet(self):
        """
        Create new subnet - given subnet name, subnet network, subnet mask
        """

        subnet_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_subnet(subnet_name, subnet_network, subnet_mask)
        self.assertIsNotNone(self.subnet.search_subnet(subnet_name))

    def test_remove_subnet_1(self):
        """
        Delete subnet - Create subnet and delete the same
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
        """"
        Delete subnet - Create subnet. Attempt to delete subnet but cancel
        in the confirmation dialog box
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
        Update subnet name
        """

        subnet_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_subnet(subnet_name, subnet_network, subnet_mask)
        new_subnet_name = generate_name(8, 8)
        self.subnet.update(subnet_name, new_subnet_name, None, None)
        result_object = self.subnet.search_subnet(new_subnet_name)
        self.assertEqual(new_subnet_name, result_object['name'])

    def test_update_subnet_2(self):
        """
        Update subnet network
        """

        subnet_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_subnet(subnet_name, subnet_network, subnet_mask)
        new_subnet_network = generate_ipaddr(ip3=True)
        self.subnet.update(subnet_name, None, new_subnet_network, None)
        result_object = self.subnet.search_subnet(subnet_name)
        self.assertEqual(new_subnet_network, result_object['network'])

    def test_update_subnet_3(self):
        """
        Update subnet mask
        """

        subnet_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_subnet(subnet_name, subnet_network, subnet_mask)
        new_subnet_mask = "128.128.128.0"
        self.subnet.update(subnet_name, None, None, new_subnet_mask)
        result_object = self.subnet.search_subnet(subnet_name)
        self.assertEqual(new_subnet_mask, result_object['mask'])

    def test_search_subnet_1(self):
        """
        Search subnet - Given the subnet name
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
        Search subnet - Search for a non-existent subnet
        """

        subnet_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.assertFalse(self.subnet.search_subnet(subnet_name))
