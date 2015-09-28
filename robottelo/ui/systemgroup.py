# -*- encoding: utf-8 -*-

"""Implements System Groups UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators


class SystemGroup(Base):

    def create(self, name, description=None, limit=None):
        """Creates new System Group from UI"""
        if self.wait_until_element(locators['system-groups.new']):
            # new
            self.click(locators['system-groups.new'])
            self.wait_until_element(locators['system-groups.name'])
            # fill name
            self.field_update('system-groups.name', name)
            # fill description
            if description:
                self.field_update('system-groups.description', description)
            # set limit (unlimited by default)
            if limit:
                self.click(locators['system-groups.unlimited'])
                self.field_update('system-groups.limit', limit)
            # create
            self.click(common_locators['create'])

    def update(self, name, new_name=None, new_description=None, limit=None):
        """Updates existing System Group from UI"""
        system_group = self.search(name)
        self.wait_for_ajax()
        if system_group:
            system_group.click()
            self.wait_for_ajax()

            if new_name:  # update name
                self.edit_entity(locators["system-groups.update_name"],
                                 locators["system-groups.update_name_field"],
                                 new_name,
                                 locators["system-groups.update_name_save"])
            if new_description:  # update description
                self.edit_entity(
                    locators["system-groups.update_description"],
                    locators["system-groups.update_description_field"],
                    new_description,
                    locators["system-groups.update_description_save"]
                )
            if limit:  # update limit
                self.click(locators["system-groups.update_limit"])
                checkbox = self.wait_until_element(
                    locators["system-groups.update_limit_checkbox"])
                # uncheck checkbox when needed
                if checkbox.get_attribute('checked'):
                    checkbox.click()
                self.wait_for_ajax()
                # update field and save
                self.field_update("system-groups.update_limit_field", limit)
                self.click(locators["system-groups.update_limit_save"])

    def remove(self, name):
        """Removes existing System Group from UI"""
        system_group = self.search(name)
        self.wait_for_ajax()
        if system_group:
            system_group.click()
            self.wait_for_ajax()
            self.click(locators["system-groups.remove"])
            self.click(locators["system-groups.confirm_remove"])

    def search(self, name):
        """Searches existing System Group from UI"""
        return self.search_entity(
            name, locators['system-groups.search'], katello=True)
