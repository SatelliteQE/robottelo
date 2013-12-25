#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Environment UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators


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
        self.find_element(locators["submit"]).click()

    def delete(self, name, really):
        """
        Deletes the environment.
        """
        search = self.search(name, locators["env.env_name"])
        if search:
            strategy = locators["env.dropdown"][0]
            value = locators["env.dropdown"][1]
            dropdown = self.wait_until_element((strategy, value % name))
            dropdown.click()
            strategy1 = locators["env.delete"][0]
            value1 = locators["env.delete"][1]
            element = self.wait_until_element((strategy1, value1 % name))
            if element:
                element.click()
                if really:
                    alert = self.browser.switch_to_alert()
                    alert.accept()
                else:
                    alert = self.browser.switch_to_alert()
                    alert.dismiss()
        # TODO: need to raise exception for negative testing
