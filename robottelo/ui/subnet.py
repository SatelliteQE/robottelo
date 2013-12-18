#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Subnet UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from selenium.webdriver.common.keys import Keys


class Subnet(Base):

    def __init__(self, browser):
        self.browser = browser

    def create(self, subnet_name=None, subnet_network=None, subnet_mask=None,):
        self.wait_until_element(locators["subnet.new"]).click()
        if self.wait_until_element(locators["subnet.name"]):
            name_field = self.find_element(locators["subnet.name"])
            name_field.clear()
            name_field.send_keys(subnet_name)
        if self.wait_until_element(locators["subnet.network"]):
            network_field = self.find_element(locators["subnet.network"])
            network_field.clear()
            network_field.send_keys(subnet_network)
        if self.wait_until_element(locators["subnet.mask"]):
            mask_field = self.find_element(locators["subnet.mask"])
            mask_field.clear()
            mask_field.send_keys(subnet_mask)
        self.wait_until_element(locators["subnet.submit"]).click()
        self.wait_for_ajax()

    def remove(self, subnet_name, really):
        element = self.wait_until_element((locators["subnet.delete"][0],
                                           locators["subnet.delete"][1]
                                           % subnet_name), delay=5)
        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss()
        self.wait_for_ajax()

    def search(self, subnet_name):
        result = None
        searchbox = self.wait_until_element(locators["search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(subnet_name)
            searchbox.send_keys(Keys.RETURN)
            subnet_object = self.find_element((
                                locators["subnet.display_name"][0],
                                locators["subnet.display_name"][1]
                                % subnet_name))
            if subnet_object:
                subnet_object.click()
                if self.wait_until_element(locators["subnet.name"]):
                    result = dict([('name', None), ('network', None),
                                   ('mask', None)])
                    result['name'] = self.find_element(
                                        locators["subnet.name"]).get_attribute("value")  # @IgnorePep8
                    result['network'] = self.find_element(
                                            locators["subnet.network"]).get_attribute("value")  # @IgnorePep8
                    result['mask'] = self.find_element(
                                        locators["subnet.mask"]).get_attribute("value")  # @IgnorePep8
        return result

    def update(self, subnet_name, new_subnet_name=None,
               new_subnet_network=None, new_subnet_mask=None):
        if self.wait_until_element((locators["subnet.display_name"][0],
                                    locators["subnet.display_name"][1]
                                    % subnet_name), delay=2):
            subnet_object = self.find_element((
                                locators["subnet.display_name"][0],
                                locators["subnet.display_name"][1]
                                % subnet_name))
        if subnet_object:
            subnet_object.click()
        if new_subnet_name:
            if self.wait_until_element(locators["subnet.name"]):
                name_field = self.find_element(locators["subnet.name"])
                name_field.clear()
                name_field.send_keys(new_subnet_name)
        if new_subnet_network:
            if self.wait_until_element(locators["subnet.network"]):
                network_field = self.find_element(locators["subnet.network"])
                network_field.clear()
                network_field.send_keys(new_subnet_network)
        if new_subnet_mask:
            if self.wait_until_element(locators["subnet.mask"]):
                mask_field = self.find_element(locators["subnet.mask"])
                mask_field.clear()
                mask_field.send_keys(new_subnet_mask)
        self.wait_until_element(locators["subnet.submit"]).click()
        self.wait_for_ajax()
