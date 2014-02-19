# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Life cycle content environments
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators


class ContentEnvironment(Base):
    """
    Manipulates content environments from UI
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def create(self, name, description=None, prior=None):
        """
        Creates new life cycle environment
        """
        if prior == 'Library' or 'None':
            self.wait_until_element(locators["content_env.new"]).click()
            self.wait_until_element(locators
                                    ["content_env.create_initial"]
                                    ).click()
        else:
            strategy = locators["content_env.env_link"][0]
            value = locators["content_env.env_link"][1]
            element = self.wait_until_element((strategy, value % prior))
            if element:
                element.click()
        if self.wait_until_element(common_locators["name"]):
            self.text_field_update(common_locators["name"], name)
            if description:
                self.text_field_update(common_locators
                                       ["description"], description)
            self.wait_until_element(common_locators["create"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not create new environment '%s'" % name)

    def delete(self, name, really):
        """
        Deletes an existing environment.
        """

        strategy = locators["content_env.select_name"][0]
        value = locators["content_env.select_name"][1]
        element = self.wait_until_element((strategy, value % name))
        if element:
            element.click()
            self.wait_until_element(locators["content_env.remove"]).click()
            if really:
                self.wait_until_element(common_locators
                                        ["confirm_remove"]).click()
        else:
            raise Exception(
                "Could not delete the selected environment '%s'." % name)

    def update(self, name, new_name=None, description=None):
        """
        Updates an existing environment.
        """

        strategy = locators["content_env.select_name"][0]
        value = locators["content_env.select_name"][1]
        element = self.wait_until_element((strategy, value % name))
        if element:
            element.click()
            if new_name:
                self.edit_entity("content_env.edit_name",
                                 "content_env.edit_name_text",
                                 new_name, "content_env.save_name")
            if description:
                self.edit_entity("content_env.edit_description",
                                 "content_env.edit_description_text",
                                 description, "content_env.save_description")
        else:
            raise Exception(
                "Could not update the selected environment '%s'." % name)
