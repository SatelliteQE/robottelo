"""
Implements Config Groups UI
"""

from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator


class ConfigGroups(Base):
    """
    Provides the CRUD functionality for Config-Groups.
    """

    def create(self, name):
        """
        Creates the config-groups.
        """
        self.wait_until_element(locators["config_groups.new"]).click()
        if self.wait_until_element(locators["config_groups.name"]):
            self.find_element(locators["config_groups.name"]).send_keys(name)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise UINoSuchElementError(
                "Could not text box to add config_group name")

    def update(self, old_name, new_name=None):
        """
        Updates the config-groups.
        """
        element = self.search(old_name)
        if element:
            element.click()
            if (self.wait_until_element(locators["config_groups.name"]) and
               new_name):
                self.field_update("config_groups.name", new_name)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()

    def search(self, name):
        """
        Searches existing config-groups from UI
        """
        Navigator(self.browser).go_to_config_groups()
        self.wait_for_ajax()
        element = self.search_entity(name,
                                     locators["config_groups.select_name"])
        return element

    def delete(self, name, really, drop_locator=None):
        """
        Deletes the config-groups.
        """

        self.delete_entity(name, really, locators["config_groups.select_name"],
                           locators['config_groups.delete'],
                           drop_locator=drop_locator)
