# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Activation keys UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from selenium.webdriver.support.select import Select
from time import sleep


class ActivationKey(Base):
    """
    Manipulates Activation keys from UI
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def create(self, name, env, description=None, content_view=None):
        """
        Creates new activation key from UI
        """

        self.wait_for_ajax()
        self.wait_until_element(locators["ak.new"]).click()

        if self.wait_until_element(locators["ak.name"]):
            self.field_update("ak.name", name)
            if description:
                if self.wait_until_element(locators
                                           ["ak.description"]):
                    self.field_update("ak.description", description)
            if env:
                strategy = locators["ak.env"][0]
                value = locators["ak.env"][1]
                element = self.wait_until_element((strategy, value % env))
                if element:
                    element.click()
                    sleep(10)
            else:
                raise Exception(
                    "Could not create new activation key '%s', \
                    without env" % name)
            if content_view:
                Select(self.find_element
                       (locators["ak.content_view"]
                        )).select_by_visible_text(content_view)
            else:
                Select(self.find_element
                       (locators["ak.content_view"]
                        )).select_by_value("0")
            self.wait_until_element(locators["ak.create"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not create new activation key '%s'" % name)
