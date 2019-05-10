# -*- encoding: utf-8 -*-
"""Implements Medium UI."""

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Medium(Base):
    """Implements the CRUD functions for Installation media."""

    def navigate_to_entity(self):
        """Navigate to Medium entity page"""
        Navigator(self.browser).go_to_installation_media()

    def _search_locator(self):
        """Specify locator for Medium entity search procedure"""
        return locators['medium.medium_name']

    def _configure_medium(self, os_family=None):
        """Configures Installation media's OS family."""
        if os_family:
            self.select(locators['medium.os_family'], os_family)

    def create(self, name, path, os_family=None):
        """Creates new Installation media."""
        self.click(locators['medium.new'])
        self.assign_value(locators['medium.name'], name)
        self.assign_value(locators['medium.path'], path)
        self._configure_medium(os_family)
        self.click(common_locators['submit'])

    def update(self, old_name, new_name=None, new_path=None, os_family=None):
        """Update installation media name, media path and OS family."""
        self.search_and_click(old_name)
        self.assign_value(locators['medium.name'], new_name)
        if new_path:
            self.assign_value(locators['medium.path'], new_path)
        self._configure_medium(os_family)
        self.click(common_locators['submit'])
