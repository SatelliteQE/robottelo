# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Architecture UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators


class Architecture(Base):
    """
    Manipulates architecture from UI
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def create(self, name, os_name=None):
        """
        Creates new architecture from UI with existing OS
        """

        self.wait_until_element(locators["arch.new"]).click()

        if self.wait_until_element(locators["arch.name"]):
            self.field_update("arch.name", name)
        if os_name:
            self.select_entity("arch.os_name", "arch.select_os_name",
                               os_name, None)
        self.find_element(common_locators["submit"]).click()
        self.wait_for_ajax()

    def search(self, name):
        """
        Searches existing architecture from UI
        """
        self.search_entity(name, locators['arch.arch_name'])

    def delete(self, name, really):
        """
        Delete existing architecture from UI
        """

        self.delete_entity(name, really, locators['arch.arch_name'],
                           locators['arch.delete'])

    def update(self, oldname, newname, new_osname):
        """
        Update existing arch's name and OS
        """

        element = self.search(oldname)

        if element:
            element.click()
            if self.wait_until_element(locators["arch.name"]):
                self.field_update("arch.name", newname)
            if new_osname:
                self.select_entity("arch.os_name", "arch.select_os_name",
                                   new_osname, None)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
