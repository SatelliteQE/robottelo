"""Implements Config Groups UI"""

from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class ConfigGroups(Base):
    """Provides the CRUD functionality for Config-Groups."""

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
        element = self.search(old_name)
        if element:
            element.click()
            if (self.wait_until_element(locators['config_groups.name']) and
               new_name):
                self.field_update('config_groups.name', new_name)
            self.click(common_locators['submit'])

    def search(self, name):
        """Searches existing config-groups from UI"""
        Navigator(self.browser).go_to_config_groups()
        if len(name) <= 30:
            element = self.search_entity(
                name, locators['config_groups.select_name'])
        else:
            element = self.search_entity(
                name, common_locators['select_filtered_entity'])
        return element

    def delete(self, name, really=True):
        """Deletes the config-groups."""
        self.delete_entity(
            name,
            really,
            locators['config_groups.select_name'],
            locators['config_groups.delete'],
            drop_locator=locators['config_groups.dropdown'],
        )
