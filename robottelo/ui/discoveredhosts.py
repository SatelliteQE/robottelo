# -*- encoding: utf-8 -*-
"""Implements Discovered Hosts from UI."""
from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class DiscoveredHosts(Base):
    """Manipulates Discovered Hosts from UI"""

    def search(self, host_name):
        """Searches existing discovered hosts from UI"""
        Navigator(self.browser).go_to_discovered_hosts()
        strategy, value = locators['discoveredhosts.hostname']
        return self.wait_until_element((strategy, value % host_name))

    def delete(self, hostname, really=True):
        """Delete existing discovered hosts from UI"""
        Navigator(self.browser).go_to_discovered_hosts()
        self.delete_entity(
            hostname,
            really,
            locators['discoveredhosts.hostname'],
            locators['discoveredhosts.delete'],
            locators['discoveredhosts.dropdown'],
        )
