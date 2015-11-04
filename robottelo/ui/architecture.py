# -*- encoding: utf-8 -*-
"""Implements Architecture UI"""

from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class Architecture(Base):
    """Manipulates architecture from UI"""

    def create(self, name, os_names=None):
        """Creates new architecture from UI with existing OS"""
        self.click(locators['arch.new'])

        if self.wait_until_element(locators['arch.name']):
            self.field_update('arch.name', name)
            self.configure_entity(os_names, FILTER['arch_os'])
            self.click(common_locators['submit'])
        else:
            raise UIError(
                'Could not create new architecture "{0}"'.format(name)
            )

    def search(self, name):
        """Searches existing architecture from UI"""
        Navigator(self.browser).go_to_architectures()
        return self.search_entity(name, locators['arch.arch_name'])

    def delete(self, name, really=True):
        """Delete existing architecture from UI"""
        self.delete_entity(
            name,
            really,
            locators['arch.arch_name'],
            locators['arch.delete'],
        )

    def update(self, old_name, new_name=None, os_names=None,
               new_os_names=None):
        """Update existing arch's name and OS"""
        element = self.search(old_name)

        if element:
            element.click()
            if self.wait_until_element(locators['arch.name']) and new_name:
                self.field_update('arch.name', new_name)
                self.configure_entity(
                    os_names,
                    FILTER['arch_os'],
                    new_entity_list=new_os_names
                )
                self.click(common_locators['submit'])
        else:
            raise UIError(
                'Could not update the architecture "{0}"'.format(old_name)
            )
