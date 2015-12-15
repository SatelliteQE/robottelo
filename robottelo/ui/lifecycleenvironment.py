# -*- encoding: utf-8 -*-
"""Implements Lifecycle content environments."""

from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators
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
            strategy, value = locators['content_env.env_link']
            self.click((strategy, value % prior))
        else:
            self.click(locators['content_env.new'])
        if self.wait_until_element(common_locators['name']) is None:
            raise UINoSuchElementError(
                'Could not create new environment {0}'.format(name))
        self.text_field_update(common_locators['name'], name)
        if description:
            self.text_field_update(
                common_locators['description'], description)
        self.click(common_locators['create'])

    def search(self, name):
        """Search for an existing environment. It is necessary to use custom
        search here as we don't have search bar, search button and entities
        list.

        """
        self.navigate_to_entity()
        strategy, value = self._search_locator()
        return self.wait_until_element((strategy, value % name))

    def delete(self, name):
        """Deletes an existing environment. We don't have confirmation dialog
        for current operation, so it is necessary to use custom method
        """
        element = self.search(name)
        if not element:
            raise UINoSuchElementError(
                'Could not find the %s lifecycle environment.' % name)
        element.click()
        self.click(locators['content_env.remove'])

    def update(self, name, new_name=None, description=None):
        """Updates an existing environment."""
        element = self.search(name)
        if not element:
            raise UINoSuchElementError(
                'Could not find the %s lifecycle environment.' % name)
        element.click()
        if new_name:
            self.edit_entity(
                locators['content_env.edit_name'],
                locators['content_env.edit_name_text'],
                new_name,
                locators['content_env.edit_name_text.save']
            )
        if description:
            self.edit_entity(
                locators['content_env.edit_description'],
                locators['content_env.edit_description_textarea'],
                description,
                locators['content_env.edit_description_textarea.save']
            )
