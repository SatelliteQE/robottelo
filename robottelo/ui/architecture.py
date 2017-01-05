# -*- encoding: utf-8 -*-
"""Implements Architecture UI"""

from robottelo.constants import FILTER
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Architecture(Base):
    """Manipulates architecture from UI"""

    def navigate_to_entity(self):
        """Navigate to Architecture entity page"""
        Navigator(self.browser).go_to_architectures()

    def _search_locator(self):
        """Specify locator for Architecture entity search procedure"""
        return locators['arch.arch_name']

    def create(self, name, os_names=None):
        """Creates new architecture from UI with existing OS"""
        self.click(locators['arch.new'])
        self.assign_value(locators['arch.name'], name)
        self.configure_entity(os_names, FILTER['arch_os'])
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Delete existing architecture from UI"""
        self.delete_entity(
            name,
            really,
            locators['arch.delete'],
        )

    def update(self, old_name, new_name=None, os_names=None,
               new_os_names=None):
        """Update existing arch's name and OS"""
        self.search_and_click(old_name)
        if new_name:
            self.assign_value(locators['arch.name'], new_name)
        self.configure_entity(
            os_names,
            FILTER['arch_os'],
            new_entity_list=new_os_names
        )
        self.click(common_locators['submit'])
