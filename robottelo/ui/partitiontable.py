# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Partition Table UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators
from selenium.webdriver.support.select import Select


class PartitionTable(Base):
    """
    Implements the CRUD functions for partition table
    """

    def __init__(self, browser):
        """
        Sets the browser object
        """
        self.browser = browser

    def create(self, name, layout=None, os_family=None):
        """
        Creates new partition table from UI
        """

        self.wait_until_element(locators["ptable.new"]).click()

        if self.wait_until_element(locators["ptable.name"]):
            self.find_element(locators["ptable.name"]).send_keys(name)
            if self.wait_until_element(locators["ptable.layout"]):
                self.find_element(locators["ptable.layout"]).send_keys(layout)
            if os_family:
                Select(self.find_element(locators
                                         ["ptable.os_family"]
                                         )).select_by_visible_text(os_family)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()

    def search(self, name):
        """
        Searches existing partition table from UI
        """
        self.search_entity(name, locators["ptable.ptable_name"])

    def delete(self, name, really):
        """
        Removes existing partition table from UI
        """

        self.delete_entity(name, really, locators["ptable.ptable_name"],
                           locators['ptable.delete'])

    def update(self, oldname, new_name=None,
               new_layout=None, new_os_family=None):
        """
        Updates partition table name, layout and OS family
        """

        element = self.search(oldname)

        if element:
            element.click()
        if self.wait_until_element(locators["ptable.name"]):
            self.field_update("ptable.name", new_name)
        if new_layout:
            if self.wait_until_element(locators["ptable.layout"]):
                self.field_update("ptable.layout", new_layout)
        if new_os_family:
            Select(self.find_element(locators
                                     ["ptable.os_family"]
                                     )).select_by_visible_text(new_os_family)
        self.find_element(common_locators["submit"]).click()
        self.wait_for_ajax()
