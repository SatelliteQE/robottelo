# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Life cycle content environments
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators


class ContentEnvironment(Base):
    """
    Manipulates content environments from UI
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def create(self, name, description=None):
        """
        Creates new life cycle environment
        """

        self.wait_until_element(locators["content_env.new"]).click()
        self.wait_until_element(locators["content_env.create_initial"]).click()

        if self.wait_until_element(locators["content_env.name"]):
            self.field_update("content_env.name", name)
            if description:
                if self.wait_until_element(locators
                                           ["content_env.description"]):
                    self.field_update("content_env.description", description)
            self.wait_until_element(locators["content_env.create"]).click()
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
                self.wait_until_element(locators
                                        ["content_env.confirm_remove"]
                                        ).click()
        else:
            raise Exception(
                "Could not delete the selected environment '%s'." % name)
