# -*- encoding: utf-8 -*-
"""Implements Settings UI"""

from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class OptionError(ValueError):
    """Indicates that value_type is other than 'input' and 'dropdown'"""


class Settings(Base):
    """Implements the Update function to edit/update settings"""

    def navigate_to_entity(self):
        """Navigate to Settings entity page"""
        Navigator(self.browser).go_to_settings()

    def _search_locator(self):
        """Specify locator for Settings entity search procedure"""
        return locators['settings.param']

    def update(self, tab_locator, param_name, value_type, param_value):
        """Updates the value of selected parameter under settings

        @param tab_locator: Selenium locator to select appropriate tab.
        @param param_name: A valid parameter name.
        @param value_type: Valid value type either 'input' or 'dropdown'
        @param param_value: Value of selected parameter

        @raise OptionError: Raise an exception when value type is different
        than 'input' and 'dropdown'.
        @raise UINoSuchElementError: Raise an exception when UI element is
        not found

        """
        if self.wait_until_element(tab_locator) is None:
            raise UINoSuchElementError(
                "Couldn't find the tab with name: '%s'" % tab_locator)
        self.click(tab_locator)

        strategy, value = locators['settings.edit_param']
        self.click((strategy, value % param_name))

        if value_type == 'dropdown':
            self.select(locators['settings.select_value'], param_value)
        elif value_type == 'input':
            self.wait_until_element(locators['settings.input_value'])
            self.field_update('settings.input_value', param_value)
        else:
            raise OptionError('Please input appropriate value type')
        self.wait_for_ajax()
        self.click(locators['settings.save'])

    def get_saved_value(self, tab_locator, param_name):
        """Fetch the updated value to assert"""
        self.navigate_to_entity()
        if self.wait_until_element(tab_locator):
            self.click(tab_locator)
            strategy, value = locators['settings.edit_param']
            element = self.wait_until_element((strategy, value % param_name))
            if element:
                if element.text.lower().startswith('click to edit'):
                    return ''
                return element.text
            else:
                raise UINoSuchElementError(
                    "Couldn't find element to fetch the param's value")
