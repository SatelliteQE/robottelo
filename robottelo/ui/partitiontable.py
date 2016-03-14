# -*- encoding: utf-8 -*-
"""Implements Partition Table UI."""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class PartitionTable(Base):
    """Implements the CRUD functions for partition table."""

    def navigate_to_entity(self):
        """Navigate to Partition Table entity page"""
        Navigator(self.browser).go_to_partition_tables()

    def _search_locator(self):
        """Specify locator for Partition Table entity search procedure"""
        return locators['ptable.ptable_name']

    def _configure_partition_table(self, os_family=None):
        """Configures the os family of partition table."""
        if os_family:
            self.select(locators['ptable.os_family'], os_family)

    def create(self, name, template_path=None, os_family=None,
               custom_really=True):
        """Creates new partition table from UI."""
        self.click(locators['ptable.new'])

        if self.wait_until_element(locators['ptable.name']) is None:
            raise UIError(
                u'Could not create partition table "{0}"'.format(name)
            )
        self.find_element(locators['ptable.name']).send_keys(name)
        if template_path:
            self.find_element(
                locators['ptable.layout_template']
            ).send_keys(template_path)
            self.handle_alert(custom_really)
        self._configure_partition_table(os_family)
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Removes existing partition table from UI."""
        self.delete_entity(
            name,
            really,
            locators['ptable.delete'],
            drop_locator=locators['ptable.dropdown'],
        )

    def update(self, old_name, new_name=None, new_template_path=None,
               new_os_family=None, custom_really=True):
        """Updates partition table name, layout and OS family."""
        element = self.search(old_name)
        if element is None:
            raise UIError(
                u'Could not update partition table "{0}"'.format(old_name)
            )
        self.click(element)
        if new_name:
            self.wait_until_element(locators['ptable.name'])
            self.field_update('ptable.name', new_name)
        if new_template_path:
            self.wait_until_element(locators['ptable.layout_template'])
            self.find_element(
                locators['ptable.layout_template']
            ).send_keys(new_template_path)
            self.handle_alert(custom_really)
        if new_os_family:
            self._configure_partition_table(new_os_family)
        self.click(common_locators['submit'])
