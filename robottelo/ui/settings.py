# -*- encoding: utf-8 -*-
"""Implements Settings UI"""

from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class Settings(Base):
    """Implements the Update function to edit/update settings"""

    def navigate_to_entity(self):
        """Navigate to Settings entity page"""
        Navigator(self.browser).go_to_settings()

    def remove_parameter(self, tab_locator, param_name):
        """Removes the value of selected parameter under settings"""
        self.click(tab_locator)
        loc = locators['settings.edit_param']
        self.click(loc % param_name)
        self.click(locators['settings.remove'])
        self.click(locators['settings.save'])

    def _search_locator(self):
        """Specify locator for Settings entity search procedure"""
        return locators['settings.param']

    def update(self, tab_locator, param_name, param_value):
        """Updates the value of selected parameter under settings

        @param tab_locator: Selenium locator to select appropriate tab.
        @param param_name: A valid parameter name.
        @param param_value: Value of selected parameter

        @raise UINoSuchElementError: Raise an exception when UI element is
        not found
        """
        if self.wait_until_element(tab_locator) is None:
            raise UINoSuchElementError(
                "Couldn't find the tab with name: '%s'" % tab_locator)
        self.click(tab_locator)

        loc = locators['settings.edit_param']
        if self.wait_until_element(loc % param_name) is None:
            raise UINoSuchElementError(
                'Could not find edit button to update selected param'
            )
        else:
            self.click(loc % param_name)
            self.assign_value(locators['settings.edit_value'], param_value)
            self.click(locators['settings.save'])

    def get_saved_value(self, tab_locator, param_name):
        """Fetch the updated value to assert"""
        self.navigate_to_entity()
        if self.wait_until_element(tab_locator):
            self.click(tab_locator)
            element = self.wait_until_element(
                locators['settings.edit_param'] % param_name)
            if element:
                if element.text.lower().startswith('Empty'):
                    return ''
                return element.text
            else:
                raise UINoSuchElementError(
                    "Couldn't find element to fetch the param's value")
