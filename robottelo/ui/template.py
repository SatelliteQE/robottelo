# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Template UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
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
            self.handle_alert(custom_really)
        if template_type:
            self.wait_until_element(tab_locators["provision.tab_type"]).click()
            type_ele = self.find_element(locators["provision.template_type"])
            Select(type_ele).select_by_visible_text(template_type)
        if os_list is not None:
            self.wait_until_element(tab_locators["provision.tab_association"]).click()  # @IgnorePep8
            for os in os_list:
                strategy = locators["provision.associate_os"][0]
                value = locators["provision.associate_os"][1]
                element = self.wait_until_element((strategy, value % os))
                if element:
                    element.click()
        self.find_element(common_locators["submit"]).click()

    def search(self, name):
        """
        Searches existing template from UI
        """
        self.search_entity(name, locators["provision.template_select"])

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
                self.handle_alert(custom_really)
            if template_type:
                type_loc = self.wait_until_element(tab_locators["provision.tab_type"])  # @IgnorePep8
                type_loc.click()
                ele = self.find_element(locators["provision.template_type"])
                Select(ele).select_by_visible_text(template_type)
            if os_list is not None:
                assoc_loc = self.wait_until_element(tab_locators["provision.tab_association"])  # @IgnorePep8
                assoc_loc.click()
                for os in os_list:
                    strategy = locators["provision.associate_os"][0]
                    value = locators["provision.associate_os"][1]
                    element = self.wait_until_element((strategy, value % os))
                    if element:
                        element.click()
            self.find_element(common_locators["submit"]).click()
        else:
            raise Exception("Could not update the template '%s'" % name)

    def delete(self, name, really):
        """
        Deletes a template.
        """
        self.delete_entity(name, really, locators["provision.template_select"],
                           locators["provision.template_delete"])
