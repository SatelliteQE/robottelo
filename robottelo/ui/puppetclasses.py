"""
Implements Puppet Classes UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator


class PuppetClasses(Base):
    """
    Provides the CRUD functionality for Puppet-classes.
    """

    def create(self, name, environment=None):
        """
        Creates the Puppet-classes.
        """
        self.wait_until_element(locators["puppetclass.new"]).click()
        if self.wait_until_element(locators["puppetclass.name"]):
            self.find_element(locators["puppetclass.name"]).send_keys(name)
        if environment:
            self.find_element(
                locators['puppetclass.environments']).send_keys(environment)
        self.find_element(common_locators["submit"]).click()
        self.wait_for_ajax()

    def update(self, old_name, new_name=None, new_env=None):
        """
        Updates the Puppet-classes.
        """
        element = self.search(old_name)
        if element:
            element.click()
            if (self.wait_until_element(locators["puppetclass.name"]) and
               new_name):
                self.field_update("puppetclass.name", new_name)
            if new_env:
                self.text_field_update(locators['puppetclass.environments'],
                                       new_env)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()

    def search(self, name):
        """
        Searches existing puppet-classes from UI
        """
        Navigator(self.browser).go_to_puppet_classes()
        self.wait_for_ajax()
        element = self.search_entity(name,
                                     locators["puppetclass.select_name"])
        return element

    def delete(self, name, really):
        """
        Deletes the puppet-classes.
        """

        self.delete_entity(name, really, locators["puppetclass.select_name"],
                           locators['puppetclass.delete'])
