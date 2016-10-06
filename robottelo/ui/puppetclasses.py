"""Implements Puppet Classes UI"""

from robottelo.ui.base import Base, UINoSuchElementError
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
        if self.wait_until_element(locators['puppetclass.name']):
            self.find_element(locators['puppetclass.name']).send_keys(name)
        if environment:
            self.find_element(
                locators['puppetclass.environments']).send_keys(environment)
        self.click(common_locators['submit'])

    def update(self, old_name, new_name=None, new_env=None):
        """Updates the Puppet-classes."""
        element = self.get_entity(old_name)
        if element:
            element.click()
            if (self.wait_until_element(locators['puppetclass.name']) and
               new_name):
                self.field_update('puppetclass.name', new_name)
            if new_env:
                self.text_field_update(locators['puppetclass.environments'],
                                       new_env)
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

    def update_class_parameter_description(
            self, class_name=None, parameter_name=None, description=None):
        """Updates the description field of a given puppet class parameter."""
        puppet_class = self.get_entity(class_name)
        if puppet_class is None:
            raise UINoSuchElementError(
                "Couldn't find the puppet class '{0}'.".format(class_name)
            )
        puppet_class.click()
        if self.wait_until_element(tab_locators['puppetclass.parameters']):
            self.click(tab_locators['puppetclass.parameters'])
        if self.wait_until_element(
            locators['puppetclass.paramfilter']
        ) and parameter_name:
            self.field_update('puppetclass.paramfilter', parameter_name)
        if self.wait_until_element(
            locators['puppetclass.param_description']
        ) and description:
            self.field_update('puppetclass.param_description', description)
        self.click(common_locators['submit'])

    def fetch_class_parameter_description(
            self, class_name=None, parameter_name=None):
        """Fetches the description of a given puppet class parameter."""
        description = None
        puppet_class = self.get_entity(class_name)
        if puppet_class is None:
            raise UINoSuchElementError(
                "Couldn't find the puppet class '{0}'.".format(class_name)
            )
        puppet_class.click()
        self.wait_for_ajax()
        self.click(tab_locators['puppetclass.parameters'])
        if self.wait_until_element(
            locators['puppetclass.paramfilter']
        ) and parameter_name:
            self.field_update('puppetclass.paramfilter', parameter_name)
        if self.wait_until_element(
            locators['puppetclass.param_description']
        ):
            description = self.find_element(
                locators['puppetclass.param_description']
            ).text
        self.click(locators['puppetclass.cancel'])
        return description
