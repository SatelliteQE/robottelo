"""Implements Config Groups UI"""

from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class ConfigGroups(Base):
    """Provides the CRUD functionality for Config-Groups."""

    def navigate_to_entity(self):
        """Navigate to Config Group entity page"""
        Navigator(self.browser).go_to_config_groups()

    def _search_locator(self):
        """Specify locator for Config Group entity search procedure"""
        return locators['config_groups.select_name']

    def create(self, name):
        """Creates the config-groups."""
        self.click(locators['config_groups.new'])
        if self.wait_until_element(locators['config_groups.name']):
            self.find_element(locators['config_groups.name']).send_keys(name)
            self.click(common_locators['submit'])
        else:
            raise UINoSuchElementError(
                'Could not text box to add config_group name')

    def update(self, old_name, new_name=None):
        """Updates the config-groups."""
        element = self.get_entity(old_name)
        if element:
            element.click()
            if (self.wait_until_element(locators['config_groups.name']) and
               new_name):
                self.field_update('config_groups.name', new_name)
            self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Deletes the config-groups."""
        self.delete_entity(
            name,
            really,
            locators['config_groups.delete'],
            drop_locator=locators['config_groups.dropdown'],
        )
