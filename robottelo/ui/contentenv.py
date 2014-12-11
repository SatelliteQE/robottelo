# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""Implements Life cycle content environments."""

from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import locators, common_locators


class ContentEnvironment(Base):
    """Manipulates content environments from UI."""

    def create(self, name, description=None, prior=None):
        """Creates new life cycle environment."""
        if prior:
            strategy, value = locators["content_env.env_link"]
            element = self.wait_until_element((strategy, value % prior))
            if element:
                element.click()
        else:
            self.wait_for_ajax()
            self.find_element(locators["content_env.new"]).click()
        if self.wait_until_element(common_locators["name"]) is None:
            raise UINoSuchElementError(
                'Could not create new environment {0}'.format(name))
        self.text_field_update(common_locators["name"], name)
        if description:
            self.text_field_update(common_locators["description"],
                                   description)
        self.wait_until_element(common_locators["create"]).click()

    def delete(self, name):
        """Deletes an existing environment."""

        strategy = locators["content_env.select_name"][0]
        value = locators["content_env.select_name"][1]
        element = self.wait_until_element((strategy, value % name))
        if element is None:
            raise UINoSuchElementError(
                'Could not find the selected environment {0}'.format(name))
        element.click()
        self.wait_until_element(locators["content_env.remove"]).click()

    def update(self, name, new_name=None, description=None):
        """Updates an existing environment."""

        strategy = locators["content_env.select_name"][0]
        value = locators["content_env.select_name"][1]
        element = self.wait_until_element((strategy, value % name))
        if element is None:
            raise UINoSuchElementError(
                'Could not update the selected environment {0}'.format(name))
        element.click()
        if new_name:
            self.edit_entity(locators["content_env.edit_name"],
                             locators["content_env.edit_name_text"],
                             new_name,
                             locators["content_env.edit_name_text.save"])
        if description:
            self.edit_entity(
                locators["content_env.edit_description"],
                locators["content_env.edit_description_textarea"],
                description,
                locators["content_env.edit_description_textarea.save"]
            )
