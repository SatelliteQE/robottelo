# -*- encoding: utf-8 -*-
"""Implements Partition Table UI."""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class PartitionTable(Base):
    """Implements the CRUD functions for partition table."""

    def _configure_partition_table(self, os_family=None):
        """Configures the os family of partition table."""
        if os_family:
            Select(
                self.find_element(locators['ptable.os_family'])
            ).select_by_visible_text(os_family)

    def create(self, name, layout=None, os_family=None):
        """Creates new partition table from UI."""
        self.click(locators['ptable.new'])

        if self.wait_until_element(locators['ptable.name']):
            self.find_element(locators['ptable.name']).send_keys(name)
            if self.wait_until_element(locators['ptable.layout']):
                self.find_element(locators['ptable.layout']).send_keys(layout)
                self._configure_partition_table(os_family)
                self.click(common_locators['submit'])
            else:
                raise UIError(
                    'Could not create partition table "{0}", missing layout'
                    .format(name)
                )
        else:
            raise UIError(
                'Could not create partition table "{0}"'.format(name)
            )

    def search(self, name):
        """Searches existing partition table from UI."""
        Navigator(self.browser).go_to_partition_tables()
        return self.search_entity(name, locators['ptable.ptable_name'])

    def delete(self, name, really=True):
        """Removes existing partition table from UI."""
        self.delete_entity(
            name,
            really,
            locators['ptable.ptable_name'],
            locators['ptable.delete'],
        )

    def update(self, old_name, new_name=None,
               new_layout=None, os_family=None):
        """Updates partition table name, layout and OS family."""
        element = self.search(old_name)

        if element:
            element.click()
            if self.wait_until_element(locators['ptable.name']):
                self.field_update('ptable.name', new_name)
            if new_layout:
                if self.wait_until_element(locators['ptable.layout']):
                    self.field_update('ptable.layout', new_layout)
            self._configure_partition_table(os_family)
            self.click(common_locators['submit'])
        else:
            raise UIError(
                'Could not update partition table "{0}"'.format(old_name)
            )
