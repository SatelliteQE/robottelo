# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Domain UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators
from selenium.webdriver.support.select import Select


class Domain(Base):
    "Manipulates Foreman's domain from UI"

    def __init__(self, browser):
        """
        Sets the browser object
        """
        self.browser = browser

    def create(self, name, description=None, dns_proxy=None):
        """
        Creates new domain with name, description and dns_proxy
        """

        self.wait_until_element(locators["domain.new"]).click()

        if self.wait_until_element(locators["domain.name"]):
            self.find_element(locators["domain.name"]).send_keys(name)
            if description:
                if self.wait_until_element(locators["domain.description"]):
                    self.find_element(locators
                                      ["domain.description"]
                                      ).send_keys(description)
            if dns_proxy:
                Select(self.find_element(locators
                                         ["domain.dns_proxy"]
                                         )).select_by_visible_text(dns_proxy)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()

    def search(self, name):
        """
        Searches existing domain from UI
        """
        element = self.search_entity(name,
                                     locators['domain.domain_description'])
        return element

    def delete(self, name, really):
        """
        Delete existing domain from UI
        """

        self.delete_entity(name, really, locators['domain.domain_description'],
                           locators['domain.delete'])

    def update(self, old_description, new_name=None,
               new_description=None, new_dns_proxy=None):
        """
        Update an existing domain's name, description and dns_proxy
        """

        element = self.search(old_description)

        if element:
            element.click()
            if self.wait_until_element(locators["domain.name"]):
                self.field_update("domain.name", new_name)
            if new_description:
                if self.wait_until_element(locators["domain.description"]):
                    self.field_update("domain.description", new_description)
            if new_dns_proxy:
                element = self.find_element(locators["domain.dns_proxy"])
                Select(element).select_by_visible_text(new_dns_proxy)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()

    def set_domain_parameter(self, domain_description,
                             param_name, param_value):
        """
        Add new parameter for domain
        """

        element = self.search(domain_description)

        if element:
            element.click()
        self.set_parameter(param_name, param_value)

    def remove_domain_parameter(self, domain_description, param_name):
        """
        Remove new parameter from domain
        """

        element = self.search(domain_description)

        if element:
            element.click()
        self.remove_parameter(param_name)
