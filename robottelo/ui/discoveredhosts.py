# -*- encoding: utf-8 -*-
"""Implements Discovered Hosts from UI."""
from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class DiscoveredHosts(Base):
    """Manipulates Discovered Hosts from UI"""

    def navigate_to_entity(self):
        """Navigate to Discovered Hosts entity page"""
        Navigator(self.browser).go_to_discovered_hosts()

    def _search_locator(self):
        """Specify locator for Discovered Hosts entity search procedure"""
        return locators["discoveredhosts.hostname"]

    def delete(self, hostname, really=True):
        """Delete existing discovered hosts from UI"""
        Navigator(self.browser).go_to_discovered_hosts()
        self.delete_entity(
            hostname,
            really,
            locators['discoveredhosts.delete'],
            locators['discoveredhosts.dropdown'],
        )
