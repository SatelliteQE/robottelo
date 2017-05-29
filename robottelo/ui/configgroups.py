"""Implements Config Groups UI"""

from robottelo.ui.base import Base
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
        self.assign_value(locators['config_groups.name'], name)
        self.click(common_locators['submit'])

    def update(self, old_name, new_name=None):
        """Updates the config-groups."""
        self.search_and_click(old_name)
        if new_name:
            self.assign_value(locators['config_groups.name'], new_name)
        self.click(common_locators['submit'])
