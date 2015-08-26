# -*- encoding: utf-8 -*-
"""Implements Lifecycle content environments."""

from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators


class ContentEnvironment(Base):
    """Manipulates content environments from UI."""

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

    def delete(self, name):
        """Deletes an existing environment."""
        strategy, value = locators['content_env.select_name']
        self.click((strategy, value % name))
        self.click(locators['content_env.remove'])

    def update(self, name, new_name=None, description=None):
        """Updates an existing environment."""
        strategy, value = locators['content_env.select_name']
        self.click((strategy, value % name))
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
