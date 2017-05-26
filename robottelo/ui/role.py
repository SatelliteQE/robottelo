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
                self.select(
                    locators['roles.select_resource_type'], resource_type)
                if permission_list:
                    self.configure_entity(
                        permission_list, FILTER['role_permission'])
            if organization:
                self.click(tab_locators['roles.tab_org'])
                self.configure_entity(organization, FILTER['role_org'])
        self.click(common_locators['submit'])

    def add_permission(self, role_name, resource_type=None,
                       permission_list=None):
        """Add new permission to Role Filter"""
        self.search(role_name)
        strategy, value = locators['roles.dropdown']
        self.click((strategy, value % role_name))
        self.click(locators['roles.add_permission'])
        if resource_type:
            self.assign_value(
                locators['roles.select_resource_type'], resource_type)
        if permission_list:
            self.configure_entity(
                permission_list, FILTER['filter_permission'])
        self.click(common_locators['submit'])

    def get_resources(self, role_name):
        """Fetch resources from role filters.

        :param role_name: String with role name.
        :return: List of strings with resource names.
        """
        self.search_and_click(role_name)
        self.click(tab_locators['roles.tab_filters'])
        resources = [
            resource.text for resource in
            self.find_elements(locators['roles.resources'])
        ]
        next_ = self.find_element(locators["roles.filters.pagination_next"])
        while next_:
            self.click(next_)
            next_ = self.find_element(
                locators["roles.filters.pagination_next"])
            resources.extend(
                [resource.text for resource in
                    self.find_elements(locators['roles.resources'])])
        return resources

    def get_permissions(self, role_name, resource_types):
        """Fetch permissions for provided resource types from role filters.

        :param role_name: String with role name.
        :param resource_types: List with resource types names.
        :return: Dict with resource name as a key and list of strings with
            permissions names as a values.
        """
        self.search_and_click(role_name)
        self.click(tab_locators['roles.tab_filters'])
        dict_permissions = {}
        for res_type in resource_types:
            self.assign_value(locators["roles.filters.search"], res_type)
            strategy, value = locators['roles.permissions']
            permissions = self.wait_until_element((strategy, value % res_type))
            if permissions:
                dict_permissions[res_type] = permissions.text.split(', ')
        return dict_permissions

    def clone(self, name, new_name, locations=None, organizations=None):
        """Clone role with name/location/organization."""
        self.search(name)
        strategy, value = locators['roles.dropdown']
        self.click((strategy, value % name))
        self.click(locators['roles.clone'])
        self.assign_value(locators['roles.name'], new_name)
        if locations or organizations:
            self._configure_taxonomies(locations, organizations)
        self.click(common_locators['submit'])
