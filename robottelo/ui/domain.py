# -*- encoding: utf-8 -*-
"""Implements Domain UI"""
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Domain(Base):
    """Manipulates Foreman's domain from UI"""

    def _configure_domain(self, description=None, dns_proxy=None):
        """Configures domain description and dns proxy"""

        if description:
            if self.wait_until_element(locators['domain.description']):
                self.field_update('domain.description', description)
        if dns_proxy:
            self.select(locators['domain.dns_proxy'], dns_proxy)
        self.click(common_locators['submit'])

    def create(self, name, description=None, dns_proxy=None):
        """Creates new domain with name, description and dns_proxy."""
        self.click(locators['domain.new'])

        if self.wait_until_element(locators['domain.name']):
            self.find_element(locators['domain.name']).send_keys(name)
            self._configure_domain(description, dns_proxy)
        else:
            raise UIError(
                'Could not create new domain "{0}"'.format(name)
            )

    def navigate_to_entity(self):
        """Navigate to Domains entity page"""
        Navigator(self.browser).go_to_domains()

    def _search_locator(self):
        """Specify locator for Domains entity search procedure"""
        return locators['domain.domain_description']

    def delete(self, description, really=True):
        """Delete existing domain from UI"""
        self.delete_entity(
            description,
            really,
            locators['domain.delete'],
        )

    def update(self, old_description, new_name=None, description=None,
               dns_proxy=None):
        """Update an existing domain's name, description and dns_proxy."""
        element = self.search(old_description)
        self.click(element)
        if self.wait_until_element(locators['domain.name']):
            self.field_update('domain.name', new_name)
        self._configure_domain(description, dns_proxy)

    def set_domain_parameter(
            self, domain_description, param_name, param_value):
        """Add new parameter for domain."""
        element = self.search(domain_description)
        self.click(element)
        self.set_parameter(param_name, param_value)

    def remove_domain_parameter(self, domain_description, param_name):
        """Remove new parameter from domain."""
        element = self.search(domain_description)
        self.click(element)
        self.remove_parameter(param_name)
