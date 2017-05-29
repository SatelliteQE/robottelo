# -*- encoding: utf-8 -*-
"""Implements Partition Table UI."""

from robottelo.ui.base import Base
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

    def _configure_partition_table(self, audit_comment=None, default=None,
                                   os_family=None, snippet=None):
        """Configures the optional parameters of partition table."""
        if audit_comment:
            self.assign_value(locators['ptable.audit_comment'], audit_comment)
        if default is not None:
            self.assign_value(locators['ptable.default_template'], default)
        if os_family:
            self.assign_value(locators['ptable.os_family'], os_family)
        if snippet:
            self.assign_value(locators['ptable.snippet'], snippet)

    def create(self, name, audit_comment=None, default=False,
               template_path=None, os_family=None, snippet=None):
        """Creates new partition table from UI."""
        self.click(locators['ptable.new'])
        self.assign_value(locators['ptable.name'], name)
        if template_path:
            self.wait_until_element(
                locators['ptable.layout_template']).send_keys(template_path)
            self.handle_alert(True)
        self._configure_partition_table(
            audit_comment=audit_comment,
            default=default,
            os_family=os_family,
            snippet=snippet,
        )
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Removes existing partition table from UI."""
        self.delete_entity(
            name,
            really,
            common_locators['delete_button'],
            drop_locator=locators['ptable.dropdown'],
        )

    def update(self, old_name, new_name=None, new_template_path=None,
               new_os_family=None, audit_comment=None, default=None,
               snippet=None):
        """Updates partition table parameters"""
        self.search_and_click(old_name)
        if new_name:
            self.assign_value(locators['ptable.name'], new_name)
        if new_template_path:
            self.wait_until_element(
                locators['ptable.layout_template']
            ).send_keys(new_template_path)
            self.handle_alert(True)
        self._configure_partition_table(
            audit_comment=audit_comment,
            default=default,
            os_family=new_os_family,
            snippet=snippet,
        )
        self.click(common_locators['submit'])
