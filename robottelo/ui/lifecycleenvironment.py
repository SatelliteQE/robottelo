# -*- encoding: utf-8 -*-
"""Implements Lifecycle content environments."""

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class LifecycleEnvironment(Base):
    """Manipulates lifecycle environments from UI."""

    def navigate_to_entity(self):
        """Navigate to Lifecycle Environment entity page"""
        Navigator(self.browser).go_to_life_cycle_environments()

    def _search_locator(self):
        """Specify locator for Lifecycle Environment entity search procedure"""
        return locators['content_env.select_name']

    def create(self, name, description=None, prior=None):
        """Creates new life cycle environment."""
        if prior:
            self.click(locators['content_env.env_link'] % prior)
        else:
            self.click(locators['content_env.new'])
        self.assign_value(common_locators['name'], name)
        if description:
            self.assign_value(common_locators['description'], description)
        self.click(common_locators['create'])

    def search(self, name):
        """Search for an existing environment. It is necessary to use custom
        search here as we don't have search bar, search button and entities
        list.
        """
        self.navigate_to_entity()
        return self.wait_until_element(self._search_locator() % name)

    def delete(self, name):
        """Deletes an existing environment. We don't have confirmation dialog
        for current operation, so it is necessary to use custom method
        """
        self.search_and_click(name)
        self.click(locators['content_env.remove'])

    def update(self, name, new_name=None, description=None):
        """Updates an existing environment."""
        self.search_and_click(name)
        if new_name:
            self.edit_entity(
                locators['content_env.edit_name'],
                locators['content_env.edit_name_text'],
                new_name,
                common_locators['save']
            )
        if description:
            self.edit_entity(
                locators['content_env.edit_description'],
                locators['content_env.edit_description_textarea'],
                description,
                common_locators['save']
            )

    def fetch_puppet_module(self, lce_name, module_name, cv_name=None):
        """Get added puppet module name from selected lifecycle environment and
        content-view
        """
        self.search_and_click(lce_name)
        self.click(tab_locators['lce.tab_puppet_modules'])
        if cv_name:
            self.assign_value(
                locators['content_env.puppet_module.select_cv'], cv_name)
        self.assign_value(common_locators['kt_search'], module_name)
        self.click(common_locators['kt_search_button'])
        return self.wait_until_element(
            locators['content_env.puppet_module.get_name'] % module_name)

    def get_package_names(self, lce_name, search_string, cv_name=None):
        """Get yum package names from selected lifecycle environment and
        content-view

        :param lce_name: the Lifecycle environment name
        :param search_string: a string to search by the package names
        :param cv_name: the content view name if applicable
        """
        self.search_and_click(lce_name)
        self.click(tab_locators['lce.tab_packages'])
        if cv_name:
            self.assign_value(
                locators['content_env.package.select_cv'], cv_name)
        self.assign_value(common_locators['kt_search'], search_string)
        self.click(common_locators['kt_search_button'])
        return [element.text for element in
                self.find_elements(locators['content_env.package.get_names'])]
