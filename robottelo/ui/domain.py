# -*- encoding: utf-8 -*-
"""Implements Domain UI"""
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Domain(Base):
    """Manipulates Foreman's domain from UI"""

    def navigate_to_entity(self):
        """Navigate to Domains entity page"""
        Navigator(self.browser).go_to_domains()

    def _search_locator(self):
        """Specify locator for Domains entity search procedure"""
        return locators['domain.domain_description']

    def _configure_domain(self, description=None, dns_proxy=None):
        """Configures domain description and dns proxy"""
        if description:
            self.assign_value(locators['domain.description'], description)
        if dns_proxy:
            self.assign_value(locators['domain.dns_proxy'], dns_proxy)
        self.click(common_locators['submit'])

    def create(self, name, description=None, dns_proxy=None):
        """Creates new domain with name, description and dns_proxy."""
        self.click(locators['domain.new'])
        self.assign_value(locators['domain.name'], name)
        self._configure_domain(description, dns_proxy)

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
        self.search_and_click(old_description)
        self.assign_value(locators['domain.name'], new_name)
        self._configure_domain(description, dns_proxy)

    def set_domain_parameter(
            self, domain_description, param_name, param_value):
        """Add new parameter for domain."""
        self.search_and_click(domain_description)
        self.set_parameter(param_name, param_value)

    def remove_domain_parameter(self, domain_description, param_name):
        """Remove new parameter from domain."""
        self.search_and_click(domain_description)
        self.remove_parameter(param_name)
