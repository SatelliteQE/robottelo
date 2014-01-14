# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Subnet UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators


class Subnet(Base):
    """
    Provides the CRUD functionality for Subnet
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def create(self, subnet_name=None, subnet_network=None, subnet_mask=None,):
        """
        Create Subnet from UI
        """

        self.wait_until_element(locators["subnet.new"]).click()

        if self.wait_until_element(locators["subnet.name"]):
            self.find_element(locators["subnet.name"]).send_keys(subnet_name)
        if self.wait_until_element(locators["subnet.network"]):
            self.find_element(locators
                              ["subnet.network"]
                              ).send_keys(subnet_network)
        if self.wait_until_element(locators["subnet.mask"]):
            self.find_element(locators["subnet.mask"]).send_keys(subnet_mask)
        self.wait_until_element(common_locators["submit"]).click()

    def delete(self, subnet_name, really):
        """
        Remove subnet from UI
        """

        self.delete_entity(subnet_name, really,
                           locators["subnet.display_name"],
                           locators['subnet.delete'])

    def search_subnet(self, subnet_name):
        """
        Search Subnet name, network and mask to validate results
        """

        result = None

        subnet_object = self.search_entity(subnet_name,
                                    locators
                                    ['subnet.display_name'])

        if subnet_object:
            subnet_object.click()
            if self.wait_until_element(locators["subnet.name"]):
                result = dict([('name', None), ('network', None),
                               ('mask', None)])
                result['name'] = self.find_element(
                    locators["subnet.name"]
                ).get_attribute("value")
                result['network'] = self.find_element(
                    locators["subnet.network"]
                ).get_attribute("value")
                result['mask'] = self.find_element(
                    locators["subnet.mask"]
                ).get_attribute("value")
        return result

    def update(self, subnet_name, new_subnet_name=None,
               new_subnet_network=None, new_subnet_mask=None):
        """
        Update subnet name, network and mask from UI
        """

        subnet_object = self.search_entity(subnet_name,
                                    locators
                                    ["subnet.display_name"])

        if subnet_object:
            subnet_object.click()
            if new_subnet_name:
                if self.wait_until_element(locators["subnet.name"]):
                    self.field_update("subnet.name", new_subnet_name)
            if new_subnet_network:
                if self.wait_until_element(locators["subnet.network"]):
                    self.field_update("subnet.network", new_subnet_network)
            if new_subnet_mask:
                if self.wait_until_element(locators["subnet.mask"]):
                    self.field_update("subnet.mask", new_subnet_mask)
            self.wait_until_element(common_locators["submit"]).click()
