# -*- encoding: utf-8 -*-
"""
Implements Partition Table UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class PartitionTable(Base):
    """
    Implements the CRUD functions for partition table
    """

    def _configure_partition_table(self, os_family=None):
        """
        Configures the os family of partition table
        """
        if os_family:
            Select(self.find_element(locators
                                     ["ptable.os_family"]
                                     )).select_by_visible_text(os_family)

    def create(self, name, layout=None, os_family=None):
        """
        Creates new partition table from UI
        """

        self.wait_until_element(locators["ptable.new"]).click()

        if self.wait_until_element(locators["ptable.name"]):
            self.find_element(locators["ptable.name"]).send_keys(name)
            if self.wait_until_element(locators["ptable.layout"]):
                self.find_element(locators["ptable.layout"]).send_keys(layout)
                self._configure_partition_table(os_family)
                self.find_element(common_locators["submit"]).click()
                self.wait_for_ajax()
            else:
                raise Exception(
                    "Could not create partition table '%s', \
                    missing layout" % name)
        else:
            raise Exception(
                "Could not create partition table '%s'" % name)

    def search(self, name):
        """
        Searches existing partition table from UI
        """
        Navigator(self.browser).go_to_partition_tables()
        element = self.search_entity(name, locators["ptable.ptable_name"])
        return element

    def delete(self, name, really):
        """
        Removes existing partition table from UI
        """

        self.delete_entity(name, really, locators["ptable.ptable_name"],
                           locators['ptable.delete'])

    def update(self, old_name, new_name=None,
               new_layout=None, os_family=None):
        """
        Updates partition table name, layout and OS family
        """
        element = self.search(old_name)

        if element:
            element.click()
            if self.wait_until_element(locators["ptable.name"]):
                self.field_update("ptable.name", new_name)
            if new_layout:
                if self.wait_until_element(locators["ptable.layout"]):
                    self.field_update("ptable.layout", new_layout)
            self._configure_partition_table(os_family)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not update partition table '%s'" % old_name)
