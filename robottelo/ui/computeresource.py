#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from selenium.webdriver.support.select import Select


class ComputeResource(Base):
    """
    Provides the CRUD functionality for Compute Resources.
    """

    def __init__(self, browser):
        self.browser = browser

    def create(self, name, provider_type=None, url=None, user=None,
               password=None, region=None, libvirt_display=None,
               libvirt_set_passwd=True, tenant=None):
        """
        Configures the compute resource.
        """
        self.wait_until_element(locators["resource.new"]).click()
        if self.wait_until_element(locators["resource.name"]):
            self.find_element(locators["resource.name"]).send_keys(name)
        if provider_type:
            type_ele = self.find_element(locators["resource.provider_type"])
            Select(type_ele).select_by_visible_text(provider_type)
            if provider_type in ["EC2", "Rackspace", "Openstack"]:
                if provider_type in ["Rackspace", "Openstack"]:
                    self.find_element(locators["resource.url"]).send_keys(url)
                access = self.find_element(locators["resource.user"])
                access.send_keys(user)
                secret = self.find_element(locators["resource.password"])
                secret.send_keys(password)
                self.find_element(locators["resource.test_connection"]).click()
                self.wait_for_ajax()
                if provider_type in ["Rackspace", "EC2"]:
                    region = self.find_element(locators["resource.region"])
                    Select(region).select_by_visible_text(region)
                elif provider_type == "Openstack":
                    tenant = self.find_element(locators["resource.rhos_tenant"])  # @IgnorePep8
                    Select(tenant).select_by_visible_text(tenant)

            if provider_type == "Libvirt":
                if self.wait_until_element(locators["resource.url"]):
                    self.find_element(locators["resource.url"]).send_keys(url)
                if libvirt_display is not None:
                    display = self.find_element(locators["resource.libvirt_display"])  # @IgnorePep8
                    Select(display).select_by_visible_text(libvirt_display)
                if libvirt_set_passwd is False:
                    self.find_element(locators["resource.libvirt_console_passwd"]).click()  # @IgnorePep8
                self.find_element(locators["resource.test_connection"]).click()
                self.wait_for_ajax()
        self.find_element(locators["submit"]).click()

    def delete(self, name, really):
        """
        Removes the compute resource info.
        """
        searched = self.search(name, locators["resource.select_name"])
        if searched:
            strategy = locators["resource.dropdown"][0]
            value = locators["resource.dropdown"][1]
            dropdown = self.wait_until_element((strategy, value % name))
            dropdown.click()
            strategy1 = locators["resource.delete"][0]
            value1 = locators["resource.delete"][1]
            element = self.wait_until_element((strategy1, value1 % name))
            if element:
                element.click()
                if really:
                    alert = self.browser.switch_to_alert()
                    alert.accept()
                else:
                    alert = self.browser.switch_to_alert()
                    alert.dismiss()
