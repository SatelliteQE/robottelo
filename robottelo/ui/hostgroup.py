# -*- encoding: utf-8 -*-
"""Implements Host Group UI."""
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class Hostgroup(Base):
    """Manipulates hostgroup from UI."""

    def create(self, name, parent=None, environment=None):
        """Creates a new hostgroup from UI."""
        self.click(locators['hostgroups.new'])

        if self.wait_until_element(locators['hostgroups.name']):
            self.find_element(locators['hostgroups.name']).send_keys(name)
            if parent:
                Select(self.find_element(
                    locators['hostgroups.parent'])
                ).select_by_visible_text(parent)
            if environment:
                Select(self.find_element(
                    locators['hostgroups.environment'])
                ).select_by_visible_text(environment)
            self.click(common_locators['submit'])
        else:
            raise UIError('Could not create new hostgroup.')

    def search(self, name):
        """Searches existing hostgroup from UI."""
        Navigator(self.browser).go_to_host_groups()
        element = self.search_entity(name, locators['hostgroups.hostgroup'])
        return element

    def delete(self, name, really=True):
        """Deletes existing hostgroup from UI."""
        Navigator(self.browser).go_to_host_groups()
        self.delete_entity(
            name,
            really,
            locators['hostgroups.hostgroup'],
            locators['hostgroups.delete'],
            drop_locator=locators['hostgroups.dropdown']
        )

    def update(self, name, new_name=None, parent=None, environment=None):
        """Updates existing hostgroup from UI."""
        element = self.search(name)

        if element:
            element.click()
            self.wait_for_ajax()
            if parent:
                Select(self.find_element(
                    locators['hostgroups.parent'])
                ).select_by_visible_text(parent)
            if environment:
                Select(self.find_element(
                    locators['hostgroups.environment'])
                ).select_by_visible_text(environment)
            if new_name:
                self.field_update('hostgroups.name', new_name)
            self.click(common_locators['submit'])
        else:
            raise UIError('Could not find hostgroup "{0}"'.format(name))
