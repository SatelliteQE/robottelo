# -*- encoding: utf-8 -*-
"""Implements Medium UI."""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


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
            Select(
                self.find_element(locators['medium.os_family'])
            ).select_by_visible_text(os_family)

    def create(self, name, path, os_family=None):
        """Creates new Installation media."""
        self.click(locators['medium.new'])

        if self.wait_until_element(locators['medium.name']):
            self.find_element(locators['medium.name']).send_keys(name)
            if self.wait_until_element(locators['medium.path']):
                self.find_element(locators['medium.path']).send_keys(path)
                self._configure_medium(os_family)
                self.click(common_locators['submit'])
            else:
                raise UIError(
                    'Could not create new installation media without path'
                )
        else:
            raise UIError(
                'Could not create new installation media "{0}"'.format(name)
            )

    def delete(self, name, really=True):
        """Delete Installation media."""
        self.delete_entity(
            name,
            really,
            locators['medium.delete'],
        )

    def update(self, old_name, new_name=None, new_path=None, os_family=None):
        """Update installation media name, media path and OS family."""
        element = self.search(old_name)

        if element:
            element.click()
            if self.wait_until_element(locators['medium.name']):
                self.field_update('medium.name', new_name)
            if new_path:
                if self.wait_until_element(locators['medium.path']):
                    self.field_update('medium.path', new_path)
            self._configure_medium(os_family)
            self.click(common_locators['submit'])
        else:
            raise UIError(
                'Could not update the installation media "{0}"'
                .format(old_name)
            )
