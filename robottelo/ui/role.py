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
        self.click(common_locators['select_action_dropdown'] % role_name)
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

    def filters_get_resources(self, role_name):
        """Fetch resources from role filters.

        :param role_name: String with role name.
        :return: List of strings with resource names.
        """
        self.search(role_name)
        self.click(locators['roles.filters_button'] % role_name)
        # make sure The role filter page is loaded
        self.wait_until_element(locators['role_filters.title'])
        resources = [
            resource.text for resource in
            self.find_elements(locators['role_filters.resources'])
        ]
        next_ = self.find_element(locators['role_filters.pagination_next'])
        while next_:
            self.click(next_)
            self.wait_until_element(locators["role_filters.results_ready"])
            resources.extend(
                [resource.text for resource in
                 self.find_elements(locators['role_filters.resources'])])
            next_ = self.find_element(locators['role_filters.pagination_next'])
        # return only unique values
        return list(set(resources))

    def _get_page_resources_permissions(self, resource_types, permissions):
        """Retrieve the permissions for each resource type in resource_types
        on Role Filters page.

         :param resource_types: the list of resource types to check on the
            current page.
        :param  permissions: a dict store to register the resource permissions
            found.

        Note: The resource is removed from resource_types when found
        """
        self.wait_until_element(locators["role_filters.results_ready"])
        resources = {
            resource.text for resource in
            self.find_elements(locators['role_filters.resources'])
            }
        for res_type in resources:
            if res_type in resource_types:
                perm_elements = self.find_elements(
                    locators['role_filters.permissions'] % res_type)
                for perm_element in perm_elements:
                    if res_type not in permissions:
                        permissions[res_type] = []
                    perms = [
                        perm
                        for perm in perm_element.text.split(', ')
                        if perm and perm not in permissions[res_type]
                    ]
                    permissions[res_type].extend(perms)

    def filters_get_permissions(self, role_name, resource_types):
        """Fetch permissions for provided resource types from role filters.

        :param role_name: String with role name.
        :param resource_types: List with resource types names.
        :return: Dict with resource name as a key and list of strings with
            permissions names as a values.
        """
        self.search(role_name)
        self.click(locators['roles.filters_button'] % role_name)
        # make sure The role filter page is loaded
        self.wait_until_element(locators['role_filters.title'])
        permissions = {}
        # create a copy of unique resources types
        resource_types = list(set(resource_types))
        self._get_page_resources_permissions(resource_types, permissions)
        next_ = self.find_element(locators['role_filters.pagination_next'])
        while resource_types and next_:
            self.click(next_)
            self._get_page_resources_permissions(resource_types, permissions)
            next_ = self.find_element(locators['role_filters.pagination_next'])
        missing_resource_types = set(resource_types).difference(
            set(permissions.keys()))
        if missing_resource_types:
            raise UIError(
                'Not all resource types where found: {0} are missing'
                .format(', '.join(missing_resource_types))
            )
        return permissions

    def get_permissions(self, role_name):
        """Fetch all assigned permissions from role page.

        :param role_name: String with role name.
        :return: Dict with resource name as a key and list of strings with
            permissions names as a values.
        """
        self.search_and_click(role_name)
        self.click(tab_locators['roles.tab_filters'])
        dict_permissions = {}
        while True:
            resources = [
                resource.text for resource in
                self.find_elements(locators['roles.resources'])
            ]
            permissions = [
                filter_.text for filter_ in
                self.find_elements(locators['roles.permissions'] % '')
            ]
            for res_type, perms in zip(resources, permissions):
                if res_type not in dict_permissions:
                    dict_permissions[res_type] = []
                dict_permissions[res_type] += perms.split(', ')
            next_ = self.find_element(
                locators["roles.filters.pagination_next"])
            if not next_:
                break
            self.click(next_)
        return dict_permissions

    def clone(self, name, new_name, locations=None, organizations=None):
        """Clone role with name/location/organization."""
        self.search(name)
        if self.find_element(locators['roles.locked'] % name):
            self.click(locators['roles.locked_dropdown'] % name)
        else:
            self.click(common_locators['select_action_dropdown'] % name)
        self.click(locators['roles.clone'])
        self.assign_value(locators['roles.name'], new_name)
        if locations or organizations:
            self._configure_taxonomies(locations, organizations)
        self.click(common_locators['submit'])
