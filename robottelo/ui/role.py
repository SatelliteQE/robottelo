# -*- encoding: utf-8 -*-
"""Implements Roles UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Role(Base):
    """Implements the CRUD functions for Roles."""

    def navigate_to_entity(self):
        """Navigate to Role entity page"""
        Navigator(self.browser).go_to_roles()

    def _search_locator(self):
        """Specify locator for Role entity search procedure"""
        return locators['roles.role']

    def _configure_taxonomies(self, locations=None, organizations=None):
        """Associate role with organization or location"""
        if locations:
            self.configure_entity(locations, FILTER['role_loc'])
        if organizations:
            self.configure_entity(organizations, FILTER['role_org'])

    def create(self, name, locations=None, organizations=None):
        """Creates new Role with default permissions."""
        self.click(locators['roles.new'])
        self.assign_value(locators['roles.name'], name)
        if locations or organizations:
            self._configure_taxonomies(locations, organizations)
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Delete existing role."""
        self.delete_entity(
            name,
            really,
            locators['roles.delete'],
            locators['roles.dropdown'],
        )

    def update(self, name, new_name=None, locations=None, organizations=None):
        """Update role name/location/organization."""
        self.click(self.search(name))
        if new_name:
            self.assign_value(locators['roles.name'], new_name)
        if locations or organizations:
            self._configure_taxonomies(locations, organizations)
        self.click(common_locators['submit'])

    def add_permission(self, role_name, resource_type=None,
                       permission_list=None, override=None,
                       override_check=None, unlimited=None,
                       organization=None, location=None):
        """Add new permission to Role Filter"""
        self.search(role_name)
        self.click(locators['roles.dropdown'] % role_name)
        self.click(locators['roles.add_permission'])
        if resource_type:
            self.assign_value(
                locators['roles.select_resource_type'], resource_type)
        if permission_list:
            self.configure_entity(
                permission_list, FILTER['filter_permission'])
        # Verify whether 'Override' checkbox is present on the page or not.
        # Putting it here as we can do it only during create procedure, not
        # after
        if override_check is True:
            if self.wait_until_element(
                    locators['roles.override']).is_selected():
                raise UIError('Override checkbox has unexpected state')
        # For non-overridable filters, checkbox should be absent at all
        elif override_check is False:
            self.wait_until_element_is_not_visible(locators['roles.override'])
        if override:
            self.assign_value(locators['roles.override'], override)
        if unlimited:
            self.assign_value(locators['roles.unlimited'], unlimited)
        if organization:
            self.click(tab_locators['roles.tab_org'])
            self.configure_entity(organization, FILTER['filter_org'])
        if location:
            self.click(tab_locators['roles.tab_location'])
            self.configure_entity(location, FILTER['filter_loc'])
        self.click(common_locators['submit'])
