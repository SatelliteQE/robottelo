#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select


class Domain(Base):

    def __init__(self, browser):
        self.browser = browser

    def create(self, name, description=None, dns_proxy=None):
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
            self.find_element(locators["submit"]).click()
            self.wait_for_ajax()

    def delete(self, name, really):
        element = self.wait_until_element((locators
                                           ["domain.delete"][0],
                                           locators
                                           ["domain.delete"][1]
                                           % name))
        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss(self)
            self.wait_for_ajax()

    def search(self, description):
        searchbox = self.wait_until_element(locators["search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(description)
            searchbox.send_keys(Keys.RETURN)
            domain = self.wait_until_element((locators
                                              ["domain.domain_description"][0],
                                              locators
                                              ["domain.domain_description"][1]
                                              % description))
            if domain:
                domain.click()
        return domain

    def update(self, old_description, new_name=None,
               new_description=None, new_dns_proxy=None):
        element = self.wait_until_element((locators
                                           ["domain.domain_description"][0],
                                           locators
                                           ["domain.domain_description"][1]
                                           % old_description))
        if element:
            element.click()
        if self.wait_until_element(locators["domain.name"]):
            self.field_update("domain.name", new_name)
        if new_description:
            if self.wait_until_element(locators["domain.description"]):
                self.field_update("domain.description", new_description)
        if new_dns_proxy:
            Select(self.find_element(locators
                                     ["domain.dns_proxy"]
                                     )).select_by_visible_text(new_dns_proxy)
        self.find_element(locators["submit"]).click()
        self.wait_for_ajax()

    def set_parameter(self, domain_description, param_name, param_value):
        element = self.wait_until_element((locators
                                           ["domain.domain_description"][0],
                                           locators
                                           ["domain.domain_description"][1]
                                           % domain_description))
        if element:
            element.click()
            self.wait_until_element(locators["domain.parameter_tab"]).click()
            self.wait_until_element(locators["domain.add_parameter"]).click()
            if self.wait_until_element(locators
                                       ["domain.parameter_name"]):
                self.find_element(locators
                                  ["domain.parameter_name"]
                                  ).send_keys(param_name)
            if self.wait_until_element(locators
                                       ["domain.parameter_value"]):
                self.find_element(locators
                                  ["domain.parameter_value"]
                                  ).send_keys(param_value)
            self.find_element(locators["submit"]).click()
            self.wait_for_ajax()

    def remove_parameter(self, domain_description, param_name):
        element = self.wait_until_element((locators
                                           ["domain.domain_description"][0],
                                           locators
                                           ["domain.domain_description"][1]
                                           % domain_description))
        if element:
            element.click()
            self.wait_until_element(locators["domain.parameter_tab"]).click()
            remove_element = self.wait_until_element((locators
                                                      ["domain.parameter_remove"][0],
                                                      locators
                                                      ["domain.parameter_remove"][1]
                                                      % param_name))
            if remove_element:
                remove_element.click()
            self.find_element(locators["submit"]).click()
