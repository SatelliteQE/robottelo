# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Environment UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators


class Environment(Base):
    """
    Provides the CRUD functionality for Environment.
    """

    def __init__(self, browser):
        self.browser = browser

    def create(self, name):
        """
        Creates the environment.
        """
        self.wait_until_element(locators["env.new"]).click()
        if self.wait_until_element(locators["env.name"]):
            self.find_element(locators["env.name"]).send_keys(name)
        self.find_element(common_locators["submit"]).click()

    def delete(self, name, really):
        """
        Deletes the environment.
        """

        self.delete_entity(name, really, locators["env.env_name"],
                           locators['env.delete'],
                           drop_locator=locators["env.dropdown"])
