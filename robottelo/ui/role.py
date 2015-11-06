# -*- encoding: utf-8 -*-
"""Implements Roles UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class Role(Base):
    """Implements the CRUD functions for Roles."""

    def navigate_to_entity(self):
        """Navigate to Role entity page"""
        Navigator(self.browser).go_to_roles()

    def _search_locator(self):
        """Specify locator for Role entity search procedure"""
        return locators['roles.role']

    def create(self, name):
        """Creates new Role with default permissions."""
        self.click(locators['roles.new'])

        if self.wait_until_element(locators['roles.name']):
            self.find_element(locators['roles.name']).send_keys(name)
            self.click(common_locators['submit'])
        else:
            raise UIError(
                'Could not create new role "{0}"'.format(name)
            )

    def delete(self, name, really=True):
        """Delete existing role."""
        self.delete_entity(
            name,
            really,
            locators['roles.delete'],
            locators['roles.dropdown'],
        )

    def update(self, name, new_name=None, add_permission=False,
               resource_type=None, permission_list=None, organization=None):
        """Update role name/permissions/org."""
        element = self.search(name)

        if element is None:
            raise UIError('Could not find role "{0}"'.format(name))
        if new_name:
            element.click()
            if self.wait_until_element(locators['roles.name']):
                self.field_update('roles.name', new_name)
        if add_permission:
            strategy, value = locators['roles.dropdown']
            self.click((strategy, value % name))
            self.click(locators['roles.add_permission'])
            if resource_type:
                Select(
                    self.find_element(
                        locators['roles.select_resource_type'])
                ).select_by_visible_text(resource_type)
                if permission_list:
                    self.configure_entity(
                        permission_list, FILTER['role_permission'])
            if organization:
                self.click(tab_locators['roles.tab_org'])
                self.configure_entity(organization, FILTER['role_org'])
        self.click(common_locators['submit'])
