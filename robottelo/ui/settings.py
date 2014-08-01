# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Settings UI
"""

from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import locators
from selenium.webdriver.support.select import Select


class UnknownValueType(Exception):
    """Indicates that value_type is other than 'input' and 'dropdown'"""


class Settings(Base):
    """
    Implements the Update function to edit/update settings
    """

    def search(self, name):
        """
        Searches existing parameter from UI
        """
        element = self.search_entity(name, locators["settings.param"])
        return element

    def update(self, tab_locator, param_name, value_type, param_value):
        """
        Updates the value of selected parameter under settings
        """

        if self.wait_until_element(tab_locator):
            self.find_element(tab_locator).click()
            strategy, value = locators["settings.edit_param"]
            element = self.wait_until_element((strategy,
                                               value % param_name))
            if element:
                element.click()
                if value_type == "dropdown":
                    Select(self.find_element
                           (locators["settings.select_value"])
                           ).select_by_value(param_value)
                elif value_type == "input":
                    self.field_update("settings.input_value", param_value)
                else:
                    raise UnknownValueType(
                        "Please input appropriate value type")
                self.wait_for_ajax()
                self.wait_until_element(locators["settings.save"]).click()
                self.wait_for_ajax()
            else:
                raise UINoSuchElementError(
                    "Couldn't find edit button to update selected param")
        else:
            raise UINoSuchElementError(
                "Couldn't find the tab with name: '%s'" % tab_locator)

    def get_saved_value(self, tab_locator, param_name):
        """
        Fetch the updated value to assert
        """

        if self.wait_until_element(tab_locator):
            self.find_element(tab_locator).click()
            strategy, value = locators["settings.edit_param"]
            element = self.wait_until_element((strategy,
                                               value % param_name))
            if element:
                return element.text
            else:
                raise UINoSuchElementError(
                    "Couldn't find element to fetch the param's value")
