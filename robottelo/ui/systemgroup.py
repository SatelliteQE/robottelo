# -*- encoding: utf-8 -*-

"""Implements System Groups UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class SystemGroup(Base):
    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Host Collection entity page"""
        Navigator.go_to_host_collections()

    def _search_locator(self):
        """Specify locator for Host Collection entity search procedure"""
        return locators['system-groups.search']

    def create(self, name, description=None, limit=None):
        """Creates new System Group from UI"""
        # new
        self.click(locators['system-groups.new'])
        # fill name
        self.assign_value(locators['system-groups.name'], name)
        # fill description
        if description:
            self.assign_value(
                locators['system-groups.description'], description)
        # set limit (unlimited by default)
        if limit:
            self.click(locators['system-groups.unlimited'])
            self.assign_value(locators['system-groups.limit'], limit)
        # create
        self.click(common_locators['create'])

    def update(self, name, new_name=None, new_description=None, limit=None):
        """Updates existing System Group from UI"""
        self.search_and_click(name)
        if new_name:  # update name
            self.edit_entity(
                locators["system-groups.update_name"],
                locators["system-groups.update_name_field"],
                new_name,
                locators["system-groups.update_name_save"]
            )
        if new_description:  # update description
            self.edit_entity(
                locators["system-groups.update_description"],
                locators["system-groups.update_description_field"],
                new_description,
                locators["system-groups.update_description_save"]
            )
        if limit:  # update limit
            self.click(locators["system-groups.update_limit"])
            # uncheck checkbox when needed
            self.assign_value(
                locators["system-groups.update_limit_checkbox"], False)
            # update field and save
            self.assign_value(
                locators["system-groups.update_limit_field"], limit)
            self.click(locators["system-groups.update_limit_save"])

    def delete(self, name, really=True):
        """Removes existing System Group from UI"""
        self.delete_entity(
            name,
            really,
            locators['system-groups.remove'],
        )
