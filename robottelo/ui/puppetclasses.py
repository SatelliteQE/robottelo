"""Implements Puppet Classes UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class PuppetClasses(Base):
    """Provides the CRUD functionality for Puppet-classes."""

    def navigate_to_entity(self):
        """Navigate to Puppet Classes entity page"""
        Navigator(self.browser).go_to_puppet_classes()

    def _search_locator(self):
        """Specify locator for Puppet Classes entity search procedure"""
        return locators['puppetclass.select_name']

    def create(self, name, environment=None):
        """Creates the Puppet-classes."""
        self.click(locators['puppetclass.new'])
        self.assign_value(locators['puppetclass.name'], name)
        self.assign_value(locators['puppetclass.environments'], environment)
        self.click(common_locators['submit'])

    def update(self, old_name, new_name=None, new_env=None):
        """Updates the Puppet-classes."""
        self.search_and_click(old_name)
        if new_name:
            self.assign_value(locators['puppetclass.name'], new_name)
        if new_env:
            self.assign_value(locators['puppetclass.environments'], new_env)
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Deletes the puppet-classes."""
        self.delete_entity(
            name,
            really,
            locators['puppetclass.delete'],
        )

    def import_scap_client_puppet_classes(self):
        """Imports puppet-foreman_scap_client puppet classes."""
        Navigator(self.browser).go_to_puppet_classes()
        self.click(locators['puppetclass.import'])
        # Checking if the scap client puppet classes are already imported
        if self.wait_until_element(
                locators['puppetclass.environment_default_check']):
            self.click(locators['puppetclass.environment_default_check'])
            self.click(locators['puppetclass.update'])
        else:
            self.click(locators['puppetclass.cancel'])

    def update_class_parameter(
            self, class_name=None, parameter_name=None, description=None):
        """Updates given puppet class parameter."""
        self.search_and_click(class_name)
        self.click(tab_locators['puppetclass.parameters'])
        if parameter_name:
            self.assign_value(
                locators['puppetclass.paramfilter'], parameter_name)
        if description:
            self.assign_value(
                locators['puppetclass.param_description'], description)
        self.click(common_locators['submit'])

    def fetch_class_parameter_description(
            self, class_name=None, parameter_name=None):
        """Fetches the description of a given puppet class parameter."""
        self.search_and_click(class_name)
        self.click(tab_locators['puppetclass.parameters'])
        if parameter_name:
            self.assign_value(
                locators['puppetclass.paramfilter'], parameter_name)
        description = self.wait_until_element(
            locators['puppetclass.param_description']).text
        self.click(locators['puppetclass.cancel'])
        return description
