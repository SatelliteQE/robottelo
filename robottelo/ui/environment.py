#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from selenium.webdriver.common.keys import Keys


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
        dropdown = self.wait_until_element((locators["env.dropdown"][0],
                                           locators["env.dropdown"][1] % name))
        dropdown.click()
        element = self.wait_until_element((locators["env.delete"][0],
                                           locators["env.delete"][1] % name))
        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss()

    def search(self, name):
        """
        Searches for the environment.
        """
        searchbox = self.wait_until_element(locators["search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(name)
            searchbox.send_keys(Keys.RETURN)
            env = self.wait_until_element((locators["env.env_name"][0],
                                           locators["env.env_name"][1] \
                                           % name))
            if env:
                env.click()
        return env
