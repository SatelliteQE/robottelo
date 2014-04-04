# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Medium UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class Medium(Base):
    """
    Implements the CRUD functions for Installation media
    """

    def _configure_medium(self, os_family=None):
        """
        Configures Installation media's OS family
        """
        if os_family:
            Select(self.find_element(locators
                                     ["medium.os_family"]
                                     )).select_by_visible_text(os_family)

    def create(self, name, path, os_family=None):
        """
        Creates new Installation media
        """

        self.wait_until_element(locators["medium.new"]).click()

        if self.wait_until_element(locators["medium.name"]):
            self.find_element(locators["medium.name"]).send_keys(name)
            if self.wait_until_element(locators["medium.path"]):
                self.find_element(locators["medium.path"]).send_keys(path)
                self._configure_medium(os_family)
                self.find_element(common_locators["submit"]).click()
                self.wait_for_ajax()
            else:
                raise Exception(
                    "Could not create new installation media without path")
        else:
            raise Exception(
                "Could not create new installation media '%s'" % name)

    def search(self, name):
        """
        Searches existing medium from UI
        """
        nav = Navigator(self.browser)
        nav.go_to_installation_media()
        element = self.search_entity(name, locators["medium.medium_name"])
        return element

    def delete(self, name, really):
        """
        Delete Installation media
        """
        self.delete_entity(name, really, locators["medium.medium_name"],
                           locators['medium.delete'])

    def update(self, old_name, new_name=None, new_path=None, os_family=None):
        """
        Update installation media name, media path and OS family
        """
        element = self.search(old_name)

        if element:
            element.click()
            if self.wait_until_element(locators["medium.name"]):
                self.field_update("medium.name", new_name)
            if new_path:
                if self.wait_until_element(locators["medium.path"]):
                    self.field_update("medium.path", new_path)
            self._configure_medium(os_family)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not update the installation media '%s'" % old_name)
