#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.ui.base import Base
from lib.ui.locators import locators
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select


class Template(Base):
    """
    Provides the CRUD functionality for Templates.
    """

    def __init__(self, browser):
        self.browser = browser

    def create(self, name, os_list, custom_really, template_path=None,
               template_type=None):
        """
        Creates a template.
        """
        self.wait_until_element(locators["provision.template_new"]).click()
        if self.wait_until_element(locators["provision.template_name"]):
            temp_name = self.find_element(locators["provision.template_name"])
            temp_name.send_keys(name)
        if template_path:
            browse = self.find_element(locators["provision.template_template"])
            browse.send_keys(template_path)
            if custom_really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss()
        if template_type:
            self.wait_until_element(locators["provision.tab_type"]).click()
            type_ele = self.find_element(locators["provision.template_type"])
            Select(type_ele).select_by_visible_text(template_type)
        if os_list is not None:
            self.wait_until_element(locators["provision.tab_association"]).click() # @IgnorePep8
            for os in os_list:
                strategy = locators["provision.associate_os"][0]
                value = locators["provision.associate_os"][1]
                element = self.wait_until_element((strategy, value % os))
                if element:
                    element.click()
        self.find_element(locators["submit"]).click()

    def update(self, name, os_list, custom_really, new_name=None,
               template_path=None, template_type=None):
        """
        Updates a given template.
        """
        element = self.search(name)
        if element:
            element.click()
            self.wait_for_ajax()
            if new_name:
                self.field_update("provision.template_name", new_name)
            if template_path:
                tp = self.find_element(locators["provision.template_template"])
                tp.send_keys(template_path)
                if custom_really:
                    alert = self.browser.switch_to_alert()
                    alert.accept()
                else:
                    alert = self.browser.switch_to_alert()
                    alert.dismiss()
            if template_type:
                self.wait_until_element(locators["provision.tab_type"]).click()
                ele = self.find_element(locators["provision.template_type"])
                Select(ele).select_by_visible_text(template_type)
            if os_list is not None:
                self.wait_until_element(locators["provision.tab_association"]).click()  # @IgnorePep8
                for os in os_list:
                    strategy = locators["provision.associate_os"][0]
                    value = locators["provision.associate_os"][1]
                    element = self.wait_until_element((strategy, value % os))
                    if element:
                        element.click()
            self.find_element(locators["submit"]).click()

    def delete(self, name, really):
        """
        Deletes a template.
        """
        strategy = locators["provision.template_select"][0]
        value = locators["provision.template_select"][1]
        element = self.wait_until_element((strategy, value % name))
        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss(self)

    def search(self, name):
        """
        Searches for the template.
        """
        searchbox = self.wait_until_element(locators["search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(name)
            searchbox.send_keys(Keys.RETURN)
            strategy = locators["provision.template_select"][0]
            value = locators["provision.template_select"][1]
            template = self.wait_until_element((strategy, value % name))
            if template:
                template.click()
        return template
